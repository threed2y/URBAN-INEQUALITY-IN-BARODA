import geopandas as gpd
import folium
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
OUTPUT = os.path.join(
    BASE_DIR, "results", "interactive_physical_maps", "UOI_3D_Folium.html"
)

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

gdf = gpd.read_file(INPUT_GPKG).to_crs("EPSG:4326")
center = gdf.geometry.unary_union.centroid

m = folium.Map(location=[center.y, center.x], zoom_start=12, tiles="CartoDB positron")

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery",
    name="Satellite",
).add_to(m)


def style(feature):
    uoi = feature["properties"]["UOI_Score"]
    return {
        "fillColor": "#2166ac" if uoi > 60 else "#b2182b",
        "color": "black",
        "weight": 0.4,
        "fillOpacity": min(0.9, 0.3 + uoi / 150),
    }


folium.GeoJson(
    gdf,
    style_function=style,
    tooltip=folium.GeoJsonTooltip(
        fields=["ward_id", "UOI_Score"],
        aliases=["Ward", "UOI"],
        sticky=True,
    ),
).add_to(m)

folium.LayerControl().add_to(m)
m.save(OUTPUT)

print(f"✅ 3D-style UOI map saved:\n{OUTPUT}")
