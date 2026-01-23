import geopandas as gpd
import numpy as np
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
OUTPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_typology.gpkg"
)


# --------------------------------------------------
# CLASSIFICATION FUNCTION (NEUTRAL LABELS)
# --------------------------------------------------
def classify(row, uoi_thr, flood_thr):
    if row["UOI_Score"] < uoi_thr and row["flood_risk_pct"] > flood_thr:
        return "Low Opportunity / High Risk"
    if row["UOI_Score"] > uoi_thr and row["flood_risk_pct"] < flood_thr:
        return "High Opportunity / Low Risk"
    if row["UOI_Score"] > uoi_thr and row["flood_risk_pct"] > flood_thr:
        return "High Opportunity / High Risk"
    return "Low Opportunity / Low Risk"


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def build_typology():
    print("--- STEP 13: WARD TYPOLOGY (UOI–FLOOD) ---")

    gdf = gpd.read_file(INPUT_GPKG)

    # Drop NaNs explicitly
    gdf = gdf.dropna(subset=["UOI_Score", "flood_risk_pct"]).reset_index(drop=True)

    # --------------------------------------------------
    # ROBUST THRESHOLDS
    # --------------------------------------------------
    uoi_thr = gdf["UOI_Score"].median()
    flood_thr = gdf["flood_risk_pct"].median()

    gdf["Ward_Type"] = gdf.apply(classify, axis=1, args=(uoi_thr, flood_thr))

    # --------------------------------------------------
    # METADATA (TRANSPARENCY)
    # --------------------------------------------------
    iqr_uoi = gdf["UOI_Score"].quantile(0.75) - gdf["UOI_Score"].quantile(0.25)
    iqr_flood = gdf["flood_risk_pct"].quantile(0.75) - gdf["flood_risk_pct"].quantile(
        0.25
    )

    gdf.attrs = {
        "UOI_threshold": float(uoi_thr),
        "Flood_threshold": float(flood_thr),
        "UOI_IQR": float(iqr_uoi),
        "Flood_IQR": float(iqr_flood),
        "Method": "Median-based bivariate typology (robust to IQR variation)",
    }

    gdf.to_file(OUTPUT_GPKG, driver="GPKG")

    print(f"✅ Typology dataset saved to:\n   {OUTPUT_GPKG}")


if __name__ == "__main__":
    build_typology()
