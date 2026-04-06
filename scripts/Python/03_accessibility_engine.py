import geopandas as gpd
import pandas as pd
import osmnx as ox
import networkx as nx
import os
from shapely.ops import nearest_points

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
RAW_MAP_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km.gpkg")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_travel_times.csv")

PROJECT_CRS = "EPSG:32643"

DRIVE_SPEED_KMPH = 35
WALK_SPEED_KMPH = 4.5
TRAFFIC_FACTOR = 1.3        # congestion multiplier on travel time
HUMAN_ERROR_FACTOR = 1.1    # routing/behavioural correction
TERMINAL_PENALTY_MINS = 2.0

# FIX I-06: Apply TRAFFIC_FACTOR to the effective drive speed so ALL
# drive-time calculations (hospital, highway) are consistently congestion-
# adjusted — not just the hospital terminal penalty.
EFFECTIVE_DRIVE_SPEED_KMPH = DRIVE_SPEED_KMPH / TRAFFIC_FACTOR   # ~26.9 km/h
METERS_PER_MIN_DRIVE = (EFFECTIVE_DRIVE_SPEED_KMPH * 1000) / 60
METERS_PER_MIN_WALK  = (WALK_SPEED_KMPH * 1000) / 60


def calculate_access():
    print("--- STEP 3 (FINAL): ACCESSIBILITY ENGINE ---")

    wards = gpd.read_file(WARDS_FILE).to_crs(PROJECT_CRS)
    pois = gpd.read_file(RAW_MAP_FILE, layer="pois").to_crs(PROJECT_CRS)

    pois = pois[pois["name"].notna()].copy()
    pois["name_clean"] = pois["name"].str.lower()

    # --------------------------------------------------
    # FILTER POIs
    # --------------------------------------------------
    hospitals = pois[pois["amenity"] == "hospital"].copy()
    schools   = pois[pois["amenity"].isin(["school", "college", "university"])].copy()

    # FIX I-11: OSM tags bus stops as highway=bus_stop (not amenity=bus_stop).
    # The old filter found zero nodes and masked failure with a 45-min fallback.
    transport = pois[
        pois["amenity"].isin(["bus_station"]) |
        (pois.get("highway",         pd.Series(dtype=str)) == "bus_stop") |
        (pois.get("public_transport", pd.Series(dtype=str)).isin(["stop_position", "station"]))
    ].copy()

    if transport.empty:
        print("   ⚠️  No bus/transit nodes found in POI layer — transport times will use fallback (45 min).")
    else:
        print(f"   ✅ {len(transport)} bus/transit nodes found.")

    for df in (hospitals, schools, transport):
        df["geometry"] = df.geometry.centroid

    # --------------------------------------------------
    # NETWORK
    # --------------------------------------------------
    boundary = gpd.read_file(RAW_MAP_FILE, layer="boundary").to_crs("EPSG:4326")
    G = ox.graph_from_polygon(boundary.geometry.iloc[0], network_type="drive")
    G = ox.project_graph(G, to_crs=PROJECT_CRS)

    nodes, edges = ox.graph_to_gdfs(G)

    # Highway geometry (for snapping)
    hwy_edges = edges[
        edges["highway"].astype(str).str.contains("motorway|trunk|primary", regex=True)
    ]
    # FIX I-10: unary_union is deprecated in Shapely 2.x — use union_all()
    hwy_geom = hwy_edges.union_all()

    # --------------------------------------------------
    # HELPER FUNCTION
    # --------------------------------------------------
    def network_time(origin_point, targets, speed, penalty=0):
        if targets.empty:
            return 999

        orig_node = ox.nearest_nodes(G, origin_point.x, origin_point.y)
        target_nodes = [
            ox.nearest_nodes(G, p.x, p.y) for p in targets.geometry
        ]

        dists = []
        for tn in target_nodes:
            try:
                d = nx.shortest_path_length(G, orig_node, tn, weight="length")
                dists.append(d)
            except nx.NetworkXNoPath:
                continue

        if not dists:
            return 999

        return round((min(dists) / speed) + penalty, 2)

    # --------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------
    results = []

    for _, ward in wards.iterrows():
        ward_id = ward["ward_id"]
        access_pt = ward.geometry.representative_point()

        # TERMINAL_PENALTY: human_error only — traffic already baked into METERS_PER_MIN_DRIVE
        t_hosp = network_time(
            access_pt,
            hospitals,
            METERS_PER_MIN_DRIVE,
            penalty=TERMINAL_PENALTY_MINS * HUMAN_ERROR_FACTOR,
        )

        t_school = network_time(access_pt, schools, METERS_PER_MIN_WALK)

        t_bus = network_time(access_pt, transport, METERS_PER_MIN_WALK)
        if t_bus == 999:
            t_bus = 45.0

        # Highway access: snap to nearest highway geometry
        try:
            nearest_hwy_pt = nearest_points(access_pt, hwy_geom)[1]
            orig_node = ox.nearest_nodes(G, access_pt.x, access_pt.y)
            hwy_node = ox.nearest_nodes(G, nearest_hwy_pt.x, nearest_hwy_pt.y)
            dist = nx.shortest_path_length(G, orig_node, hwy_node, weight="length")
            t_hwy = round(dist / METERS_PER_MIN_DRIVE, 2)
        except:
            t_hwy = 45.0

        results.append(
            dict(
                ward_id=ward_id,
                hospitals_min=t_hosp,
                schools_min=t_school,
                transport_node_min=t_bus,
                highway_access_min=t_hwy,
            )
        )

        print(f"Ward {ward_id}: Hosp={t_hosp}, School={t_school}, Hwy={t_hwy}")

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Travel-time matrix saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    calculate_access()
