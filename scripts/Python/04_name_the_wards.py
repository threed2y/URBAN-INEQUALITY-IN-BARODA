import geopandas as gpd
import pandas as pd
import osmnx as ox
import sys
import warnings

# Suppress future warnings from pandas/geopandas
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
WARDS_FILE = "data/interim/vadodara_project.gpkg"
SCORES_FILE = "data/processed/ward_indicators.csv"
TRAVEL_FILE = "data/processed/ward_travel_times.csv"
OUTPUT_FILE = "output/maps/ward_identities.csv"

# SETTINGS
ox.settings.log_console = False
ox.settings.use_cache = True


def identify_wards():
    print("--- STEP 4: IDENTIFYING NEIGHBORHOODS (Smart Mode) ---")

    # 1. Load and Merge Data
    try:
        wards = gpd.read_file(WARDS_FILE)
        indicators = pd.read_csv(SCORES_FILE)
        travel = pd.read_csv(TRAVEL_FILE)

        # Merge all data
        df = wards.merge(indicators, on="ward_id").merge(travel, on="ward_id")

    except Exception as e:
        print(f"❌ Error loading data: {e}")
        sys.exit(1)

    # 2. Re-Calculate Index (to rank them)
    def normalize(x):
        return (x - x.min()) / (x.max() - x.min())

    df["n_green"] = normalize(df["green_density"])
    df["n_built"] = normalize(df["building_density"])
    df["n_hosp"] = normalize(df["hospitals_min"])
    df["n_school"] = normalize(df["schools_min"])
    df["n_trans"] = normalize(df["transport_min"])

    # Final Score
    df["Urban_Score"] = (
        (df["n_green"] + (1 - df["n_built"])) / 2
        + ((1 - df["n_hosp"]) + (1 - df["n_school"]) + (1 - df["n_trans"])) / 3
    ) / 2

    # 3. Smart Search for Names
    print(f"-> Scanning {len(df)} wards. Using multi-stage search...")

    results = []
    df_latlon = df.to_crs(epsg=4326)

    for idx, row in df_latlon.iterrows():
        ward_id = row["ward_id"]
        score = row["Urban_Score"]
        poly = row["geometry"]

        # Determine Status
        if score > 0.60:
            status = "HIGH (Privileged)"
        elif score < 0.35:
            status = "LOW (Deprived)"
        else:
            status = "MEDIUM"

        print(f"   Ward {ward_id} [{status}]...", end=" ")

        found_name = None

        # --- STRATEGY 1: Look for Neighborhood Names (Best) ---
        try:
            tags = {"place": ["suburb", "neighbourhood", "quarter", "village"]}
            places = ox.features_from_polygon(poly, tags=tags)
            if not places.empty and "name" in places.columns:
                names = places["name"].dropna().unique().tolist()
                if names:
                    found_name = ", ".join(names[:3]) + " (Area)"
        except Exception:
            pass

        # --- STRATEGY 2: Look for Major Amenities (Schools, Hospitals, Temples) ---
        if not found_name:
            try:
                tags = {
                    "amenity": [
                        "university",
                        "college",
                        "hospital",
                        "place_of_worship",
                    ],
                    "leisure": ["park", "stadium"],
                }
                landmarks = ox.features_from_polygon(poly, tags=tags)
                if not landmarks.empty and "name" in landmarks.columns:
                    # Filter out tiny things
                    names = landmarks["name"].dropna().unique().tolist()
                    if names:
                        found_name = names[0] + " (Landmark)"
            except Exception:
                pass

        # --- STRATEGY 3: Look for Major Roads ---
        if not found_name:
            try:
                tags = {"highway": ["primary", "secondary", "trunk"]}
                roads = ox.features_from_polygon(poly, tags=tags)
                if not roads.empty and "name" in roads.columns:
                    names = roads["name"].dropna().unique().tolist()
                    if names:
                        found_name = "Near " + names[0]
            except Exception:
                pass

        # Fallback
        if not found_name:
            found_name = "Unknown Zone"

        print(f"-> Identified: {found_name}")

        results.append(
            {
                "Ward_ID": ward_id,
                "Status": status,
                "Score": round(score, 3),
                "Identified_Area": found_name,
            }
        )

    # 4. Save and Show
    results_df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
    results_df.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 85)
    print(f"{'WARD':<5} | {'SCORE':<6} | {'STATUS':<18} | {'IDENTIFIED AREA'}")
    print("=" * 85)
    for _, row in results_df.iterrows():
        print(
            f"{row['Ward_ID']:<5} | {row['Score']:<6} | {row['Status']:<18} | {row['Identified_Area']}"
        )
    print("=" * 85)
    print(f"✅ Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    identify_wards()
