import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
from scipy.spatial import Voronoi
from shapely.geometry import Polygon
import os
import sys

# --- CONFIGURATION ---
INPUT_FILE = "data/interim/vadodara_project2.gpkg"
if not os.path.exists(INPUT_FILE):
    INPUT_FILE = "data/interim/vadodara_project2.gpkg"

OUTPUT_FILE = "data/interim/vadodara_project.gpkg"
NUM_WARDS = 19
TARGET_CRS = "EPSG:32643"  # UTM Zone 43N (Meters)

# VADODARA CITY CENTER (Mandvi Gate / Sayaji Baug area)
CITY_CENTER_LAT = 22.3072
CITY_CENTER_LON = 73.1812
URBAN_RADIUS_KM = 9  # 9km radius covers the VMC area perfectly (~250 sq km)


def generate_wards():
    print("--- STEP 1c: GENERATING URBAN CORE WARDS ---")

    # 1. Define the Urban Core (The "Cookie Cutter")
    print(f"-> Creating {URBAN_RADIUS_KM}km buffer around City Center...")
    center_point = gpd.GeoSeries(
        [Point(CITY_CENTER_LON, CITY_CENTER_LAT)], crs="EPSG:4326"
    ).to_crs(TARGET_CRS)

    # Create the circle
    urban_boundary = center_point.buffer(URBAN_RADIUS_KM * 1000).iloc[0]
    print(f"   Urban Area: {urban_boundary.area / 1e6:.2f} sq km (Target: ~250)")

    # 2. Generate Points INSIDE the Urban Core
    print(f"-> Generating {NUM_WARDS} synthetic wards inside the Urban Core...")
    points = []
    min_x, min_y, max_x, max_y = urban_boundary.bounds

    attempts = 0
    while len(points) < 800 and attempts < 20000:
        # Random point in the bounding box
        random_point = Point(
            np.random.uniform(min_x, max_x), np.random.uniform(min_y, max_y)
        )
        # Keep it only if it's inside the circle
        if random_point.within(urban_boundary):
            points.append([random_point.x, random_point.y])
        attempts += 1

    # 3. K-Means Clustering (To space them out evenly)
    from sklearn.cluster import KMeans

    kmeans = KMeans(n_clusters=NUM_WARDS, n_init=10, random_state=42)
    kmeans.fit(points)
    centers = kmeans.cluster_centers_

    # 4. Voronoi Tessellation
    def voronoi_finite_polygons_2d(vor, radius=None):
        if vor.points.shape[1] != 2:
            raise ValueError("Requires 2D input")
        new_regions = []
        new_vertices = vor.vertices.tolist()
        center = vor.points.mean(axis=0)
        if radius is None:
            radius = np.ptp(vor.points, axis=0).max() * 2  # Fixed for NumPy 2.0

        all_ridges = {}
        for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
            all_ridges.setdefault(p1, []).append((p2, v1, v2))
            all_ridges.setdefault(p2, []).append((p1, v1, v2))

        for p1, region in enumerate(vor.point_region):
            vertices = vor.regions[region]
            if all(v >= 0 for v in vertices):
                new_regions.append(vertices)
                continue
            ridges = all_ridges[p1]
            new_region = [v for v in vertices if v >= 0]
            for p2, v1, v2 in ridges:
                if v2 < 0:
                    v1, v2 = v2, v1
                if v1 >= 0:
                    continue
                t = vor.points[p2] - vor.points[p1]
                t /= np.linalg.norm(t)
                n = np.array([-t[1], t[0]])
                midpoint = vor.points[[p1, p2]].mean(axis=0)
                direction = np.sign(np.dot(midpoint - center, n)) * n
                far_point = vor.vertices[v2] + direction * radius
                new_region.append(len(new_vertices))
                new_vertices.append(far_point.tolist())
            vs = np.asarray([new_vertices[v] for v in new_region])
            c = vs.mean(axis=0)
            angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
            new_region = np.array(new_region)[np.argsort(angles)]
            new_regions.append(new_region.tolist())
        return new_regions, np.asarray(new_vertices)

    vor = Voronoi(centers)
    regions, vertices = voronoi_finite_polygons_2d(vor)

    # 5. Clip to Urban Boundary
    ward_polys = []
    for region in regions:
        polygon = Polygon(vertices[region])
        intersection = polygon.intersection(urban_boundary)
        if not intersection.is_empty:
            if intersection.geom_type == "MultiPolygon":
                intersection = max(intersection.geoms, key=lambda a: a.area)
            if intersection.geom_type == "Polygon":
                ward_polys.append(intersection)

    # 6. Save
    gdf_wards = gpd.GeoDataFrame(geometry=ward_polys, crs=TARGET_CRS)
    gdf_wards["ward_id"] = range(1, len(gdf_wards) + 1)

    print(f"-> Created {len(gdf_wards)} wards inside Urban Vadodara.")
    gdf_wards.to_file(OUTPUT_FILE, layer="wards", driver="GPKG")
    print(f"✅ SUCCESS: Saved Urban Map to {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_wards()
