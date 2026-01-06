import geopandas as gpd
import os
import sys

# --- CONFIGURATION ---
# We look specifically for your digitized file
RAW_FILE = "data/raw/wards_19_digitized.gpkg"
OUTPUT_DIR = "data/interim"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "vadodara_project.gpkg")
TARGET_CRS = "EPSG:32643"  # UTM Zone 43N (Meters)


def build_database():
    print("--- STEP 1: BUILDING SPATIAL DATABASE ---")

    # 1. Check if the raw file exists
    if not os.path.exists(RAW_FILE):
        print(f"❌ Critical Error: Could not find '{RAW_FILE}'")
        print("   -> Make sure you are running this from the Project Root folder!")
        sys.exit(1)

    print(f"-> Loading raw map: {RAW_FILE}")

    # 2. Load the data
    try:
        wards = gpd.read_file(RAW_FILE)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)

    print(f"   Found {len(wards)} wards.")

    # 3. Standardize CRS (Reproject to Meters)
    if wards.crs.to_string() != TARGET_CRS:
        print(f"-> Reprojecting from {wards.crs.to_string()} to {TARGET_CRS}...")
        wards = wards.to_crs(TARGET_CRS)
    else:
        print(f"-> CRS is already correct ({TARGET_CRS}).")

    # 4. Save to Master Database
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"-> Saving to {OUTPUT_FILE}...")
    wards.to_file(OUTPUT_FILE, layer="wards", driver="GPKG")

    print("✅ SUCCESS: Database built successfully.")


if __name__ == "__main__":
    build_database()
