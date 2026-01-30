import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from libpysal.weights import KNN
from esda.moran import Moran
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UOI_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

OUT_TXT = os.path.join(BASE_DIR, "results", "FINAL_SUMMARY_REPORT.txt")

FLOOD_COL = "flood_exposure_pct"


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def normalize(x):
    return (x - x.min()) / (x.max() - x.min())


def gini(x):
    x = np.sort(np.array(x))
    n = len(x)
    return (np.sum((2 * np.arange(1, n + 1) - n - 1) * x)) / (n * np.sum(x))


def kolm_pollak_ede(x, k):
    x = np.array(x)
    return -(1 / k) * np.log(np.mean(np.exp(-k * x)))


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def generate_final_report():
    gdf = gpd.read_file(UOI_GPKG)

    # --------------------------------------------------
    # HARD COLUMN VALIDATION (NO MERGE)
    # --------------------------------------------------
    REQUIRED_COLS = ["ward_id", "UOI_Score", FLOOD_COL]

    missing = [c for c in REQUIRED_COLS if c not in gdf.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in GPKG: {missing}\n"
            f"Available columns: {list(gdf.columns)}"
        )

    df = pd.DataFrame(gdf.drop(columns="geometry"))

    # --------------------------------------------------
    # BASIC STATS
    # --------------------------------------------------
    n_wards = len(df)
    mean_uoi = df["UOI_Score"].mean()
    median_uoi = df["UOI_Score"].median()
    min_uoi = df["UOI_Score"].min()
    max_uoi = df["UOI_Score"].max()

    # --------------------------------------------------
    # INEQUALITY
    # --------------------------------------------------
    gini_uoi = gini(df["UOI_Score"])
    uoi_norm = normalize(df["UOI_Score"]) + 1e-6

    ede_05 = kolm_pollak_ede(uoi_norm, 0.5)
    ede_10 = kolm_pollak_ede(uoi_norm, 1.0)
    ede_20 = kolm_pollak_ede(uoi_norm, 2.0)

    # --------------------------------------------------
    # FLOOD × OPPORTUNITY
    # --------------------------------------------------
    valid = df[[FLOOD_COL, "UOI_Score"]].dropna()

    pear_r, pear_p = pearsonr(valid[FLOOD_COL], valid["UOI_Score"])
    spear_r, spear_p = spearmanr(valid[FLOOD_COL], valid["UOI_Score"])

    # --------------------------------------------------
    # SPATIAL AUTOCORRELATION
    # --------------------------------------------------
    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"
    moran = Moran(df["UOI_Score"].values, w)

    # --------------------------------------------------
    # WRITE REPORT
    # --------------------------------------------------
    with open(OUT_TXT, "w") as f:
        f.write("URBAN INEQUALITY IN VADODARA – FINAL SUMMARY REPORT\n")
        f.write("=" * 55 + "\n\n")

        f.write("1. STUDY EXTENT\n")
        f.write("-" * 25 + "\n")
        f.write(f"Total wards analysed: {n_wards}\n\n")

        f.write("2. URBAN OPPORTUNITY INDEX (UOI)\n")
        f.write("-" * 25 + "\n")
        f.write(f"Mean UOI:   {mean_uoi:.2f}\n")
        f.write(f"Median UOI: {median_uoi:.2f}\n")
        f.write(f"Minimum:   {min_uoi:.2f}\n")
        f.write(f"Maximum:   {max_uoi:.2f}\n\n")

        f.write("3. INEQUALITY IN OPPORTUNITY\n")
        f.write("-" * 25 + "\n")
        f.write(f"Gini coefficient (UOI): {gini_uoi:.3f}\n")
        f.write("Kolm–Pollak EDE (normalized):\n")
        f.write(f"  κ = 0.5 → EDE = {ede_05:.3f}\n")
        f.write(f"  κ = 1.0 → EDE = {ede_10:.3f}\n")
        f.write(f"  κ = 2.0 → EDE = {ede_20:.3f}\n\n")

        f.write("4. FLOOD EXPOSURE × OPPORTUNITY\n")
        f.write("-" * 25 + "\n")
        f.write(f"Pearson r:  {pear_r:.3f} (p = {pear_p:.4f})\n")
        f.write(f"Spearman ρ: {spear_r:.3f} (p = {spear_p:.4f})\n\n")

        f.write("5. SPATIAL AUTOCORRELATION\n")
        f.write("-" * 25 + "\n")
        f.write(f"Global Moran’s I: {moran.I:.3f}\n")
        f.write(f"P-value (permutation): {moran.p_sim:.4f}\n\n")

        f.write("END OF REPORT\n")

    print(f"✅ Final summary report generated:\n   {OUT_TXT}")


# --------------------------------------------------
if __name__ == "__main__":
    generate_final_report()
