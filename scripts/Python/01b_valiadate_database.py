# File: scripts/python/01b_validate_database.py
# Purpose: Validate the spatial integrity of vadodara_project.gpkg

import geopandas as gpd
import os
import sys

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INTERIM_DIR = os.path.join(BASE_DIR, "data", "interim")
GPKG_PATH = os.path.join(INTERIM_DIR, "vadodara_project.gpkg")

EXPECTED_CRS = "EPSG:32643"

print("\n--- STEP 1B: VALIDATING SPATIAL DATABASE ---\n")

# -------------------------------------------------
# 1. BASIC FILE CHECK
# -------------------------------------------------
if not os.path.exists(GPKG_PATH):
    print("❌ CRITICAL ERROR: GeoPackage not found.")
    sys.exit(1)

print("✅ GeoPackage found.")

# -------------------------------------------------
# 2. LIST ALL LAYERS
# -------------------------------------------------
layers = gpd.io.file.fiona.listlayers(GPKG_PATH)
print(f"📦 Layers detected: {layers}")

if "wards" not in layers:
    print("❌ CRITICAL ERROR: 'wards' layer missing.")
    sys.exit(1)

# -------------------------------------------------
# 3. LOAD & VALIDATE EACH LAYER
# -------------------------------------------------
errors_found = False

for layer in layers:
    print(f"\n🔍 Validating layer: {layer}")
    gdf = gpd.read_file(GPKG_PATH, layer=layer)

    # --- Geometry presence ---
    if gdf.empty:
        print("❌ Layer is empty.")
        errors_found = True
        continue

    if gdf.geometry.is_empty.any():
        print("⚠️ Empty geometries detected.")
        errors_found = True

    # --- Geometry validity ---
    invalid_count = (~gdf.geometry.is_valid).sum()
    if invalid_count > 0:
        print(f"❌ {invalid_count} invalid geometries found.")
        errors_found = True
    else:
        print("✅ All geometries valid.")

    # --- CRS check ---
    if gdf.crs is None:
        print("❌ CRS missing.")
        errors_found = True
    elif gdf.crs.to_string() != EXPECTED_CRS:
        print(f"❌ CRS mismatch: {gdf.crs}")
        errors_found = True
    else:
        print("✅ CRS verified.")

    # --- Duplicate check (points only) ---
    if layer != "wards":
        dupes = gdf.duplicated(subset="geometry").sum()
        if dupes > 0:
            print(f"⚠️ {dupes} duplicate points found.")
        else:
            print("✅ No duplicate points.")

# -------------------------------------------------
# 4. FINAL VERDICT
# -------------------------------------------------
print("\n--- VALIDATION SUMMARY ---")

if errors_found:
    print("❌ VALIDATION FAILED.")
    print("Fix the above issues before continuing analysis.")
    sys.exit(1)
else:
    print("✅ VALIDATION PASSED.")
    print("Spatial database is SAFE for analysis.\n")
