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

OUTPUT_DIR = os.path.join(BASE_DIR, "results", "interactive_vibrant_maps")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_UOI = os.path.join(OUTPUT_DIR, "UOI_Vibrant.html")
OUTPUT_FLOOD = os.path.join(OUTPUT_DIR, "Flood_Vulnerability_Vibrant.html")


# --------------------------------------------------
# COMMON TOOLTIP
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
            "Ward ID",
            "Urban Opportunity Index",
            "Flood Risk (%)",
            "Building Density (%)",
            "Hospital Access (min)",
            "School Access (min)",
            "Bus Access (min)",
            "Highway Access (min)",
        ],
        localize=True,
        sticky=True,
        labels=True,
        style="""
            background-color: white;
            border: 1px solid black;
            border-radius: 4px;
            box-shadow: 3px;
        """,
    )


# --------------------------------------------------
# MAP 1: URBAN OPPORTUNITY INDEX
# --------------------------------------------------
def map_uoi():
    print("→ Generating vibrant UOI map...")

    gdf = gpd.read_file(INPUT_GPKG).to_crs("EPSG:4326")
    center = gdf.geometry.unary_union.centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles="CartoDB positron",
    )

    vmin = gdf["UOI_Score"].quantile(0.05)
    vmax = gdf["UOI_Score"].quantile(0.95)

    cmap = cm.LinearColormap(
        colors=["#9e0142", "#f46d43", "#fdae61", "#abdda4", "#3288bd"],
        vmin=vmin,
        vmax=vmax,
        caption="Urban Opportunity Index (Higher = Better)",
    )

    def style(feature):
        return {
            "fillColor": cmap(feature["properties"]["UOI_Score"]),
            "color": "#333333",
            "weight": 0.4,
            "fillOpacity": 0.9,
        }

    folium.GeoJson(
        gdf,
        style_function=style,
        tooltip=rich_tooltip(),
        name="UOI",
    ).add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    m.save(OUTPUT_UOI)
    print(f"   ✓ Saved: {OUTPUT_UOI}")


# --------------------------------------------------
# MAP 2: FLOOD VULNERABILITY
# --------------------------------------------------
def map_flood():
    print("→ Generating vibrant flood vulnerability map...")

    gdf = gpd.read_file(INPUT_GPKG).to_crs("EPSG:4326")
    center = gdf.geometry.unary_union.centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles="CartoDB dark_matter",
    )

    vmax = gdf["flood_exposure_pct"].quantile(0.95)

    cmap = cm.LinearColormap(
        colors=["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
        vmin=0,
        vmax=vmax,
        caption="Flood Vulnerability (% of Ward Area)",
    )

    def style(feature):
        return {
            "fillColor": cmap(feature["properties"]["flood_exposure_pct"]),
            "color": "#ffffff",
            "weight": 0.4,
            "fillOpacity": 0.9,
        }

    folium.GeoJson(
        gdf,
        style_function=style,
        tooltip=rich_tooltip(),
        name="Flood Risk",
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
    print("\n✅ Vibrant interactive maps generated successfully.")
