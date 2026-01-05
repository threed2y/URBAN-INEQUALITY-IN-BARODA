# File: scripts/python/01_build_database.py
# Purpose: Build the master spatial database and verify ward count.

import pandas as pd
import geopandas as gpd
import os
import sys

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
OUTPUT_GPKG = os.path.join(INTERIM_DIR, "vadodara_project.gpkg")

TARGET_CRS = "EPSG:32643"  # UTM Zone 43N (Gujarat)

print("\n--- STEP 1: BUILDING MASTER SPATIAL DATABASE ---\n")

os.makedirs(INTERIM_DIR, exist_ok=True)

# Remove old GPKG to avoid layer conflicts
if os.path.exists(OUTPUT_GPKG):
    os.remove(OUTPUT_GPKG)
    print("🧹 Old GeoPackage removed.")

layers_to_save = {}

# -------------------------------------------------
# 1. PROCESS WARDS
# -------------------------------------------------
ward_path = os.path.join(RAW_DIR, "wards.geojson")

if not os.path.exists(ward_path):
    print(f"❌ CRITICAL ERROR: wards.geojson not found in {RAW_DIR}")
    sys.exit(1)

print(f"Reading {ward_path}...")
wards = gpd.read_file(ward_path)

ward_count = len(wards)
print(f"📊 Wards Found: {ward_count}")

if ward_count == 19:
    print("✅ SUCCESS: 19-Ward structure confirmed.")
elif ward_count == 12:
    print("⚠️ WARNING: Old 2011 Census ward map detected.")
else:
    print(f"ℹ️ Note: {ward_count} ward polygons found.")

# Geometry cleaning
wards = wards[~wards.geometry.is_empty]
wards["geometry"] = wards.geometry.make_valid()

# CRS standardization
wards = wards.to_crs(TARGET_CRS)

# Area calculation (sq km)
wards["area_sqkm"] = wards.geometry.area / 1_000_000

print(
    f"📐 Area stats — min: {wards.area_sqkm.min():.2f}, "
    f"max: {wards.area_sqkm.max():.2f} sq.km"
)

layers_to_save["wards"] = wards

# -------------------------------------------------
# 2. PROCESS SERVICE POINTS
# -------------------------------------------------
service_files = {
    "hospitals": "hospitals.csv",
    "schools": "schools.csv",
    "transport": "transport.csv"
}

for layer_name, filename in service_files.items():
    file_path = os.path.join(RAW_DIR, filename)

    if not os.path.exists(file_path):
        print(f"⚠️ {filename} not found. Skipping.")
        continue

    print(f"Processing {layer_name}...")

    try:
        df = pd.read_csv(file_path)

        required_cols = {"latitude", "longitude"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Missing columns: {required_cols - set(df.columns)}")

        # Drop bad / missing coordinates
        df = df.dropna(subset=["latitude", "longitude"])

        # Remove duplicate points
        df = df.drop_duplicates(subset=["latitude", "longitude"])

        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs="EPSG:4326"
        )

        gdf = gdf.to_crs(TARGET_CRS)
        layers_to_save[layer_name] = gdf

        print(f"  ➜ {len(gdf)} valid points added.")

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")

# -------------------------------------------------
# 3. SAVE TO GEOPACKAGE
# -------------------------------------------------
print(f"\n💾 Writing layers to {OUTPUT_GPKG}...")

for name, gdf in layers_to_save.items():
    gdf.to_file(OUTPUT_GPKG, layer=name, driver="GPKG")

print("\n✅ DONE! Spatial database ready:")
print("   data/interim/vadodara_project.gpkg\n")
