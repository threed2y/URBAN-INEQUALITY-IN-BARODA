import geopandas as gpd
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NAMED_WARDS = os.path.join(BASE_DIR, "data", "processed", "vadodara_named_wards.gpkg")

FILES_TO_UPDATE = {
    "vadodara_final_uoi.gpkg": "vadodara_final_uoi_named.gpkg",
    "vadodara_final_typology.gpkg": "vadodara_final_typology_named.gpkg",
}


def propagate_names():
    print("--- STEP 16: PROPAGATING WARD NAMES ---")

    name_gdf = gpd.read_file(NAMED_WARDS)[["ward_id", "ward_name", "ward_label"]]

    for infile, outfile in FILES_TO_UPDATE.items():
        in_path = os.path.join(BASE_DIR, "data", "processed", infile)
        out_path = os.path.join(BASE_DIR, "data", "processed", outfile)

        if not os.path.exists(in_path):
            print(f"⚠️ Skipping missing file: {infile}")
            continue

        gdf = gpd.read_file(in_path)
        gdf = gdf.merge(name_gdf, on="ward_id", how="left")

        gdf.to_file(out_path, driver="GPKG")
        print(f"✅ Updated: {outfile}")


if __name__ == "__main__":
    propagate_names()
