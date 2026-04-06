import geopandas as gpd
import pandas as pd
import numpy as np
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG  = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg")
OUTPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_typology.gpkg")
# FIX I-14: companion CSV so threshold metadata survives the .to_file() call
OUTPUT_THRESHOLDS = OUTPUT_GPKG.replace(".gpkg", "_thresholds.csv")


# --------------------------------------------------
# CLASSIFICATION FUNCTION (NEUTRAL LABELS)
# --------------------------------------------------
def classify(row, uoi_thr, flood_thr):
    # FIX I-04 residual: column is flood_exposure_pct not flood_risk_pct
    if row["UOI_Score"] < uoi_thr and row["flood_exposure_pct"] > flood_thr:
        return "Low Opportunity / High Risk"
    if row["UOI_Score"] > uoi_thr and row["flood_exposure_pct"] < flood_thr:
        return "High Opportunity / Low Risk"
    if row["UOI_Score"] > uoi_thr and row["flood_exposure_pct"] > flood_thr:
        return "High Opportunity / High Risk"
    return "Low Opportunity / Low Risk"


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def build_typology():
    print("--- STEP 13: WARD TYPOLOGY (UOI–FLOOD) ---")

    gdf = gpd.read_file(INPUT_GPKG)

    # Drop NaNs explicitly
    gdf = gdf.dropna(subset=["UOI_Score", "flood_exposure_pct"]).reset_index(drop=True)

    # --------------------------------------------------
    # ROBUST THRESHOLDS
    # --------------------------------------------------
    uoi_thr   = gdf["UOI_Score"].median()
    flood_thr = gdf["flood_exposure_pct"].median()

    gdf["Ward_Type"] = gdf.apply(classify, axis=1, args=(uoi_thr, flood_thr))

    # --------------------------------------------------
    # METADATA (TRANSPARENCY)
    # FIX I-14: gdf.attrs is silently dropped by GeoPackage driver.
    # Write thresholds to a companion CSV so they are always recoverable.
    # --------------------------------------------------
    iqr_uoi   = gdf["UOI_Score"].quantile(0.75)   - gdf["UOI_Score"].quantile(0.25)
    iqr_flood = gdf["flood_exposure_pct"].quantile(0.75) - gdf["flood_exposure_pct"].quantile(0.25)

    thresholds = pd.DataFrame([{
        "UOI_threshold":   float(uoi_thr),
        "Flood_threshold": float(flood_thr),
        "UOI_IQR":         float(iqr_uoi),
        "Flood_IQR":       float(iqr_flood),
        "Method":          "Median-based bivariate typology (robust to IQR variation)",
    }])
    thresholds.to_csv(OUTPUT_THRESHOLDS, index=False)
    print(f"   Thresholds saved → {OUTPUT_THRESHOLDS}")

    gdf.to_file(OUTPUT_GPKG, driver="GPKG")
    print(f"✅ Typology dataset saved to:\n   {OUTPUT_GPKG}")


if __name__ == "__main__":
    build_typology()
