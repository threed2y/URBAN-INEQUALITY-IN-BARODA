import geopandas as gpd
import folium
import branca.colormap as cm
import os
from libpysal.weights import KNN
from esda.moran import Moran_Local

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "results", "interactive_standalone_advanced")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------
# BASEMAPS
# --------------------------------------------------
def add_basemaps(m):
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Topographic",
        name="Physical / Terrain",
        overlay=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OSM Reference",
        overlay=False,
    ).add_to(m)


# --------------------------------------------------
# TOOLTIP (COMMON)
# --------------------------------------------------
def rich_tooltip():
    return folium.GeoJsonTooltip(
        fields=[
            "ward_id",
            "UOI_Score",
            "flood_risk_pct",
            "building_density_pct",
            "hospitals_min",
            "schools_min",
            "transport_node_min",
            "highway_access_min",
        ],
        aliases=[
            "Ward ID",
            "Urban Opportunity Index",
            "Flood Exposure (%)",
            "Building Density (%)",
            "Hospital Access (min)",
            "School Access (min)",
            "Bus Access (min)",
            "Highway Access (min)",
        ],
        sticky=True,
        labels=True,
    )


# ==================================================
# MAP 1: URBAN OPPORTUNITY INDEX (STANDALONE)
# ==================================================
def map_uoi():
    print("→ Creating standalone UOI map...")
    gdf = gpd.read_file(INPUT_GPKG).to_crs("EPSG:4326")
    center = gdf.geometry.unary_union.centroid

    m = folium.Map(location=[center.y, center.x], zoom_start=12, tiles=None)
    add_basemaps(m)

    vmin = gdf["UOI_Score"].quantile(0.05)
    vmax = gdf["UOI_Score"].quantile(0.95)

    cmap = cm.LinearColormap(
        colors=["#b2182b", "#ef8a62", "#fddbc7", "#d1e5f0", "#2166ac"],
        vmin=vmin,
        vmax=vmax,
        caption="Urban Opportunity Index (Higher = Better)",
    )

    def style(feature):
        return {
            "fillColor": cmap(feature["properties"]["UOI_Score"]),
            "color": "#000000",
            "weight": 0.4,
            "fillOpacity": 0.85,
        }

    folium.GeoJson(
        gdf,
        name="Urban Opportunity Index",
        style_function=style,
        tooltip=rich_tooltip(),
    ).add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    out = os.path.join(OUTPUT_DIR, "UOI_Standalone.html")
    m.save(out)
    print(f"   ✓ Saved {out}")


# ==================================================
# MAP 2: FLOOD EXPOSURE (STANDALONE)
# ==================================================
def map_flood():
    print("→ Creating standalone Flood Exposure map...")
    gdf = gpd.read_file(INPUT_GPKG).to_crs("EPSG:4326")
    center = gdf.geometry.unary_union.centroid

    m = folium.Map(location=[center.y, center.x], zoom_start=12, tiles=None)
    add_basemaps(m)

    vmax = gdf["flood_risk_pct"].quantile(0.95)

    cmap = cm.LinearColormap(
        colors=["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
        vmin=0,
        vmax=vmax,
        caption="Flood Exposure (% of Ward Area)",
    )

    def style(feature):
        risk = feature["properties"]["flood_risk_pct"]
        norm = min(risk / vmax, 1)
        opacity = max(0.35, 0.85 - 0.5 * norm)

        return {
            "fillColor": cmap(risk),
            "color": "#000000",
            "weight": 0.4,
            "fillOpacity": opacity,
        }

    folium.GeoJson(
        gdf,
        name="Flood Exposure",
        style_function=style,
        tooltip=rich_tooltip(),
    ).add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    out = os.path.join(OUTPUT_DIR, "Flood_Standalone.html")
    m.save(out)
    print(f"   ✓ Saved {out}")


# ==================================================
# MAP 3: LISA CLUSTERS (STANDALONE)
# ==================================================
def map_lisa():
    print("→ Creating standalone LISA cluster map...")
    gdf = gpd.read_file(INPUT_GPKG)

    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"

    y = gdf["UOI_Score"].values
    lisa = Moran_Local(y, w)

    gdf["LISA"] = "Not Significant"
    gdf.loc[(lisa.q == 1) & (lisa.p_sim < 0.05), "LISA"] = "High–High"
    gdf.loc[(lisa.q == 2) & (lisa.p_sim < 0.05), "LISA"] = "Low–High"
    gdf.loc[(lisa.q == 3) & (lisa.p_sim < 0.05), "LISA"] = "Low–Low"
    gdf.loc[(lisa.q == 4) & (lisa.p_sim < 0.05), "LISA"] = "High–Low"

    gdf = gdf.to_crs("EPSG:4326")
    center = gdf.geometry.unary_union.centroid

    m = folium.Map(location=[center.y, center.x], zoom_start=12, tiles=None)
    add_basemaps(m)

    colors = {
        "High–High": "#b2182b",
        "Low–Low": "#2166ac",
        "High–Low": "#ef8a62",
        "Low–High": "#67a9cf",
        "Not Significant": "#cccccc",
    }

    def style(feature):
        cat = feature["properties"]["LISA"]
        return {
            "fillColor": colors[cat],
            "color": "#000000",
            "weight": 0.4,
            "fillOpacity": 0.75 if cat != "Not Significant" else 0.3,
        }

    folium.GeoJson(
        gdf,
        name="LISA Clusters (UOI)",
        style_function=style,
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "LISA", "UOI_Score"],
            aliases=["Ward", "Cluster Type", "UOI"],
        ),
    ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; width: 200px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:13px; padding: 10px;">
    <b>LISA Cluster Types</b><br>
    <i style="background:#b2182b;width:12px;height:12px;display:inline-block"></i> High–High<br>
    <i style="background:#2166ac;width:12px;height:12px;display:inline-block"></i> Low–Low<br>
    <i style="background:#ef8a62;width:12px;height:12px;display:inline-block"></i> High–Low<br>
    <i style="background:#67a9cf;width:12px;height:12px;display:inline-block"></i> Low–High<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    folium.LayerControl(collapsed=False).add_to(m)

    out = os.path.join(OUTPUT_DIR, "LISA_Clusters_Standalone.html")
    m.save(out)
    print(f"   ✓ Saved {out}")


# --------------------------------------------------
# RUN ALL
# --------------------------------------------------
if __name__ == "__main__":
    map_uoi()
    map_flood()
    map_lisa()
    print("\n✅ Standalone advanced maps generated.")
