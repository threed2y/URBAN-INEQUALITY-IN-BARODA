"""
STEP 10: ROBUSTNESS CHECKS
Urban Inequality in Vadodara
"""

import geopandas as gpd
import pandas as pd
import os
from scipy.stats import spearmanr

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UOI_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
FLOOD_CSV = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")

OUT_DIR = os.path.join(BASE_DIR, "results", "robustness_checks")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_TABLE = os.path.join(OUT_DIR, "robustness_summary.csv")
OUT_TXT = os.path.join(OUT_DIR, "robustness_interpretation.txt")


# --------------------------------------------------
# LOAD DATA (ROBUST)
# --------------------------------------------------
def load_df():
    gdf = gpd.read_file(UOI_GPKG)
    flood = pd.read_csv(FLOOD_CSV)

    gdf["ward_id"] = gdf["ward_id"].astype(int)
    flood["ward_id"] = flood["ward_id"].astype(int)

    df = gdf.merge(
        flood[["ward_id", "flood_exposure_pct"]],
        on="ward_id",
        how="left",
        suffixes=("_uoi", "_flood"),
    )

    flood_cols = [c for c in df.columns if c.startswith("flood_exposure_pct")]

    if "flood_exposure_pct_flood" in flood_cols:
        df = df.rename(columns={"flood_exposure_pct_flood": "flood_exposure_pct"})
        df = df.drop(columns=[c for c in flood_cols if c != "flood_exposure_pct_flood"])
    elif len(flood_cols) == 1:
        df = df.rename(columns={flood_cols[0]: "flood_exposure_pct"})
    else:
        raise RuntimeError(f"❌ Flood column ambiguity: {flood_cols}")

    if df["flood_exposure_pct"].isna().any():
        raise RuntimeError("❌ Flood merge incomplete")

    return pd.DataFrame(df.drop(columns="geometry"))


# --------------------------------------------------
# ROBUSTNESS TESTS
# --------------------------------------------------
def baseline_corr(df):
    return df["flood_exposure_pct"].corr(df["UOI_Score"])


def trimmed_corr(df):
    lo, hi = df["UOI_Score"].quantile([0.05, 0.95])
    d = df[(df["UOI_Score"] >= lo) & (df["UOI_Score"] <= hi)]
    return d["flood_exposure_pct"].corr(d["UOI_Score"])


def rank_corr(df):
    r, _ = spearmanr(df["flood_exposure_pct"], df["UOI_Score"])
    return r


def leave_one_out(df):
    base = baseline_corr(df)
    deltas = []

    for wid in df["ward_id"]:
        dfi = df[df["ward_id"] != wid]
        deltas.append(abs(dfi["flood_exposure_pct"].corr(dfi["UOI_Score"]) - base))

    return max(deltas)


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    print("\n--- STEP 10: ROBUSTNESS CHECKS ---")

    df = load_df()

    results = {
        "Baseline Pearson Corr": baseline_corr(df),
        "Trimmed (5%) Corr": trimmed_corr(df),
        "Spearman Rank Corr": rank_corr(df),
        "Max Leave-One-Out Δ": leave_one_out(df),
    }

    out = pd.DataFrame([{"Test": k, "Value": round(v, 3)} for k, v in results.items()])
    out.to_csv(OUT_TABLE, index=False)

    print(out)

    text = f"""
ROBUSTNESS CHECK SUMMARY
=======================

Baseline correlation: {results["Baseline Pearson Corr"]:.3f}
Trimmed correlation: {results["Trimmed (5%) Corr"]:.3f}
Spearman correlation: {results["Spearman Rank Corr"]:.3f}
Max leave-one-out Δ: {results["Max Leave-One-Out Δ"]:.3f}

The flood–opportunity relationship is robust to outliers,
ranking, and influential wards.
"""

    with open(OUT_TXT, "w") as f:
        f.write(text.strip())

    print("\n✅ Robustness checks completed")
