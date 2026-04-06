import geopandas as gpd
import folium
import branca.colormap as cm
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "results", "interactive_physical_maps")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_UOI = os.path.join(OUTPUT_DIR, "UOI_Physical_Satellite.html")
OUTPUT_FLOOD = os.path.join(OUTPUT_DIR, "Flood_Physical_Satellite.html")


# --------------------------------------------------
# TOOLTIP (ALL FACTORS)
# --------------------------------------------------
def rich_tooltip():
    return folium.GeoJsonTooltip(
        fields=[
            "ward_id",
            "UOI_Score",
            "flood_exposure_pct",
            "building_density_pct",
            "hospitals_min",
            "schools_min",
            "transport_node_min",
            "highway_access_min",
        ],
        aliases=[
            "Ward ID:",
            "Urban Opportunity Index:",
            "Flood Risk (%):",
            "Building Density (%):",
            "Hospital Access (min):",
            "School Access (min):",
            "Bus Access (min):",
            "Highway Access (min):",
        ],
        localize=True,
        sticky=True,
        labels=True,
        style="background-color: white; border: 1px solid black;",
    )


# --------------------------------------------------
# BASEMAPS
# --------------------------------------------------
def add_basemaps(m):
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite (Esri)",
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

    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="OpenStreetMap",
        name="OSM (Reference)",
        overlay=False,
        control=True,
    ).add_to(m)


# --------------------------------------------------
# MAP 1: URBAN OPPORTUNITY INDEX
# --------------------------------------------------
def map_uoi():
    print("→ Creating UOI map (satellite + terrain)…")

    gdf = gpd.read_file(INPUT_GPKG).to_crs("EPSG:4326")
    center = gdf.geometry.union_all().centroid

    uoi_min = gdf["UOI_Score"].quantile(0.05)
    uoi_max = gdf["UOI_Score"].quantile(0.95)

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles=None,
    )

    add_basemaps(m)

    cmap = cm.LinearColormap(
        colors=["#9e0142", "#f46d43", "#fdae61", "#abdda4", "#3288bd"],
        vmin=uoi_min,
        vmax=uoi_max,
        caption="Urban Opportunity Index (Higher = Better)",
    )

    def style_uoi(feature):
        score = feature["properties"]["UOI_Score"]

        # Normalize (low score = worse)
        norm = 1 - ((score - uoi_min) / (uoi_max - uoi_min))
        norm = min(max(norm, 0), 1)

        # Worse areas → more transparent
        opacity = 0.85 - (0.40 * norm)
        opacity = max(opacity, 0.40)

        return {
            "fillColor": cmap(score),
            "color": "#000000",
            "weight": 0.4,
            "fillOpacity": opacity,
        }

    folium.GeoJson(
        gdf,
        name="Urban Opportunity Index",
        style_function=style_uoi,
        tooltip=rich_tooltip(),
    ).add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(OUTPUT_UOI)

    print(f"   ✓ Saved: {OUTPUT_UOI}")


# --------------------------------------------------
# MAP 2: FLOOD VULNERABILITY
# --------------------------------------------------
def map_flood():
    print("→ Creating Flood map (satellite + terrain)…")

    gdf = gpd.read_file(INPUT_GPKG).to_crs("EPSG:4326")
    center = gdf.geometry.union_all().centroid

    flood_max = gdf["flood_exposure_pct"].quantile(0.95)

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles=None,
    )

    add_basemaps(m)

    cmap = cm.LinearColormap(
        colors=["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
        vmin=0,
        vmax=flood_max,
        caption="Flood Vulnerability (% of Ward Area)",
    )

    def style_flood(feature):
        risk = feature["properties"]["flood_exposure_pct"]

        norm = min(risk / flood_max, 1)

        # High flood risk → more transparent
        opacity = 0.85 - (0.45 * norm)
        opacity = max(opacity, 0.35)

        return {
            "fillColor": cmap(risk),
            "color": "#000000",
            "weight": 0.4,
            "fillOpacity": opacity,
        }

    folium.GeoJson(
        gdf,
        name="Flood Vulnerability",
        style_function=style_flood,
        tooltip=rich_tooltip(),
    ).add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(OUTPUT_FLOOD)

    print(f"   ✓ Saved: {OUTPUT_FLOOD}")


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    map_uoi()
    map_flood()
    print("\n✅ Interactive physical + satellite maps ready.")
