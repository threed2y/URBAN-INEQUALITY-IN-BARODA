import geopandas as gpd
import pandas as pd
import json
import os
from shapely.geometry import Point

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
BUS_JSON = os.path.join(BASE_DIR, "data", "City-bus", "all_stops.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "processed", "ward_transit_metrics.csv")

PROJECT_CRS = "EPSG:32643"


def normalize(s):
    return (s - s.min()) / (s.max() - s.min()) if s.max() != s.min() else s * 0


def extract_stops(data):
    """Flatten nested JSON and extract stop records"""
    records = []

    def walk(obj):
        if isinstance(obj, dict):
            if "LATLAN" in obj:
                records.append(obj)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)

    walk(data)
    return records


def build_transit_metrics():
    print("--- STEP 3b: BUS TRANSIT ACCESSIBILITY ---")

    wards = gpd.read_file(WARDS_GPKG).to_crs(PROJECT_CRS)

    with open(BUS_JSON, "r") as f:
        raw = json.load(f)

    stops_raw = extract_stops(raw)

    if not stops_raw:
        raise ValueError("❌ No stop records with LATLAN found in JSON")

    df = pd.DataFrame(stops_raw)

    # FIX I-01: LATLAN field stores "lat lon" (latitude first).
    # Original code assigned coords[0] to "lon" — fully swapped.
    # All bus stops were plotted in wrong locations, corrupting the ward spatial join.
    coords = df["LATLAN"].str.split(" ", expand=True)
    df["lat"] = coords[0].astype(float)   # first token is latitude
    df["lon"] = coords[1].astype(float)   # second token is longitude

    # Sanity check — Vadodara bounding box: lat 22.2–22.5, lon 72.9–73.4
    lat_ok = df["lat"].between(22.0, 22.6).all()
    lon_ok = df["lon"].between(72.7, 73.6).all()
    if not lat_ok or not lon_ok:
        raise ValueError(
            "❌ Bus stop coordinates fall outside Vadodara bounding box.\n"
            f"   lat range: {df['lat'].min():.4f}–{df['lat'].max():.4f} (expect 22.0–22.6)\n"
            f"   lon range: {df['lon'].min():.4f}–{df['lon'].max():.4f} (expect 72.7–73.6)\n"
            "   Check LATLAN field token order in all_stops.json."
        )

    stops = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])],
        crs="EPSG:4326",
    ).to_crs(PROJECT_CRS)

    joined = gpd.sjoin(stops, wards, predicate="within")

    counts = joined.groupby("ward_id").size()
    wards["bus_stop_count"] = wards["ward_id"].map(counts).fillna(0)

    wards["area_sqkm"] = wards.area / 1e6
    wards["bus_stop_density"] = wards["bus_stop_count"] / wards["area_sqkm"]
    wards["bus_access_score"] = normalize(wards["bus_stop_density"])

    wards[["ward_id", "bus_stop_density", "bus_access_score"]].to_csv(
        OUTPUT_CSV, index=False
    )

    print(f"✅ Transit metrics saved → {OUTPUT_CSV}")


if __name__ == "__main__":
    build_transit_metrics()
