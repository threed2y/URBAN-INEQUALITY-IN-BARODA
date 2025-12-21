import geopandas as gpd

# Load the file you created in Step 1
wards = gpd.read_file("vadodara_project_data.gpkg", layer="wards")

print(f"Total Wards Found: {len(wards)}")

# Logical Check
if len(wards) == 19:
    print("✅ correct: Data matches the official VMC 19-ward structure.")
else:
    print(f"⚠️ Warning: Your map has {len(wards)} polygons. Check for duplicates or missing areas.")