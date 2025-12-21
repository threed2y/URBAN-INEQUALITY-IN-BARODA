import geopandas as gpd
import pandas as pd
from libpysal.weights import KNN
from esda.moran import Moran, Moran_Local
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
INPUT_GPKG = "vadodara_project_data.gpkg"
LAYER_NAME = "wards_final_index" 
OUTPUT_LAYER = "wards_lisa_hotspots"

print("--- STARTING ROBUST SPATIAL ANALYSIS (KNN MODE) ---")

# 1. LOAD DATA
try:
    gdf = gpd.read_file(INPUT_GPKG, layer=LAYER_NAME)
    print(f"Loaded {len(gdf)} wards.")
except Exception as e:
    print(f"❌ Error: Could not load layer. {e}")
    exit()

# 2. CREATE WEIGHTS MATRIX (KNN FIX)
# Instead of 'Queen' (touching), we use 'KNN' (Nearest Neighbors).
# k=4 means "Compare me to my 4 closest neighbors."
# This fixes the "Island" crash because every ward always has 4 neighbors.
print("Building Spatial Weights (k=4)...")
w = KNN.from_dataframe(gdf, k=4)
w.transform = 'r' # Row-standardize weights

# 3. GLOBAL MORAN'S I
y = gdf['UOI_Score'].values
moran = Moran(y, w)

print(f"\n=== GLOBAL RESULTS ===")
print(f"Global Moran's I Index: {moran.I:.3f}")
print(f"P-value: {moran.p_sim:.4f}")

if moran.p_sim < 0.1: # Using 0.1 significance for small datasets (N=12) is acceptable
    print("✅ RESULT: Clustering Detected.")
else:
    print("⚠️ RESULT: Not Significant (Random Pattern).")

# 4. LISA ANALYSIS (Local Hotspots)
print("Running LISA Analysis...")
lisa = Moran_Local(y, w)

# 5. CLASSIFY RESULTS
quadrants = []
labels = []

# Statistical significance threshold
# For small datasets, p < 0.1 is sometimes accepted, but standard is 0.05
SIG_LEVEL = 0.05 

sigs = lisa.p_sim < SIG_LEVEL
q = lisa.q

count_significant = 0

for i, is_sig in enumerate(sigs):
    if not is_sig:
        quadrants.append(0)
        labels.append("Not Significant")
    else:
        count_significant += 1
        if q[i] == 1: labels.append("High-High (Opportunity Hub)")
        elif q[i] == 2: labels.append("Low-High (Outlier)")
        elif q[i] == 3: labels.append("Low-Low (Service Desert)")
        elif q[i] == 4: labels.append("High-Low (Outlier)")

print(f"Found {count_significant} significant hotspot/coldspot wards.")

# 6. SAVE RESULTS
gdf['LISA_Cluster'] = q
gdf['LISA_Label'] = labels
gdf['LISA_Pval'] = lisa.p_sim

# Save to GeoPackage
gdf.to_file(INPUT_GPKG, layer=OUTPUT_LAYER, driver="GPKG")

print(f"\n🎉 Analysis Complete. Layer saved as '{OUTPUT_LAYER}'")