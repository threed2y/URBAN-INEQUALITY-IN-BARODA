import geopandas as gpd
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
OUTPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_named_wards.gpkg")

# --------------------------------------------------
# VERIFIED, HARD-CODED WARD NAMES
# (Based on dominant locality overlap analysis)
# --------------------------------------------------
WARD_NAME_MAP = {
    1: "Gotri",
    2: "Sayajigunj",
    3: "Fatehgunj",
    4: "Karelibaug",
    5: "Alkapuri",
    6: "Akota",
    7: "Atladara",
    8: "Manjalpur",
    9: "Tarsali",
    10: "Makarpura",
    11: "Waghodia Road",
    12: "Harni",
    13: "Sama",
    14: "Chhani",
    15: "Nizampura",
    16: "Ajwa Road",
    17: "Dabhoi Road",
    18: "Vasna",
    19: "Central Vadodara",
}


def name_wards():
    print("--- STEP 15 (FINAL): HARD-CODED WARD NAMING ---")

    gdf = gpd.read_file(WARDS_GPKG)

    # --------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------
    missing = set(gdf["ward_id"]) - set(WARD_NAME_MAP.keys())
    if missing:
        raise ValueError(f"❌ Missing names for ward IDs: {missing}")

    # --------------------------------------------------
    # ASSIGN NAMES
    # --------------------------------------------------
    gdf["ward_name"] = gdf["ward_id"].map(WARD_NAME_MAP)

    # Human-readable label (for maps & tables)
    gdf["ward_label"] = "Ward " + gdf["ward_id"].astype(str) + " – " + gdf["ward_name"]

    # Metadata for thesis transparency
    gdf["name_basis"] = "Dominant locality overlap (OSM-verified)"
    gdf["ward_type"] = "Synthetic analytical unit"

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------
    gdf.to_file(OUTPUT_GPKG, driver="GPKG")
    print(f"✅ Final named wards saved to:\n   {OUTPUT_GPKG}")


if __name__ == "__main__":
    name_wards()
