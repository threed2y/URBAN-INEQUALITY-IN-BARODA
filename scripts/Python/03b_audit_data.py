import geopandas as gpd
import pandas as pd
import os
import sys

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
ACCESS_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_travel_times.csv")
OUTPUT_AUDIT = os.path.join(BASE_DIR, "data", "processed", "master_data_audit.csv")


def audit_data():
    print("--- STEP 3b: CROSS-CHECKING DATA INTEGRITY (FIXED) ---")

    # 1. Load the Map (Geometry)
    if not os.path.exists(WARDS_FILE):
        print("❌ Error: Wards file not found.")
        return

    wards = gpd.read_file(WARDS_FILE)
    # Calculate Area in Sq KM for context
    if wards.crs.is_geographic:
        wards = wards.to_crs("EPSG:32643")
    wards["area_sqkm"] = round(wards.area / 10**6, 2)

    print(f"-> Loaded {len(wards)} Wards.")

    # 2. Load the Accessibility Data (Travel Times)
    if not os.path.exists(ACCESS_FILE):
        print("❌ Error: Accessibility data not found. Run Step 3 first.")
        return

    access = pd.read_csv(ACCESS_FILE)
    print(f"-> Loaded Accessibility Data for {len(access)} wards.")

    # 3. Merge Them
    master = pd.merge(wards[["ward_id", "area_sqkm"]], access, on="ward_id", how="left")

    # 4. The Health Check
    print("\n" + "=" * 40)
    print("       DATA HEALTH REPORT       ")
    print("=" * 40)

    # Check 1: Missing Values
    missing = master.isnull().sum().sum()
    if missing > 0:
        print(f"⚠️  WARNING: Found {missing} missing values!")
        print(master[master.isnull().any(axis=1)])
    else:
        print("✅ No missing values found.")

    # Check 2: Outliers (Infinite or 0)
    # 999 usually means 'No Path Found'
    cols_to_check = [
        "hospitals_min",
        "schools_min",
        "transport_node_min",
        "highway_access_min",
    ]

    # Filter only columns that actually exist in the CSV
    cols_present = [c for c in cols_to_check if c in master.columns]

    bad_rows = master[
        (master[cols_present] >= 999).any(axis=1)
        | (master[cols_present] <= 0).any(axis=1)
    ]

    if not bad_rows.empty:
        print(
            f"⚠️  WARNING: {len(bad_rows)} wards have invalid travel times (0 or 999+)."
        )
        print(bad_rows[cols_present])
    else:
        print("✅ All travel times look realistic.")

    # Check 3: Basic Stats
    print("\n--- STATISTICS (Minutes) ---")
    print(master[cols_present].describe().round(2))

    # 5. Save for Manual Inspection
    master.to_csv(OUTPUT_AUDIT, index=False)
    print("\n" + "=" * 40)
    print(f"💾 Master Audit File saved to:\n   {OUTPUT_AUDIT}")
    print("   -> Open this in Excel to cross-check manually.")
    print("=" * 40)


if __name__ == "__main__":
    audit_data()


"""
NOTE:
This analysis measures flood EXPOSURE, not flood HAZARD.
It is based on proximity to river systems and built density,
and does not incorporate hydrodynamic or elevation modeling.
"""
