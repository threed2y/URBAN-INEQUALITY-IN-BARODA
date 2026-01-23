import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
import os
import datetime

# --------------------------------------------------
# CONFIGURATION (LOCKED)
# --------------------------------------------------
CITY_CENTER = (22.297314, 73.206192)  # Mandvi Gate (lat, lon)
RADIUS_M = 9000  # 9 km
PROJECT_CRS = "EPSG:32643"  # UTM Zone 43N

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "interim")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "vadodara_9km.gpkg")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Enable caching for reproducibility
ox.settings.use_cache = True
ox.settings.log_console = True


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def mine_data():
    print("--- STEP 1 (FINAL): MINING VADODARA (9 KM RADIUS) ---")

    # --------------------------------------------------
    # 1. Create Analysis Boundary
    # --------------------------------------------------
    center_point = Point(CITY_CENTER[1], CITY_CENTER[0])
    center_gdf = gpd.GeoDataFrame(geometry=[center_point], crs="EPSG:4326").to_crs(
        PROJECT_CRS
    )

    boundary_geom = center_gdf.buffer(RADIUS_M).geometry.iloc[0]
    boundary_gdf = gpd.GeoDataFrame(geometry=[boundary_geom], crs=PROJECT_CRS)

    boundary_poly_ll = boundary_gdf.to_crs("EPSG:4326").geometry.iloc[0]

    print("✅ 9 km boundary created")

    # --------------------------------------------------
    # 2. Download Road Network
    # --------------------------------------------------
    print("🚗 Downloading road network...")
    G = ox.graph_from_polygon(boundary_poly_ll, network_type="drive")
    G = ox.project_graph(G, to_crs=PROJECT_CRS)
    nodes, edges = ox.graph_to_gdfs(G)

    # --------------------------------------------------
    # 3. Download Buildings
    # --------------------------------------------------
    print("🏗️ Downloading buildings...")
    buildings = ox.features_from_polygon(
        boundary_poly_ll, tags={"building": True}
    ).to_crs(PROJECT_CRS)

    # --------------------------------------------------
    # 4. Download POIs (Raw, Broad)
    # --------------------------------------------------
    print("🏥🏫🚌 Downloading POIs...")
    tags_poi = {
        "amenity": [
            "hospital",
            "clinic",
            "school",
            "college",
            "bus_station",
            "university",
        ],
        "public_transport": ["station", "stop_position"],
        "highway": ["bus_stop"],
    }

    pois = ox.features_from_polygon(boundary_poly_ll, tags=tags_poi)
    pois = pois[pois.geometry.notna()].to_crs(PROJECT_CRS)

    # --------------------------------------------------
    # 5. Metadata Layer (VERY IMPORTANT)
    # --------------------------------------------------
    metadata = gpd.GeoDataFrame(
        {
            "city": ["Vadodara"],
            "center_lat": [CITY_CENTER[0]],
            "center_lon": [CITY_CENTER[1]],
            "radius_m": [RADIUS_M],
            "crs": [PROJECT_CRS],
            "extraction_date": [datetime.date.today().isoformat()],
        },
        geometry=[boundary_geom],
        crs=PROJECT_CRS,
    )

    # --------------------------------------------------
    # 6. Save to GeoPackage
    # --------------------------------------------------
    print(f"💾 Saving layers to {OUTPUT_FILE}")

    boundary_gdf.to_file(OUTPUT_FILE, layer="boundary", driver="GPKG")
    edges.to_file(OUTPUT_FILE, layer="roads", driver="GPKG")
    buildings.to_file(OUTPUT_FILE, layer="buildings", driver="GPKG")
    pois.to_file(OUTPUT_FILE, layer="pois", driver="GPKG")
    metadata.to_file(OUTPUT_FILE, layer="metadata", driver="GPKG")

    print("✅ STEP 1 COMPLETE (LOCKED & REPRODUCIBLE)")


if __name__ == "__main__":
    mine_data()
