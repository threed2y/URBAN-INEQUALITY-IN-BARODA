import geopandas as gpd
import folium
import branca.colormap as cm
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi.gpkg")
OUTPUT_UOI = os.path.join(BASE_DIR, "results", "map_01_opportunity_index.html")
OUTPUT_FLOOD = os.path.join(BASE_DIR, "results", "map_02_flood_vulnerability.html")


def generate_maps():
    print("--- STEP 6: GENERATING PROFESSIONAL MAPS ---")

    if not os.path.exists(INPUT_GPKG):
        print("❌ Error: Run Step 5 first.")
        return

    # Load Data
    gdf = gpd.read_file(INPUT_GPKG)
    if gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    centroid = gdf.geometry.unary_union.centroid

    # ==========================================
    # MAP 1: URBAN OPPORTUNITY INDEX (UOI)
    # Style: Academic Diverging (Red to Blue)
    # ==========================================
    print("-> Rendering Opportunity Map...")
    m1 = folium.Map(
        location=[centroid.y, centroid.x], zoom_start=12, tiles="CartoDB positron"
    )

    # Scale: Red (10) -> Yellow (50) -> Blue (90)
    # This separates "The Haves" (Blue) from "The Have Nots" (Red) clearly.
    cmap_uoi = cm.LinearColormap(
        colors=["#d73027", "#fc8d59", "#fee090", "#e0f3f8", "#91bfdb", "#4575b4"],
        vmin=10,
        vmax=90,
    )
    cmap_uoi.caption = "Urban Opportunity Index (UOI Score)"

    def style_uoi(feature):
        return {
            "fillColor": cmap_uoi(feature["properties"]["UOI_Score"]),
            "color": "#333333",  # Dark grey borders for professionalism
            "weight": 0.5,
            "fillOpacity": 0.8,
        }

    folium.GeoJson(
        gdf,
        name="UOI Scores",
        style_function=style_uoi,
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "UOI_Score", "Score_Mobility", "Score_Health"],
            aliases=["Ward ID:", "Total UOI:", "Mobility Score:", "Health Score:"],
            localize=True,
            sticky=False,
        ),
    ).add_to(m1)

    m1.add_child(cmap_uoi)
    m1.save(OUTPUT_UOI)

    # ==========================================
    # MAP 2: FLOOD VULNERABILITY
    # Style: Sequential (White to Deep Blue)
    # ==========================================
    print("-> Rendering Flood Risk Map...")
    m2 = folium.Map(
        location=[centroid.y, centroid.x], zoom_start=12, tiles="CartoDB dark_matter"
    )

    # Deep Blue Scale for water risk
    cmap_flood = cm.LinearColormap(
        colors=["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
        vmin=0,
        vmax=60,  # Cap at 60% to make the risk stand out
    )
    cmap_flood.caption = "Flood Risk (% Area Submerged)"

    def style_flood(feature):
        risk = feature["properties"]["flood_risk_pct"]
        return {
            "fillColor": cmap_flood(risk),
            "color": "#ffffff"
            if risk > 5
            else "transparent",  # White border only for risky areas
            "weight": 1,
            "fillOpacity": 0.9 if risk > 0 else 0.1,  # High contrast opacity
        }

    folium.GeoJson(
        gdf,
        name="Flood Zones",
        style_function=style_flood,
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "flood_risk_pct", "building_density_pct"],
            aliases=["Ward ID:", "Flood Risk (%):", "Pop. Density (%):"],
        ),
    ).add_to(m2)

    m2.add_child(cmap_flood)
    m2.save(OUTPUT_FLOOD)

    print(
        f"✅ Maps Generated:\n   1. {OUTPUT_UOI} (Access)\n   2. {OUTPUT_FLOOD} (Risk)"
    )


if __name__ == "__main__":
    generate_maps()
