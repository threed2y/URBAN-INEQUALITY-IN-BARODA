import geopandas as gpd
import pandas as pd
import numpy as np
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
TRAVEL_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_travel_times.csv")
RISK_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")
TRANSIT_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_transit_metrics.csv")

OUTPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)


# --------------------------------------------------
# NORMALIZATION
# --------------------------------------------------
def normalize(series):
    return (
        (series - series.min()) / (series.max() - series.min())
        if series.max() != series.min()
        else series * 0
    )


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def calculate_uoi():
    print("--- STEP 5 (FINAL): URBAN OPPORTUNITY INDEX ---")

    wards = gpd.read_file(WARDS_FILE)
    travel = pd.read_csv(TRAVEL_FILE)
    risk = pd.read_csv(RISK_FILE)
    transit = pd.read_csv(TRANSIT_FILE)

    df = (
        wards.merge(travel, on="ward_id")
        .merge(risk, on="ward_id")
        .merge(transit, on="ward_id", how="left")
    )

    # --------------------------------------------------
    # SUB-SCORES
    # --------------------------------------------------
    df["Score_Health"] = 1 - normalize(df["hospitals_min"])
    df["Score_Edu"] = 1 - normalize(df["schools_min"])

    # Mobility = bus + highway
    bus_score = df["bus_access_score"].fillna(0)
    hwy_score = 1 - normalize(df["highway_access_min"])

    df["Score_Mobility"] = 0.6 * bus_score + 0.4 * hwy_score

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
    # SAVE
    # --------------------------------------------------
    df.to_file(OUTPUT_GPKG, driver="GPKG")

    print(f"✅ Balanced UOI saved → {OUTPUT_GPKG}")
    print("   Transit integrated via bus stop density (supply-side)")


if __name__ == "__main__":
    calculate_uoi()
