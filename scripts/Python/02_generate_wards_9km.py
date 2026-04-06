import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.ops import voronoi_diagram
from sklearn.cluster import KMeans
import os

# --------------------------------------------------
# CONFIGURATION (LOCKED)
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km.gpkg")
OUTPUT_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")

NUM_WARDS = 19
PROJECT_CRS = "EPSG:32643"
RANDOM_STATE = 42


def generate_wards():
    print("--- STEP 2 (FINAL): GENERATING SYNTHETIC WARDS ---")

    # --------------------------------------------------
    # 1. Load Boundary and Roads
    # --------------------------------------------------
    boundary = gpd.read_file(INPUT_GPKG, layer="boundary").to_crs(PROJECT_CRS)
    roads = gpd.read_file(INPUT_GPKG, layer="roads").to_crs(PROJECT_CRS)

    boundary_poly = boundary.geometry.iloc[0]

    # --------------------------------------------------
    # 2. Extract Road Midpoints (Density Proxy)
    # --------------------------------------------------
    print("-> Extracting road midpoints...")

    midpoints = []
    for geom in roads.geometry:
        if geom.geom_type == "LineString" and geom.length > 50:
            midpoints.append(geom.interpolate(0.5, normalized=True))

    points = gpd.GeoDataFrame(geometry=midpoints, crs=PROJECT_CRS)

    # FIX I-07: Clip midpoints to boundary BEFORE sampling.
    # Without this, off-boundary KMeans seeds generate Voronoi regions
    # that clip to slivers, producing artefact wards.
    points = points[points.geometry.within(boundary_poly)].copy()

    if len(points) < NUM_WARDS * 5:
        raise ValueError(
            f"❌ Too few road midpoints inside boundary ({len(points)}). "
            "Cannot reliably generate seeds. Check boundary / road data."
        )

    # Spatial thinning to reduce noise
    points = points.sample(frac=0.3, random_state=RANDOM_STATE)

    coords = np.array([[p.x, p.y] for p in points.geometry])

    # --------------------------------------------------
    # 3. K-Means Clustering (Seed Generation)
    # --------------------------------------------------
    print(f"-> Computing {NUM_WARDS} urban centers...")
    kmeans = KMeans(n_clusters=NUM_WARDS, n_init=20, random_state=RANDOM_STATE).fit(
        coords
    )

    seeds = gpd.GeoDataFrame(
        geometry=[Point(xy) for xy in kmeans.cluster_centers_], crs=PROJECT_CRS
    )

    # --------------------------------------------------
    # 4. Voronoi Tessellation (Using Boundary as Envelope)
    # --------------------------------------------------
    print("-> Creating Voronoi wards...")
    regions = voronoi_diagram(seeds.geometry.union_all(), envelope=boundary_poly)

    ward_geoms = []
    for geom in regions.geoms:
        clipped = geom.intersection(boundary_poly)
        if not clipped.is_empty:
            ward_geoms.append(clipped)

    wards = gpd.GeoDataFrame(geometry=ward_geoms, crs=PROJECT_CRS)

    # --------------------------------------------------
    # 5. Enforce Ward Count & Clean Geometry
    # --------------------------------------------------
    wards = wards.explode(index_parts=False).reset_index(drop=True)
    wards["area"] = wards.area

    # Keep largest 19 if over-generated
    wards = wards.sort_values("area", ascending=False).head(NUM_WARDS)
    wards = wards.drop(columns="area").reset_index(drop=True)

    wards["ward_id"] = np.arange(1, NUM_WARDS + 1)

    # --------------------------------------------------
    # 6. Metadata (Critical for Thesis)
    # --------------------------------------------------
    wards["generation_method"] = "Road-density-informed Voronoi"
    wards["seed_method"] = "KMeans on road midpoints (boundary-clipped)"
    wards["num_wards"] = NUM_WARDS
    wards["crs"] = PROJECT_CRS

    # --------------------------------------------------
    # 7. Save
    # --------------------------------------------------
    wards.to_file(OUTPUT_GPKG, driver="GPKG")
    print(f"✅ {NUM_WARDS} synthetic wards generated")
    print(f"💾 Saved to {OUTPUT_GPKG}")


if __name__ == "__main__":
    generate_wards()
