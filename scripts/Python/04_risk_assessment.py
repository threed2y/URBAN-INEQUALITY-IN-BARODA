import geopandas as gpd
import pandas as pd
import os
import warnings
import osmnx as ox

"""
STEP 4: HYDRO-ENVIRONMENTAL EXPOSURE ASSESSMENT

NOTE:
This analysis measures flood EXPOSURE, not flood HAZARD.
Exposure is operationalized using proximity to river systems
and building concentration, without hydrodynamic modeling
(e.g., elevation, discharge, rainfall).
"""

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
RAW_MAP_FILE = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km.gpkg")
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")

PROJECT_CRS = "EPSG:32643"  # UTM Zone 43N (Meters)
FLOOD_BUFFER = 500  # meters from river centerline (exposure zone)

warnings.filterwarnings("ignore")


def calculate_exposure():
    print("--- STEP 4: HYDRO-ENVIRONMENTAL EXPOSURE ASSESSMENT ---")

    if not os.path.exists(WARDS_FILE) or not os.path.exists(RAW_MAP_FILE):
        print("❌ Error: Files missing. Run Step 1 & 2 first.")
        return

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------
    print("-> Loading spatial layers...")
    wards = gpd.read_file(WARDS_FILE).to_crs(PROJECT_CRS)

    try:
        buildings = gpd.read_file(RAW_MAP_FILE, layer="buildings").to_crs(PROJECT_CRS)
    except Exception:
        print("⚠️ Buildings layer missing. Density set to 0.")
        buildings = gpd.GeoDataFrame(geometry=[], crs=PROJECT_CRS)

    # --------------------------------------------------
    # ACQUIRE RIVER DATA
    # --------------------------------------------------
    print("-> Locating river system...")
    water = gpd.GeoDataFrame()

    try:
        water = gpd.read_file(RAW_MAP_FILE, layer="water").to_crs(PROJECT_CRS)
        print("   ✅ River layer found locally.")
    except Exception:
        print("   ⚠️ Local river layer missing.")

    if water.empty:
        print("   🌐 Downloading river data from OSM...")
        try:
            boundary_geom = wards.geometry.union_all().buffer(500)
            boundary_ll = (
                gpd.GeoSeries([boundary_geom], crs=PROJECT_CRS)
                .to_crs("EPSG:4326")
                .iloc[0]
            )

            tags = {"waterway": ["river", "canal", "stream"], "natural": "water"}
            water = ox.features_from_polygon(boundary_ll, tags)

            if not water.empty:
                water = water.to_crs(PROJECT_CRS)
                print(f"   ✅ Downloaded {len(water)} water features.")
        except Exception as e:
            print(f"   ❌ River download failed: {e}")

    # --------------------------------------------------
    # BUILD FLOOD EXPOSURE ZONE
    # --------------------------------------------------
    if not water.empty:
        water = water[
            water.geometry.type.isin(["LineString", "Polygon", "MultiPolygon"])
        ]
        flood_exposure_zone = water.buffer(FLOOD_BUFFER).union_all()
    else:
        print("⚠️ No river data available. Flood exposure set to 0.")
        flood_exposure_zone = None

    # --------------------------------------------------
    # ANALYSIS LOOP
    # --------------------------------------------------
    results = []

    if not buildings.empty:
        bldg_index = buildings.sindex

    print("-> Computing exposure metrics per ward...")

    for _, ward in wards.iterrows():
        ward_id = ward["ward_id"]
        geom = ward.geometry
        ward_area = geom.area

        # -------------------------------
        # Building Density (Exposure Intensity)
        # -------------------------------
        density_pct = 0.0
        if not buildings.empty:
            candidates = buildings.iloc[list(bldg_index.intersection(geom.bounds))]
            matched = candidates[candidates.intersects(geom)]
            built_area = matched.area.sum()
            density_pct = round((built_area / ward_area) * 100, 2)

        # -------------------------------
        # Flood Exposure (River Proximity)
        # -------------------------------
        flood_exposure_pct = 0.0
        if flood_exposure_zone is not None:
            exposed_area = geom.intersection(flood_exposure_zone).area
            flood_exposure_pct = round((exposed_area / ward_area) * 100, 2)

        print(
            f"   Ward {ward_id}: "
            f"Building Density={density_pct}%, "
            f"Flood Exposure={flood_exposure_pct}%"
        )

        results.append(
            {
                "ward_id": ward_id,
                "building_density_pct": density_pct,
                "flood_exposure_pct": flood_exposure_pct,
            }
        )

    # --------------------------------------------------
    # SAVE OUTPUT
    # --------------------------------------------------
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ Exposure metrics saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    calculate_exposure()
