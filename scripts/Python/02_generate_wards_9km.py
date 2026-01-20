import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.ops import voronoi_diagram
from sklearn.cluster import KMeans
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km.gpkg")
OUTPUT_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
NUM_WARDS = 19  # 19 wards for 9km radius
PROJECT_CRS = "EPSG:32643"  # Metric System (UTM Zone 43N)


def generate_wards():
    print("--- STEP 2: GENERATING SYNTHETIC WARDS (9KM - FIXED) ---")

    if not os.path.exists(INPUT_GPKG):
        print("❌ Error: Run Step 1 first.")
        return

    # 1. Load Data
    boundary = gpd.read_file(INPUT_GPKG, layer="boundary")
    roads = gpd.read_file(INPUT_GPKG, layer="roads")

    # Force Metric CRS (Meters)
    if boundary.crs.to_string() != PROJECT_CRS:
        boundary = boundary.to_crs(PROJECT_CRS)
    if roads.crs.to_string() != PROJECT_CRS:
        roads = roads.to_crs(PROJECT_CRS)

    # 2. Extract Road Intersections (Density Nodes)
    points = []
    for geom in roads.geometry:
        if geom.geom_type == "LineString":
            points.append(geom.coords[0])
            points.append(geom.coords[-1])

    # Create DataFrame of points
    points_df = pd.DataFrame(points, columns=["x", "y"]).drop_duplicates()

    # 3. K-Means Clustering
    print(f"-> Finding {NUM_WARDS} density centers...")
    kmeans = KMeans(n_clusters=NUM_WARDS, n_init=10, random_state=42)
    kmeans.fit(points_df)

    seeds = gpd.GeoDataFrame(
        geometry=[Point(xy) for xy in kmeans.cluster_centers_], crs=PROJECT_CRS
    )

    # 4. Voronoi Tessellation
    print("-> Creating Voronoi Geometry...")
    # Use union_all() if available (newer pandas), else unary_union
    try:
        combined_seeds = seeds.geometry.union_all()
    except AttributeError:
        combined_seeds = seeds.geometry.union_all()

    envelope = (
        boundary.geometry.union_all().envelope
        if hasattr(boundary.geometry, "union_all")
        else boundary.geometry.unary_union.envelope
    )

    regions = voronoi_diagram(combined_seeds, envelope=envelope)

    # 5. Clip to 9km Circle
    ward_geoms = []
    # The boundary is likely a single Polygon, extract it
    boundary_poly = boundary.geometry[0]

    for geom in regions.geoms:
        # Intersect with the circle
        clipped = geom.intersection(boundary_poly)
        if not clipped.is_empty:
            ward_geoms.append(clipped)

    # 6. Save
    wards = gpd.GeoDataFrame(geometry=ward_geoms, crs=PROJECT_CRS)
    wards["ward_id"] = range(1, len(wards) + 1)

    # Filter tiny slivers (Area is now in Meters!)
    # 10,000 sq meters = 1 Hectare. We remove anything smaller than 0.1 sq km (100,000 sqm)
    initial_count = len(wards)
    wards = wards[wards.area > 100000]

    # Reproject back to Lat/Lon for compatibility with other tools if needed,
    # BUT for analysis, we usually keep it metric. Let's save as Metric (32643).

    wards.to_file(OUTPUT_GPKG, driver="GPKG")
    print(f"✅ Created {len(wards)} Wards (Filtered from {initial_count}).")
    print(f"💾 Saved to {OUTPUT_GPKG}")


if __name__ == "__main__":
    generate_wards()
