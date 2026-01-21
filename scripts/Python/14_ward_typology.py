import geopandas as gpd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi.gpkg")
OUTPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_typology.gpkg"
)


def classify(row, uoi_med, flood_med):
    if row["UOI_Score"] < uoi_med and row["flood_risk_pct"] > flood_med:
        return "Trapped Zone"
    if row["UOI_Score"] > uoi_med and row["flood_risk_pct"] < flood_med:
        return "Elite Zone"
    if row["UOI_Score"] > uoi_med and row["flood_risk_pct"] > flood_med:
        return "Fragile Advantage"
    return "Stable but Underserved"


def build_typology():
    print("--- STEP 13: WARD TYPOLOGY ---")

    gdf = gpd.read_file(INPUT_GPKG)

    uoi_med = gdf["UOI_Score"].median()
    flood_med = gdf["flood_risk_pct"].median()

    gdf["Ward_Type"] = gdf.apply(classify, axis=1, args=(uoi_med, flood_med))

    gdf.to_file(OUTPUT_GPKG, driver="GPKG")
    print(f"✅ Typology map saved: {OUTPUT_GPKG}")


if __name__ == "__main__":
    build_typology()
