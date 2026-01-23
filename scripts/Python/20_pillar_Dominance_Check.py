import geopandas as gpd
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
OUTPUT_CSV = os.path.join(BASE_DIR, "results", "Pillar_Dominance_Check.csv")


# --------------------------------------------------
# SAFE GEOMETRIC MEAN
# --------------------------------------------------
def geom_mean(df, cols):
    eps = 1e-6
    return (df[cols] + eps).prod(axis=1) ** (1 / len(cols))


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def run_check():
    print("--- REFINEMENT 1: PILLAR DOMINANCE CHECK (ROBUST) ---")

    gdf = gpd.read_file(INPUT_GPKG)
    df = pd.DataFrame(gdf.drop(columns="geometry"))

    pillars = ["Score_Health", "Score_Edu", "Score_Mobility"]
    pillars = [p for p in pillars if p in df.columns]

    if len(pillars) < 3:
        raise ValueError("❌ Expected at least 3 pillar scores.")

    # --------------------------------------------------
    # BASELINE UOI (RECONSTRUCTED)
    # --------------------------------------------------
    df["UOI_baseline"] = geom_mean(df, pillars)

    results = []

    for p in pillars:
        remaining = [x for x in pillars if x != p]

        df[f"UOI_without_{p}"] = geom_mean(df, remaining)

        # Level stability
        corr_level = df["UOI_baseline"].corr(df[f"UOI_without_{p}"])

        # Rank stability (more important)
        rank_base = df["UOI_baseline"].rank()
        rank_alt = df[f"UOI_without_{p}"].rank()
        corr_rank, _ = spearmanr(rank_base, rank_alt)

        results.append(
            {
                "Removed_Pillar": p.replace("Score_", ""),
                "Correlation_Level": round(corr_level, 3),
                "Correlation_Rank": round(corr_rank, 3),
            }
        )

    out = pd.DataFrame(results)
    out.to_csv(OUTPUT_CSV, index=False)

    print("\nPILLAR DOMINANCE RESULTS (LEAVE-ONE-OUT)")
    print(out)
    print(f"\n✅ Saved to: {OUTPUT_CSV}")

    # --------------------------------------------------
    # INTERPRETATION CHECK
    # --------------------------------------------------
    if (out["Correlation_Rank"] < 0.9).any():
        print("⚠️  WARNING: One pillar materially affects rankings.")
    else:
        print("✅ UOI is robust: no single pillar dominates.")


if __name__ == "__main__":
    run_check()
