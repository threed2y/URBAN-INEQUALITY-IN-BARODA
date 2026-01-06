import geopandas as gpd
import osmnx as ox
import pandas as pd
import warnings
import os
import sys

# --- CONFIGURATION ---
WARDS_FILE = "data/interim/vadodara_project.gpkg"
OUTPUT_FILE = "data/processed/ward_indicators.csv"

# Settings
ox.settings.log_console = True
ox.settings.use_cache = True
warnings.filterwarnings("ignore")


def calculate_indicators():
    print("--- STEP 1b: FETCHING URBAN INDICATORS (Robust Mode) ---")

    # 1. Load Wards
    if not os.path.exists(WARDS_FILE):
        print(f"❌ Critical Error: Input file '{WARDS_FILE}' not found.")
        sys.exit(1)

    print(f"-> Loading Ward Boundaries from {WARDS_FILE}...")
    wards = gpd.read_file(WARDS_FILE)

    # Reproject to UTM Zone 43N if needed (to get meters)
    if wards.crs.is_geographic:
        wards = wards.to_crs(epsg=32643)

    print(f"-> Raw file contains {len(wards)} rows. Filtering junk...")

    results = []

    # 2. Loop through wards
    for idx, row in wards.iterrows():
        # Get Ward ID
        ward_id = row.get("ward_id", row.get("id", idx))

        # --- CRITICAL FIX: CHECK AREA ---
        polygon_proj = row["geometry"]

        # Skip if geometry is missing or empty
        if polygon_proj is None or polygon_proj.is_empty:
            print(f"   ⚠️ Skipping Row {idx}: Empty Geometry")
            continue

        # Skip if area is effectively zero (e.g., a point or line)
        ward_area = polygon_proj.area
        if ward_area < 1000:  # If smaller than 1000 sq meters, it's a glitch
            print(
                f"   ⚠️ Skipping Row {idx} (ID: {ward_id}): Area too small (Ghost Polygon)"
            )
            continue

        print(f"\n   Processing Valid Ward: {ward_id}...")

        # Convert to Lat/Lon for OSM
        polygon_latlon = (
            gpd.GeoSeries([polygon_proj], crs=wards.crs).to_crs(epsg=4326).iloc[0]
        )

        # A. BUILDING DENSITY
        try:
            buildings = ox.features_from_polygon(
                polygon_latlon, tags={"building": True}
            )
            if not buildings.empty:
                buildings = buildings.to_crs(wards.crs)
                total_built_area = buildings.area.sum()
            else:
                total_built_area = 0
        except Exception:
            total_built_area = 0

        # B. GREEN SPACE
        try:
            green_tags = {
                "leisure": ["park", "garden"],
                "landuse": ["grass", "forest", "recreation_ground"],
            }
            greenery = ox.features_from_polygon(polygon_latlon, tags=green_tags)
            if not greenery.empty:
                greenery = greenery.to_crs(wards.crs)
                total_green_area = greenery.area.sum()
            else:
                total_green_area = 0
        except Exception:
            total_green_area = 0

        # C. NORMALIZE
        built_density = (total_built_area / ward_area) * 100
        green_density = (total_green_area / ward_area) * 100

        print(f"      [Built: {built_density:.1f}%]  [Green: {green_density:.1f}%]")

        results.append(
            {
                "ward_id": ward_id,
                "building_density": built_density,
                "green_density": green_density,
            }
        )

    # 3. Save Results
    if not results:
        print("❌ Error: No valid wards processed.")
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ SUCCESS: Processed {len(df)} valid wards. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    calculate_indicators()
