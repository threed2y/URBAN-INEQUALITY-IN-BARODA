import geopandas as gpd
import folium
import branca.colormap as cm
import os

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

OUTPUT_UOI = os.path.join(BASE_DIR, "results", "map_01_opportunity_index.html")
OUTPUT_FLOOD = os.path.join(BASE_DIR, "results", "map_02_flood_vulnerability.html")


def generate_maps():
    print("--- STEP 6 (FINAL): THESIS MAPS ---")

    gdf = gpd.read_file(INPUT_GPKG)
    if gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    centroid = gdf.geometry.union_all().centroid

    # ==================================================
    # MAP 1: URBAN OPPORTUNITY INDEX
    # ==================================================
    m1 = folium.Map(
        location=[centroid.y, centroid.x],
        zoom_start=12,
        tiles="CartoDB positron",
    )

    uoi_min = gdf["UOI_Score"].quantile(0.05)
    uoi_max = gdf["UOI_Score"].quantile(0.95)

    cmap_uoi = cm.LinearColormap(
        colors=["#b2182b", "#ef8a62", "#fddbc7", "#d1e5f0", "#2166ac"],
        vmin=uoi_min,
        vmax=uoi_max,
        caption="Urban Opportunity Index (0–100)",
    )

    def style_uoi(feature):
        return {
            "fillColor": cmap_uoi(feature["properties"]["UOI_Score"]),
            "color": "#666666",
            "weight": 0.3,
            "fillOpacity": 0.85,
        }

    folium.GeoJson(
        gdf,
        style_function=style_uoi,
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "UOI_Score"],
            aliases=["Ward:", "UOI Score:"],
        ),
    ).add_to(m1)

    cmap_uoi.add_to(m1)
    m1.save(OUTPUT_UOI)

    # ==================================================
    # MAP 2: FLOOD VULNERABILITY
    # ==================================================
    if "flood_risk_pct" not in gdf.columns:
        raise KeyError(
            "flood_risk_pct missing in vadodara_final_uoi_balanced.gpkg.\n"
            "Re-run STEP 5 with the updated script."
        )

    m2 = folium.Map(
        location=[centroid.y, centroid.x],
        zoom_start=12,
        tiles="CartoDB dark_matter",
    )

    flood_max = gdf["flood_risk_pct"].quantile(0.95)

    cmap_flood = cm.LinearColormap(
        colors=["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
        vmin=0,
        vmax=flood_max,
        caption="Flood Risk (% of Ward Area)",
    )

    def style_flood(feature):
        return {
            "fillColor": cmap_flood(feature["properties"]["flood_risk_pct"]),
            "color": "#ffffff",
            "weight": 0.3,
            "fillOpacity": 0.9,
        }

    folium.GeoJson(
        gdf,
        style_function=style_flood,
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "flood_risk_pct"],
            aliases=["Ward:", "Flood Risk (%):"],
        ),
    ).add_to(m2)

    cmap_flood.add_to(m2)
    m2.save(OUTPUT_FLOOD)

    print("✅ Thesis-grade maps generated successfully.")


if __name__ == "__main__":
    generate_maps()
