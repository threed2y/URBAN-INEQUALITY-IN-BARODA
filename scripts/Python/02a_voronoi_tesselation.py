import geopandas as gpd
import folium
import numpy as np
from shapely.geometry import Polygon
from scipy.spatial import Voronoi
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WARDS_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km_wards.gpkg")
BOUNDARY_GPKG = os.path.join(BASE_DIR, "data", "interim", "vadodara_9km.gpkg")

OUT_DIR = os.path.join(BASE_DIR, "results", "interactive_maps")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_HTML = os.path.join(OUT_DIR, "Interactive_Voronoi_Wards.html")

PROJECT_CRS = "EPSG:32643"


# --------------------------------------------------
# VORONOI FUNCTION
# --------------------------------------------------
def build_voronoi(points, boundary):
    vor = Voronoi(points)
    regions = []

    for idx, region_index in enumerate(vor.point_region):
        region = vor.regions[region_index]
        if -1 in region or not region:
            regions.append(None)
            continue

        poly = Polygon([vor.vertices[i] for i in region])
        regions.append(poly.intersection(boundary))

    return regions


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def create_interactive_voronoi():
    print("→ Creating interactive Voronoi ward map")

    wards = gpd.read_file(WARDS_GPKG).to_crs(PROJECT_CRS)
    boundary = gpd.read_file(BOUNDARY_GPKG, layer="boundary").to_crs(PROJECT_CRS)

    city_boundary = boundary.geometry.iloc[0]

    # Ward centroids
    wards["centroid"] = wards.geometry.centroid
    points = np.array([[p.x, p.y] for p in wards["centroid"]])

    # Voronoi polygons
    vor_polys = build_voronoi(points, city_boundary)

    vor_gdf = gpd.GeoDataFrame(
        wards[["ward_id"]],
        geometry=vor_polys,
        crs=PROJECT_CRS,
    ).dropna()

    # Convert to WGS84 for web maps
    vor_gdf = vor_gdf.to_crs("EPSG:4326")

    center = vor_gdf.geometry.unary_union.centroid

    # --------------------------------------------------
    # FOLIUM MAP
    # --------------------------------------------------
    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles="CartoDB positron",
    )

    folium.GeoJson(
        vor_gdf,
        name="Voronoi Wards",
        style_function=lambda f: {
            "fillColor": "#c6dbef",
            "color": "#2171b5",
            "weight": 1.2,
            "fillOpacity": 0.6,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id"],
            aliases=["Ward ID"],
            sticky=True,
        ),
    ).add_to(m)

    folium.LayerControl().add_to(m)

    m.save(OUT_HTML)
    print(f"✓ Saved interactive map → {OUT_HTML}")


# --------------------------------------------------
if __name__ == "__main__":
    create_interactive_voronoi()
