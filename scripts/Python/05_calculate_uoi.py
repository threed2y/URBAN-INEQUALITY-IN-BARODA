import pandas as pd
import geopandas as gpd
import numpy as np
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
TRAVEL_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_travel_times.csv")
RISK_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")
OUTPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi.gpkg")


def calculate_uoi():
    print("--- STEP 5: CALCULATING INTEGRATED OPPORTUNITY INDEX ---")

    # 1. Load Data
    if not os.path.exists(TRAVEL_FILE) or not os.path.exists(RISK_FILE):
        print("❌ Error: Missing input files. Run Steps 3 & 4.")
        return

    print("-> Loading Datasets...")
    df_travel = pd.read_csv(TRAVEL_FILE)
    df_risk = pd.read_csv(RISK_FILE)
    gdf_wards = gpd.read_file(WARDS_FILE)

    # Merge Everything (Integrated Database)
    df = pd.merge(gdf_wards, df_travel, on="ward_id")
    df = pd.merge(df, df_risk, on="ward_id")

    # 2. Normalization Function (0 to 100 Scale)
    def normalize_inverse(series, min_target, max_target):
        # Values lower than min_target get 100. Values higher than max_target get 0.
        clipped = series.clip(lower=min_target, upper=max_target)
        norm = (clipped - min_target) / (max_target - min_target)
        return (1 - norm) * 100

    print("-> Computing Sub-Indices...")

    # A. HEALTH SCORE (Hospital Access)
    # Target: <5 min drive = 100. >45 min drive = 0.
    df["Score_Health"] = normalize_inverse(df["hospitals_min"], 5, 45)

    # B. EDUCATION SCORE (School Access)
    # Target: <5 min walk = 100. >45 min walk = 0.
    df["Score_Edu"] = normalize_inverse(df["schools_min"], 5, 45)

    # C. MOBILITY SCORE (Transport Integrated)
    # Bus: 5-40 min walk. Highway: 5-30 min drive.
    score_bus = normalize_inverse(df["transport_node_min"], 5, 40)
    score_hwy = normalize_inverse(df["highway_access_min"], 5, 30)

    # Weighted: 60% Public Transit (Equity), 40% Highway (Connectivity)
    df["Score_Mobility"] = (score_bus * 0.6) + (score_hwy * 0.4)

    # 3. FINAL UOI (Geometric Mean of 3 Pillars)
    print("-> Calculating Final UOI Score...")

    df["UOI_Score"] = (
        (df["Score_Health"] + 1) * (df["Score_Edu"] + 1) * (df["Score_Mobility"] + 1)
    ) ** (1 / 3)

    # Rounding for clean display
    cols_to_round = [
        "UOI_Score",
        "Score_Health",
        "Score_Edu",
        "Score_Mobility",
        "flood_risk_pct",
    ]
    df[cols_to_round] = df[cols_to_round].round(2)

    # 4. Save
    df.to_file(OUTPUT_GPKG, driver="GPKG")
    print(f"✅ Integrated Database Saved: {OUTPUT_GPKG}")
    print("   (Contains: UOI, Mobility, Health, Education, and Flood Risk)")


if __name__ == "__main__":
    calculate_uoi()
