import pandas as pd
import geopandas as gpd
import os

# --- CONFIGURATION ---
# We use relative paths so this works on any computer
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_GPKG = os.path.join(PROCESSED_DIR, "vadodara_db.gpkg")

# Vadodara Projection (UTM Zone 43N) - Crucial for accurate distance calc
TARGET_CRS = "EPSG:32643"

print("--- STEP 1: BUILDING GEOSPATIAL DATABASE ---")

# 1. SETUP
if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)

# 2. LOAD & CLEAN SERVICES (Point Data)
service_files = {
    "hospitals": "hospitals.csv",
    "schools": "schools.csv",
    "transport": "transport.csv"
}

layers_to_save = {}

for layer_name, filename in service_files.items():
    path = os.path.join(RAW_DIR, filename)
    if os.path.exists(path):
        print(f"Processing {layer_name}...")
        df = pd.read_csv(path)
        
        # Convert to GeoDataFrame (Assuming Input is Lat/Lon WGS84)
        gdf = gpd.GeoDataFrame(
            df, 
            geometry=gpd.points_from_xy(df.longitude, df.latitude),
            crs="EPSG:4326"
        )
        
        # Reproject to Meters (UTM)
        gdf = gdf.to_crs(TARGET_CRS)
        layers_to_save[layer_name] = gdf
    else:
        print(f"⚠️ Warning: {filename} not found in data/raw/")

# 3. LOAD & CLEAN WARDS (Polygon Data)
ward_path = os.path.join(RAW_DIR, "wards.geojson") # Verify your filename here!

if os.path.exists(ward_path):
    print("Processing Ward Boundaries...")
    wards = gpd.read_file(ward_path)
    
    # Standardize CRS
    wards = wards.to_crs(TARGET_CRS)
    
    # Calculate Area (sq km) for density checks later
    wards['area_sqkm'] = wards.geometry.area / 10**6
    
    layers_to_save["wards"] = wards
else:
    print(f"❌ CRITICAL: Ward file not found at {ward_path}")

# 4. SAVE TO GEOPACKAGE
# This creates ONE file containing ALL your layers
print(f"Saving database to {OUTPUT_GPKG}...")
for name, gdf in layers_to_save.items():
    gdf.to_file(OUTPUT_GPKG, layer=name, driver="GPKG")

print("✅ Success! Database ready.")