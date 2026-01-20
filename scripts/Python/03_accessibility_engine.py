import geopandas as gpd
import pandas as pd
import osmnx as ox
import networkx as nx
import os
import sys
from shapely.geometry import Point, LineString

# --- CONFIGURATION (9KM) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
RAW_MAP_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km.gpkg")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_travel_times.csv")

# --- REALISM PARAMETERS ---
PROJECT_CRS = "EPSG:32643"  # UTM Zone 43N (Meters)
DRIVE_SPEED_KMPH = 35
WALK_SPEED_KMPH = 4.5
TRAFFIC_FACTOR = 1.3
HUMAN_ERROR_FACTOR = 1.1
TERMINAL_PENALTY_MINS = 2.0

METERS_PER_MIN_DRIVE = (DRIVE_SPEED_KMPH * 1000) / 60
METERS_PER_MIN_WALK = (WALK_SPEED_KMPH * 1000) / 60


def calculate_access():
    print("--- STEP 3: ACCESSIBILITY ENGINE (STRICT HIGHWAY MODE) ---")

    # 1. Load Data
    if not os.path.exists(WARDS_FILE) or not os.path.exists(RAW_MAP_FILE):
        print("❌ Error: Input files missing. Run Step 1 & 2 first.")
        return

    print("-> Loading Spatial Database...")
    wards = gpd.read_file(WARDS_FILE)
    if wards.crs.to_string() != PROJECT_CRS:
        wards = wards.to_crs(PROJECT_CRS)

    pois = gpd.read_file(RAW_MAP_FILE, layer="pois")
    if pois.crs.to_string() != PROJECT_CRS:
        pois = pois.to_crs(PROJECT_CRS)
    pois["geometry"] = pois.geometry.centroid
    pois["name_clean"] = pois["name"].astype(str).str.lower()

    # ==========================================
    # 2. FILTER INFRASTRUCTURE
    # ==========================================

    # A. HOSPITALS (Govt + Major)
    govt_keywords = [
        "ssg",
        "sir sayajirao",
        "civil",
        "government",
        "govt",
        "gmers",
        "gotri",
        "urban health",
        "uhc",
        "jamnabai",
    ]
    exclude_health = [
        "dental",
        "skin",
        "eye",
        "hair",
        "homeopath",
        "physio",
        "clinic",
        "lab",
        "imaging",
        "x-ray",
    ]

    mask_hosp = pois["amenity"] == "hospital"
    mask_govt = (pois["amenity"] == "clinic") & (
        pois["name_clean"].str.contains("|".join(govt_keywords), na=False)
    )
    mask_not_spec = ~pois["name_clean"].str.contains("|".join(exclude_health), na=False)

    hospitals = pois[(mask_hosp | mask_govt) & mask_not_spec].copy()

    # B. SCHOOLS
    exclude_edu = [
        "tuition",
        "class",
        "music",
        "dance",
        "play",
        "nursery",
        "toy",
        "drawing",
        "art",
        "driving",
    ]
    mask_school = pois["amenity"].isin(["school", "college", "university"])
    mask_formal = ~pois["name_clean"].str.contains("|".join(exclude_edu), na=False)
    schools = pois[mask_school & mask_formal].copy()

    # C. PUBLIC TRANSPORT NODES
    mask_bus = pois["amenity"].isin(["bus_station", "bus_stop", "taxi"])
    transport_nodes = pois[mask_bus].copy()

    # 3. Build Graph
    print("-> Building Network Graph...")
    boundary_gdf = gpd.read_file(RAW_MAP_FILE, layer="boundary")
    boundary_poly = boundary_gdf.to_crs("EPSG:4326").geometry[0]
    G = ox.graph_from_polygon(boundary_poly, network_type="drive")
    G = ox.project_graph(G, to_crs=PROJECT_CRS)

    # 4. STRICT HIGHWAY EXTRACTION
    print("-> Extracting Strict Highway Skeleton...")
    edges = ox.graph_to_gdfs(G, nodes=False)

    # STRICT FILTER: Only Trunk (NH48) and Motorway (Expressway).
    # Removed 'secondary' and 'primary' to stop city roads from counting as highways.
    # We include 'primary' ONLY if the name indicates a highway (optional), but let's stick to types first.

    # Try 1: Very Strict (Trunk/Motorway only)
    mask_hwy = edges["highway"].astype(str).str.contains("motorway|trunk")
    highways = edges[mask_hwy].copy()

    # Fallback: If map is clipped too tight and misses the bypass, add 'primary' back
    if len(highways) < 10:
        print("   ⚠️ Strict filter found too few roads. Adding 'Primary' roads...")
        mask_hwy = edges["highway"].astype(str).str.contains("motorway|trunk|primary")
        highways = edges[mask_hwy].copy()

    print(f"   ✅ Identified {len(highways)} Highway Segments.")
    if "name" in highways.columns:
        sample_names = highways["name"].dropna().unique()[:5]
        print(f"   Examples: {sample_names}")

    results = []

    # 5. CALCULATION LOOP
    for idx, row in wards.iterrows():
        ward_id = row["ward_id"]
        centroid = row["geometry"].centroid
        orig_node = ox.nearest_nodes(G, centroid.x, centroid.y)

        def get_travel_time(targets, speed, mode_walk=False):
            if targets.empty:
                return 999
            targets["dist_temp"] = targets.distance(centroid)
            candidates = targets.nsmallest(5, "dist_temp")
            cand_nodes = ox.nearest_nodes(
                G, candidates.geometry.x, candidates.geometry.y
            )
            dists = []
            for d_node in cand_nodes:
                try:
                    d = nx.shortest_path_length(G, orig_node, d_node, weight="length")
                    dists.append(d)
                except:
                    continue
            if not dists:
                return 999
            raw = min(dists) / speed
            if mode_walk:
                return round(raw * 1.1, 2)
            else:
                return round(
                    (raw * TRAFFIC_FACTOR * HUMAN_ERROR_FACTOR) + TERMINAL_PENALTY_MINS,
                    2,
                )

        t_hosp = get_travel_time(hospitals, METERS_PER_MIN_DRIVE)
        t_school = get_travel_time(schools, METERS_PER_MIN_WALK, mode_walk=True)
        t_bus = get_travel_time(transport_nodes, METERS_PER_MIN_WALK, mode_walk=True)
        if t_bus == 999:
            t_bus = 45.0

        # Highway Logic: Distance to nearest geometry
        dist_hwy = highways.distance(centroid).min()
        # We calculate drive time to reach that point
        t_hwy = round((dist_hwy / METERS_PER_MIN_DRIVE) * 1.5, 2)

        print(
            f"   Ward {ward_id}: Hosp={t_hosp}m, Hwy={t_hwy}m (Dist: {int(dist_hwy)}m)"
        )

        results.append(
            {
                "ward_id": ward_id,
                "hospitals_min": t_hosp,
                "schools_min": t_school,
                "transport_node_min": t_bus,
                "highway_access_min": t_hwy,
            }
        )

    # Save
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Data Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    calculate_access()
