# File: scripts/python/01_build_database.py
# Purpose: Build the master spatial database and verify ward count.

import pandas as pd
import geopandas as gpd
import os
import sys

# --- CONFIGURATION ---
# We use relative paths to make this work on any computer
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
OUTPUT_GPKG = os.path.join(INTERIM_DIR, "vadodara_project.gpkg")

# CRS: UTM Zone 43N (EPSG:32643) - Critical for calculating meters in Gujarat
TARGET_CRS = "EPSG:32643"

print("--- STEP 1: BUILDING SPATIAL DATABASE ---")

# Ensure output directory exists
if not os.path.exists(INTERIM_DIR):
    os.makedirs(INTERIM_DIR)

# 1. PROCESS WARDS (The Foundation)
ward_path = os.path.join(RAW_DIR, "wards.geojson")

layers_to_save = {}

if os.path.exists(ward_path):
    print(f"Reading {ward_path}...")
    wards = gpd.read_file(ward_path)
    
    # --- VERIFICATION CHECK ---
    ward_count = len(wards)
    print(f"📊 Wards Found: {ward_count}")
    
    if ward_count == 19:
        print("✅ SUCCESS: 19-Ward structure confirmed.")
    elif ward_count == 12:
        print("⚠️ WARNING: This appears to be the old 2011 Census map (12 Wards).")
        print("   Proceeding, but be aware your map might be outdated.")
    else:
        print(f"ℹ️ Note: Your map contains {ward_count} polygons.")

    # Standardize CRS (Lat/Lon -> Meters)
    wards = wards.to_crs(TARGET_CRS)
    
    # Calculate Area for density analysis later
    wards['area_sqkm'] = wards.geometry.area / 10**6
    
    layers_to_save["wards"] = wards
else:
    print(f"❌ CRITICAL ERROR: wards.geojson not found in {RAW_DIR}")
    sys.exit(1)

# 2. PROCESS SERVICE POINTS
service_files = {
    "hospitals": "hospitals.csv",
    "schools": "schools.csv",
    "transport": "transport.csv"
}

for layer_name, filename in service_files.items():
    file_path = os.path.join(RAW_DIR, filename)
    
    if os.path.exists(file_path):
        print(f"Processing {layer_name}...")
        try:
            df = pd.read_csv(file_path)
            
            # Convert to GeoDataFrame (Assuming Input is Lat/Lon WGS84)
            gdf = gpd.GeoDataFrame(
                df, 
                geometry=gpd.points_from_xy(df.longitude, df.latitude),
                crs="EPSG:4326"
            )
            
            # Reproject to Meters
            gdf = gdf.to_crs(TARGET_CRS)
            layers_to_save[layer_name] = gdf
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
    else:
        print(f"⚠️ Warning: {filename} not found. Skipping.")

# 3. SAVE TO GEOPACKAGE
print(f"Saving database to {OUTPUT_GPKG}...")

for name, gdf in layers_to_save.items():
    # Save each layer into the single GPKG file
    gdf.to_file(OUTPUT_GPKG, layer=name, driver="GPKG")

print(f"✅ DONE! Database ready at: data/interim/vadodara_project.gpkg")