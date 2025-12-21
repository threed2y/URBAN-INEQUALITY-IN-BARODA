import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

# --- CONFIGURATION ---
# Vadodara uses UTM Zone 43N (EPSG:32643) for accurate meter measurements
Target_CRS = "EPSG:32643" 
OUTPUT_FILE = "vadodara_project_data.gpkg"

def create_gdf_from_csv(csv_path, layer_name):
    """Reads a CSV, converts to GeoDataFrame, and reprojects."""
    if not os.path.exists(csv_path):
        print(f"⚠️ Warning: {csv_path} not found. Skipping.")
        return None
    
    # 1. Read CSV
    df = pd.read_csv(csv_path)
    
    # 2. Convert to GeoDataFrame (assuming WGS84 Lat/Lon input)
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"  # Input is standard Lat/Lon
    )
    
    # 3. Reproject to UTM (Meters)
    gdf = gdf.to_crs(Target_CRS)
    
    print(f"✅ Processed {layer_name}: {len(gdf)} points")
    return gdf

# --- MAIN EXECUTION ---

# 1. Process Service Points
hospitals = create_gdf_from_csv("data/hospitals.csv", "Hospitals")
schools = create_gdf_from_csv("data/schools.csv", "Schools")
transport = create_gdf_from_csv("data/transport.csv", "Transport")

# 2. Process Ward Boundaries (The GeoJSON you have)
print("Processing Ward Boundaries...")
try:
    wards = gpd.read_file("data/wards.geojson")
    
    # Reproject Wards to match the points (CRITICAL STEP)
    wards = wards.to_crs(Target_CRS)
    
    # Optional: Calculate Area for density analysis later
    wards["area_sqkm"] = wards.geometry.area / 10**6
    
    print(f"✅ Wards Loaded: {len(wards)} wards found.")
except Exception as e:
    print(f"❌ Error loading GeoJSON: {e}")
    wards = None

# 3. Save Everything to One GeoPackage
# This creates a single file you can drag-and-drop into QGIS
print(f"Saving to {OUTPUT_FILE}...")

if wards is not None:
    wards.to_file(OUTPUT_FILE, layer="wards", driver="GPKG")

if hospitals is not None:
    hospitals.to_file(OUTPUT_FILE, layer="hospitals", driver="GPKG")

if schools is not None:
    schools.to_file(OUTPUT_FILE, layer="schools", driver="GPKG")

if transport is not None:
    transport.to_file(OUTPUT_FILE, layer="transport", driver="GPKG")

print("🎉 Success! Open 'vadodara_project_data.gpkg' in QGIS to verify.")