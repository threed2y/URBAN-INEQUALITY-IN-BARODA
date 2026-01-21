import pandas as pd
import geopandas as gpd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RANKINGS = os.path.join(BASE_DIR, "results", "ward_rankings.csv")
NAMED_WARDS = os.path.join(BASE_DIR, "data", "processed", "vadodara_named_wards.gpkg")
OUTPUT = os.path.join(BASE_DIR, "results", "ward_rankings_named.csv")


def update_rankings():
    print("--- STEP 17: UPDATING RANKINGS WITH WARD NAMES ---")

    df = pd.read_csv(RANKINGS)
    names = gpd.read_file(NAMED_WARDS)[["ward_id", "ward_name"]]

    df = df.merge(names, on="ward_id", how="left")

    # Reorder columns for readability
    cols = ["ward_id", "ward_name"] + [
        c for c in df.columns if c not in ["ward_id", "ward_name"]
    ]
    df = df[cols]

    df.to_csv(OUTPUT, index=False)
    print(f"✅ Named rankings saved: {OUTPUT}")


if __name__ == "__main__":
    update_rankings()
