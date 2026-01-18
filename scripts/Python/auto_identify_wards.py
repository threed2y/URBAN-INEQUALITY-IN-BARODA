import geopandas as gpd
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import os
from pathlib import Path


def identify_wards():
    print("--- STEP 10: AUTO-IDENTIFYING WARD NAMES ---")

    # 1. Smart Path Detection
    # Get the folder where THIS script is currently sitting
    current_script_dir = Path(__file__).resolve().parent

    # Go up 2 levels to find the Project Root (URBAN-INEQUALITY-IN-BARODA)
    # scripts/python -> scripts -> ROOT
    project_root = current_script_dir.parent.parent

    # Define paths safely
    INPUT_FILE = project_root / "data" / "processed" / "vadodara_final_index.gpkg"
    OUTPUT_FILE = project_root / "results" / "ward_identities.csv"

    print(f"-> Looking for Master File at: {INPUT_FILE}")

    if not INPUT_FILE.exists():
        print(f"❌ Error: File not found!")
        print(
            f"   Make sure 'vadodara_final_index.gpkg' is in the 'data/processed' folder."
        )
        return

    # 2. Load Data
    gdf = gpd.read_file(INPUT_FILE)
    gdf = gdf.to_crs(epsg=4326)  # Lat/Lon for Geocoding

    # 3. Setup Geocoder
    geolocator = Nominatim(user_agent="vadodara_thesis_project_v2")
    geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1.5)

    print(f"-> Identifying {len(gdf)} wards based on center points...")
    print("-> Please wait ~30 seconds (connecting to OpenStreetMap)...")

    results = []

    for idx, row in gdf.iterrows():
        ward_id = row["ward_id"]
        centroid = row["geometry"].centroid
        lat_lon = f"{centroid.y}, {centroid.x}"

        try:
            # Ask OSM: "What address is this?"
            location = geocode(lat_lon, language="en", exactly_one=True)

            if location:
                address = location.raw["address"]
                # Priority: Suburb > Neighborhood > Road > City District
                area_name = (
                    address.get("suburb")
                    or address.get("neighbourhood")
                    or address.get("residential")
                    or address.get("road")
                    or address.get("city_district")
                    or "Unknown Area"
                )

                print(f"   [Ward {ward_id}]: {area_name}")
            else:
                area_name = "Unknown Zone"
                print(f"   [Ward {ward_id}]: No address found.")

        except Exception as e:
            print(f"   [Ward {ward_id}]: Network Error - {e}")
            area_name = "Manual Check"

        results.append(
            {
                "Ward_ID": ward_id,
                "Identified_Area": area_name,
                "Full_Address": location.address if location else "",
            }
        )

        time.sleep(1)  # Be polite to the API

    # 4. Save
    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)
    df_names = pd.DataFrame(results)
    df_names.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 40)
    print(f"✅ SUCCESS: Identities saved to {OUTPUT_FILE}")
    print(
        "-> Now run 'scripts/python/09_interactive_webmap_v2.py' to update the map labels."
    )
    print("=" * 40)


if __name__ == "__main__":
    identify_wards()
