import pandas as pd
import geopandas as gpd
import numpy as np
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
TRAVEL_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_travel_times.csv")
RISK_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")
OUTPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

# --------------------------------------------------
# NORMALIZATION (0–1, INVERSE)
# --------------------------------------------------
def normalize_inverse(series, min_target, max_target):
    clipped = series.clip(lower=min_target, upper=max_target)
    norm = (clipped - min_target) / (max_target - min_target)
    return 1 - norm


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def calculate_uoi():
    print("--- STEP 5 (FINAL): URBAN OPPORTUNITY INDEX ---")

    if not os.path.exists(TRAVEL_FILE) or not os.path.exists(RISK_FILE):
        raise FileNotFoundError("❌ Run Steps 3 & 4 before Step 5.")

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------
    gdf_wards = gpd.read_file(WARDS_FILE)
    df_travel = pd.read_csv(TRAVEL_FILE)
    df_risk = pd.read_csv(RISK_FILE)

    # --------------------------------------------------
    # STANDARDIZE RISK COLUMN NAMES (CRITICAL FIX)
    # --------------------------------------------------
    if "flood_exposure_pct" in df_risk.columns:
        df_risk = df_risk.rename(columns={"flood_exposure_pct": "flood_risk_pct"})

    required_risk_cols = {"flood_risk_pct", "building_density_pct"}
    if not required_risk_cols.issubset(df_risk.columns):
        raise KeyError(
            f"Risk file missing required columns: {required_risk_cols - set(df_risk.columns)}"
        )

    # --------------------------------------------------
    # MERGE ALL DATA
    # --------------------------------------------------
    df = (
        gdf_wards
        .merge(df_travel, on="ward_id", how="inner")
        .merge(df_risk, on="ward_id", how="inner")
    )

    # --------------------------------------------------
    # SUB-SCORES (0–1)
    # --------------------------------------------------
    df["Score_Health"] = normalize_inverse(df["hospitals_min"], 5, 45)
    df["Score_Edu"] = normalize_inverse(df["schools_min"], 5, 45)

    score_bus = normalize_inverse(df["transport_node_min"], 5, 40)
    score_hwy = normalize_inverse(df["highway_access_min"], 5, 30)
    df["Score_Mobility"] = 0.6 * score_bus + 0.4 * score_hwy

    # --------------------------------------------------
    # FINAL UOI (GEOMETRIC MEAN)
    # --------------------------------------------------
    eps = 1e-6
    df["UOI_Score"] = (
        (df["Score_Health"] + eps)
        * (df["Score_Edu"] + eps)
        * (df["Score_Mobility"] + eps)
    ) ** (1 / 3)

    df["UOI_Score"] = (df["UOI_Score"] * 100).round(2)

    # --------------------------------------------------
    # FINAL DATASET (SINGLE SOURCE OF TRUTH)
    # --------------------------------------------------
    keep_cols = [
        "ward_id",
        "UOI_Score",
        "Score_Health",
        "Score_Edu",
        "Score_Mobility",
        "hospitals_min",
        "schools_min",
        "transport_node_min",
        "highway_access_min",
        "flood_risk_pct",
        "building_density_pct",
        "geometry",
    ]

    df = df[keep_cols].dropna().reset_index(drop=True)

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------
    df.to_file(OUTPUT_GPKG, driver="GPKG")

    print(f"✅ Final balanced UOI saved:\n   {OUTPUT_GPKG}")
    print("   Includes flood risk & building density (single source of truth)")


if __name__ == "__main__":
    calculate_uoi()
