import geopandas as gpd
import matplotlib.pyplot as plt
import os
from libpysal.weights import KNN
from esda.moran import Moran, Moran_Local
from splot.esda import lisa_cluster

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_figures_clean")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------
def run_spatial_stats():
    print("--- STEP 8 (FINAL): SPATIAL AUTOCORRELATION (MORAN’S I) ---")

    if not os.path.exists(INPUT_GPKG):
        raise FileNotFoundError("Balanced UOI file not found.")

    # --------------------------------------------------
    # 1. LOAD & CLEAN DATA
    # --------------------------------------------------
    gdf = gpd.read_file(INPUT_GPKG)

    # Critical: remove NaNs explicitly
    gdf = gdf.dropna(subset=["UOI_Score"]).reset_index(drop=True)
    n = len(gdf)

    print(f"-> Wards included in spatial analysis: {n}")

    # --------------------------------------------------
    # 2. SPATIAL WEIGHTS (KNN = 4)
    # --------------------------------------------------
    print("-> Building spatial weights matrix (KNN = 4)...")
    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"  # row-standardized

    # --------------------------------------------------
    # 3. GLOBAL MORAN’S I
    # --------------------------------------------------
    print("-> Computing Global Moran’s I...")
    y = gdf["UOI_Score"].values
    moran = Moran(y, w)

    print(f"\n   Global Moran’s I = {moran.I:.3f}")
    print(f"   p-value          = {moran.p_sim:.4f}")

    # --------------------------------------------------
    # 4. LOCAL MORAN’S I (LISA)
    # --------------------------------------------------
    print("-> Computing Local Indicators of Spatial Association (LISA)...")
    m_local = Moran_Local(y, w)

    fig, ax = plt.subplots(figsize=(10, 8))

    lisa_cluster(
        m_local,
        gdf,
        p=0.05,
        ax=ax,
        legend=True,
        legend_kwds={"loc": "lower left"},
    )

    ax.set_title(
        "Spatial Clustering of Urban Opportunity\n"
        f"(Global Moran’s I = {moran.I:.2f}, n = {n})",
        fontsize=14,
    )

    ax.set_axis_off()

    plt.tight_layout()
    output_png = os.path.join(OUTPUT_DIR, "Figure_18_LISA_Clusters.png")
    plt.savefig(output_png, dpi=300)
    plt.close()

    print(f"✅ LISA cluster map saved to: {output_png}")
    print("   🔴 High–High → Advantaged clusters")
    print("   🔵 Low–Low   → Structurally deprived clusters")


if __name__ == "__main__":
    run_spatial_stats()
