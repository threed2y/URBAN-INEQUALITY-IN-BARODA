import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
import os

# --- CONFIGURATION (9KM) ---
CITY_CENTER = (22.297314, 73.206192)  # Mandvi Gate
RADIUS = 9000  # 9 KM RADIUS (The Thesis Standard)
PROJECT_CRS = "EPSG:32643"  # UTM Zone 43N (Meters)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "interim")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "vadodara_9km.gpkg")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def mine_data():
    print(f"--- STEP 1: MINING VADODARA (9KM RADIUS) ---")

    # 1. Create the 9km Boundary
    center_geom = Point(CITY_CENTER[1], CITY_CENTER[0])
    center_gdf = gpd.GeoDataFrame(geometry=[center_geom], crs="EPSG:4326")
    boundary_geom = center_gdf.to_crs(PROJECT_CRS).buffer(RADIUS).geometry[0]

    # Convert back to Lat/Lon for OSM
    boundary_gdf = gpd.GeoDataFrame(geometry=[boundary_geom], crs=PROJECT_CRS).to_crs(
        "EPSG:4326"
    )
    boundary_poly = boundary_gdf.geometry[0]

    print("✅ 9km Boundary Created.")

    # 2. Download Layers
    print("🚗 Downloading Roads...")
    G = ox.graph_from_polygon(boundary_poly, network_type="drive")
    nodes, edges = ox.graph_to_gdfs(G)

    print("tj Downloading Buildings...")
    buildings = ox.features_from_polygon(boundary_poly, tags={"building": True})

    print("🏥 Downloading POIs (Hospitals, Schools, Transport)...")
    tags_poi = {
        "amenity": ["hospital", "clinic", "school", "college", "bus_station"],
        "leisure": ["park", "garden"],
    }
    pois = ox.features_from_polygon(boundary_poly, tags_poi)

    # 3. Save to GeoPackage
    print(f"💾 Saving to {OUTPUT_FILE}...")
    boundary_gdf.to_file(OUTPUT_FILE, layer="boundary", driver="GPKG")
    edges.to_file(OUTPUT_FILE, layer="roads", driver="GPKG")
    buildings.to_file(OUTPUT_FILE, layer="buildings", driver="GPKG")
    pois.to_file(OUTPUT_FILE, layer="pois", driver="GPKG")

    print("✅ STEP 1 COMPLETE.")


if __name__ == "__main__":
    mine_data()
