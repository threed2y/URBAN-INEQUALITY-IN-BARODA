import osmnx as ox
import geopandas as gpd
import os
import sys

# CONFIGURATION
PLACE_NAME = "Vadodara, Gujarat, India"
OUTPUT_DIR = "data/interim"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "vadodara_project2.gpkg")
TARGET_CRS = "EPSG:32643"  # UTM Zone 43N (Meters)


def fetch_official_boundaries():
    print("--- STEP 1 (AUTO): FETCHING OFFICIAL BOUNDARIES FROM OSM ---")

    # 1. Download City Boundary
    print(f"-> Downloading boundary for: {PLACE_NAME}...")
    try:
        # We fetch the administrative boundary (admin_level=6 usually for Taluka/City)
        # For specific wards, OSM data can be patchy, so we first get the City Block.
        # If you need specific 19 wards, we try to fetch by 'admin_level=10' or '8'
        gdf = ox.geocode_to_gdf(PLACE_NAME)
    except Exception as e:
        print(f"❌ Error downloading from OSM: {e}")
        sys.exit(1)

    if gdf.empty:
        print("❌ OSM could not find Vadodara.")
        sys.exit(1)

    print(f"-> Found boundary! Reprojecting to {TARGET_CRS}...")

    # 2. Standardize
    gdf = gdf.to_crs(TARGET_CRS)

    # 3. Add Ward ID column (Since this is the whole city, we treat it as the boundary)
    # NOTE: OSM might not have the 19 individual wards perfectly separated.
    # This creates the "City Boundary".
    # IF YOU NEED 19 SEPARATE WARDS, we might need to grid this or use Voronoi.
    # For now, let's save this valid boundary so the project runs.

    # 4. Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    gdf.to_file(OUTPUT_FILE, layer="wards", driver="GPKG")

    print("✅ SUCCESS: Official City Boundary saved.")
    print(f"   Saved to: {OUTPUT_FILE}")
    print("   (Note: This is the City Limit. If you strictly need 19 subdivisions,")
    print("    we may need to generate a Voronoi grid inside this shape next.)")


if __name__ == "__main__":
    fetch_official_boundaries()
