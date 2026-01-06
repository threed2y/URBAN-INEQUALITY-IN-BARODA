import geopandas as gpd
import pandas as pd
import osmnx as ox
import networkx as nx
import os
import sys
from shapely.geometry import Point

# --- CONFIGURATION ---
WARDS_FILE = "data/interim/vadodara_project.gpkg"
RAW_DATA_DIR = "data/raw"
OUTPUT_FILE = "data/processed/ward_travel_times.csv"

# Speed Settings
TRAVEL_SPEED_KMPH = 30
M_PER_MIN = (TRAVEL_SPEED_KMPH * 1000) / 60

# Config
ox.settings.log_console = True
ox.settings.use_cache = True


# --- HELPER FUNCTION: Find Lat/Lon columns automatically ---
def get_lat_lon_cols(df):
    cols = [c.lower() for c in df.columns]

    # Possible names for Longitude
    lon_col = next(
        (
            c
            for c in df.columns
            if c.lower() in ["lon", "longitude", "long", "x", "lng"]
        ),
        None,
    )
    # Possible names for Latitude
    lat_col = next(
        (c for c in df.columns if c.lower() in ["lat", "latitude", "y"]), None
    )

    return lon_col, lat_col


def calculate_access():
    print("--- STEP 2: NETWORK ANALYSIS (Travel Times) ---")

    # 1. Load Wards
    if not os.path.exists(WARDS_FILE):
        print(f"❌ Error: Map file '{WARDS_FILE}' not found.")
        sys.exit(1)

    wards = gpd.read_file(WARDS_FILE)
    if wards.crs.is_geographic:
        wards = wards.to_crs(epsg=32643)

    # Calculate Centroids
    wards["centroid"] = wards.geometry.centroid
    print(f"-> Loaded {len(wards)} wards. Calculated centroids.")

    # Convert centroids to Lat/Lon for lookup
    print("-> Preparing coordinate systems...")
    centroids_latlon = wards["centroid"].to_crs(epsg=4326)

    # 2. Download Road Network
    print("-> Downloading Road Network for the city (Drive mode)...")
    try:
        try:
            city_boundary = wards.to_crs(epsg=4326).geometry.union_all()
        except AttributeError:
            city_boundary = wards.to_crs(epsg=4326).geometry.unary_union

        G = ox.graph_from_polygon(city_boundary, network_type="drive")
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
    except Exception as e:
        print(f"❌ Error downloading graph: {e}")
        sys.exit(1)

    print(f"-> Graph ready: {len(G.nodes)} intersections.")

    # 3. Process Services
    services = ["hospitals", "schools", "transport"]
    results = []

    for idx, row in wards.iterrows():
        ward_id = row["ward_id"]
        ward_center_latlon = centroids_latlon.loc[idx]

        # Find start node
        orig_node = ox.nearest_nodes(G, ward_center_latlon.x, ward_center_latlon.y)

        ward_stats = {"ward_id": ward_id}
        print(f"   Calculating paths for Ward {ward_id}...", end="\r")

        for service in services:
            csv_path = os.path.join(RAW_DATA_DIR, f"{service}.csv")

            if not os.path.exists(csv_path):
                if idx == 0:
                    print(f"\n⚠️ Warning: {service}.csv missing. Skipping.")
                ward_stats[f"{service}_min"] = 999
                continue

            # Load CSV
            df_locs = pd.read_csv(csv_path)

            # --- SMART COLUMN DETECTION ---
            lon_col, lat_col = get_lat_lon_cols(df_locs)

            if not lon_col or not lat_col:
                if idx == 0:
                    print(
                        f"\n❌ Error: Could not find Lat/Lon columns in {service}.csv"
                    )
                    print(f"   Found columns: {list(df_locs.columns)}")
                ward_stats[f"{service}_min"] = 999
                continue
            # ------------------------------

            # Create geometry
            gdf_locs = gpd.GeoDataFrame(
                df_locs,
                geometry=gpd.points_from_xy(df_locs[lon_col], df_locs[lat_col]),
                crs="EPSG:4326",
            )

            # Find nearest network nodes
            dest_nodes = ox.nearest_nodes(G, gdf_locs.geometry.x, gdf_locs.geometry.y)

            # Calculate shortest path
            dists = []
            for dest_node in dest_nodes:
                try:
                    length = nx.shortest_path_length(
                        G, orig_node, dest_node, weight="length"
                    )
                    dists.append(length / M_PER_MIN)
                except nx.NetworkXNoPath:
                    continue

            ward_stats[f"{service}_min"] = round(min(dists), 2) if dists else 999

        results.append(ward_stats)

    print("\n-> Calculations complete.")

    # 4. Save
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ SUCCESS: Travel times saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    calculate_access()
