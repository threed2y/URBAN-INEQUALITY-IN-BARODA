import geopandas as gpd
import pandas as pd
import numpy as np
import os
import warnings
import osmnx as ox

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
RAW_MAP_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km.gpkg")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")

PROJECT_CRS = "EPSG:32643"  # UTM Zone 43N (Meters)
FLOOD_BUFFER = 500  # Meters from river center
warnings.filterwarnings("ignore")


def calculate_risks():
    print("--- STEP 4: RISK ASSESSMENT (FIXED RIVER DOWNLOAD) ---")

    if not os.path.exists(WARDS_FILE) or not os.path.exists(RAW_MAP_FILE):
        print("❌ Error: Files missing. Run Step 1 & 2 first.")
        return

    # 1. Load Data
    print("-> Loading Spatial Layers...")
    wards = gpd.read_file(WARDS_FILE).to_crs(PROJECT_CRS)

    # Load Buildings (for Density)
    try:
        buildings = gpd.read_file(RAW_MAP_FILE, layer="buildings").to_crs(PROJECT_CRS)
    except:
        print("⚠️ No buildings layer found. Density will be 0.")
        buildings = gpd.GeoDataFrame(geometry=[])

    # 2. ACQUIRE RIVER DATA (Self-Healing Fix)
    print("-> Locating River System...")
    water = gpd.GeoDataFrame()

    # Attempt 1: Check Local File
    try:
        water = gpd.read_file(RAW_MAP_FILE, layer="water").to_crs(PROJECT_CRS)
        print("   ✅ Found river in local database.")
    except Exception:
        print("   ⚠️ River layer missing in local file.")

    # Attempt 2: Live Download (Fallback)
    if water.empty:
        print("   🌐 Downloading Vishwamitri River data from OSM...")
        try:
            # FIX: Convert the shapely polygon to a GeoSeries before reprojecting
            unified_geom = wards.geometry.union_all().buffer(500)
            boundary_gs = gpd.GeoSeries([unified_geom], crs=PROJECT_CRS).to_crs(
                "EPSG:4326"
            )
            boundary_poly = boundary_gs[0]

            tags = {"waterway": ["river", "canal", "stream"], "natural": "water"}
            water = ox.features_from_polygon(boundary_poly, tags)

            if not water.empty:
                water = water.to_crs(PROJECT_CRS)
                print(f"   ✅ Downloaded {len(water)} river segments.")
            else:
                print("   ⚠️ No river data returned from OSM.")
        except Exception as e:
            print(f"   ❌ Could not download river: {e}")

    # 3. PREPARE LAYERS
    print("-> Preparing Flood Zone...")

    if not water.empty:
        # Filter for actual water bodies (LineString/Polygon)
        water = water[
            water.geometry.type.isin(["LineString", "Polygon", "MultiPolygon"])
        ]
        # Create the "Danger Zone"
        flood_zone = water.buffer(FLOOD_BUFFER).union_all()
    else:
        print("⚠️ Warning: No river data available. Flood Risk will be 0%.")
        flood_zone = None

    results = []

    # 4. ANALYSIS LOOP
    print("-> Calculating Metrics per Ward...")

    # Pre-calculate spatial index for buildings
    if not buildings.empty:
        sindex = buildings.sindex

    for idx, row in wards.iterrows():
        ward_id = row["ward_id"]
        geom = row["geometry"]
        ward_area = geom.area  # Sq Meters

        # --- METRIC 1: BUILDING DENSITY (Crowding) ---
        density_ratio = 0.0
        if not buildings.empty:
            possible_matches_index = list(sindex.intersection(geom.bounds))
            possible_matches = buildings.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(geom)]

            total_built_area = precise_matches.area.sum()
            # Density % (0-100)
            density_ratio = round((total_built_area / ward_area) * 100, 2)

        # --- METRIC 2: FLOOD RISK ---
        flood_pct = 0.0
        if flood_zone is not None:
            # Intersection of Ward AND Flood Zone
            flooded_area = geom.intersection(flood_zone).area
            # Percentage of Ward Underwater
            flood_pct = round((flooded_area / ward_area) * 100, 2)

        print(f"   Ward {ward_id}: Density={density_ratio}%, Flood Risk={flood_pct}%")

        results.append(
            {
                "ward_id": ward_id,
                "building_density_pct": density_ratio,
                "flood_risk_pct": flood_pct,
            }
        )

    # 5. SAVE
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Risk Metrics Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    calculate_risks()
