import geopandas as gpd
import folium
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WARD_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

OUT_DIR = os.path.join(BASE_DIR, "results", "final_maps_clean")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_HTML = os.path.join(OUT_DIR, "Interactive_Synthetic_Wards_Physical_Satellite.html")


# --------------------------------------------------
# MAP
# --------------------------------------------------
def build_map():
    gdf = gpd.read_file(WARD_GPKG).to_crs("EPSG:4326")
    center = gdf.geometry.union_all().centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles=None,  # start blank
    )

    # ----------------------------
    # BASEMAPS
    # ----------------------------
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Topographic",
        name="Physical / Terrain",
        overlay=False,
        control=True,
    ).add_to(m)

    # ----------------------------
    # SYNTHETIC WARDS LAYER
    # ----------------------------
    folium.GeoJson(
        gdf,
        name="Synthetic Wards (Voronoi)",
        style_function=lambda f: {
            "fillColor": "#c6dbef",
            "color": "#08519c",
            "weight": 1.0,
            "fillOpacity": 0.40,  # VERY IMPORTANT for satellite visibility
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id"], aliases=["Ward ID"], sticky=True
        ),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(OUT_HTML)
    print(f"✅ Saved → {OUT_HTML}")


# --------------------------------------------------
if __name__ == "__main__":
    build_map()
