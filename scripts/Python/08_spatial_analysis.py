import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import os
from libpysal.weights import Queen, KNN
from esda.moran import Moran, Moran_Local
from splot.esda import lisa_cluster

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi.gpkg")
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "figures")
OUTPUT_LISA_MAP = os.path.join(BASE_DIR, "results", "map_03_lisa_clusters.html")


def run_spatial_stats():
    print("--- STEP 8: SPATIAL STATISTICS (MORAN'S I) ---")

    if not os.path.exists(INPUT_GPKG):
        print("❌ Error: Run Step 5 first.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Data
    gdf = gpd.read_file(INPUT_GPKG)

    # 2. Define Spatial Weights (Who is a neighbor of whom?)
    # We use KNN (K-Nearest Neighbors) to ensure every ward has neighbors,
    # preventing "island" errors if geometry is messy.
    print("-> Building Spatial Weights Matrix (KNN=4)...")
    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"  # Row-standardize

    # 3. Global Moran's I (The Segregation Score)
    print("-> Calculating Global Moran's I...")
    y = gdf["UOI_Score"].values
    moran = Moran(y, w)

    print(f"\n   🌎 Global Moran's I: {moran.I:.3f}")
    print(f"   📊 P-Value: {moran.p_sim:.4f}")

    if moran.I > 0 and moran.p_sim < 0.05:
        print("   ✅ STATISTICALLY SIGNIFICANT CLUSTERING DETECTED.")
        print("      (Proof that inequality is spatially segregated, not random.)")
    else:
        print("   ⚠️ No significant clustering found.")

    # 4. Local Moran's I (LISA) - Identifying Hotspots
    print("\n-> Calculating Local Indicators of Spatial Association (LISA)...")
    m_local = Moran_Local(y, w)

    # Plotting the Cluster Map
    fig, ax = plt.subplots(figsize=(12, 10))
    lisa_cluster(m_local, gdf, p=0.05, ax=ax)
    plt.title(
        f"LISA Cluster Map: Inequality Hotspots (Moran's I={moran.I:.2f})", fontsize=16
    )

    output_png = os.path.join(OUTPUT_DIR, "04_lisa_cluster_map.png")
    plt.savefig(output_png, dpi=300)
    plt.close()

    print(f"✅ Cluster Map saved to: {output_png}")
    print("   🔴 High-High (Red) = Wealthy Clusters")
    print("   🔵 Low-Low (Blue)  = Deprived Clusters (Structural Poverty)")


if __name__ == "__main__":
    run_spatial_stats()
