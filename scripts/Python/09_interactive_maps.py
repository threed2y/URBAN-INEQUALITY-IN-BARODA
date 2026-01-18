import geopandas as gpd
import pandas as pd
import folium
from folium.features import DivIcon
import branca.colormap as cm
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.expanduser("~/Downloads/URBAN-INEQUALITY-IN-BARODA")
DATA_FILE = os.path.join(BASE_DIR, "data/processed/vadodara_final_index.gpkg")
RISK_FILE = os.path.join(BASE_DIR, "results/ward_flood_population_analysis.csv")
NAMES_FILE = os.path.join(BASE_DIR, "results/ward_identities.csv")  # <--- NEW INPUT
OUTPUT_HTML = os.path.join(
    BASE_DIR, "results/maps/vadodara_thesis_dashboard_final.html"
)


def generate_professional_map():
    print("--- GENERATING FINAL THESIS MAP (WITH NAMES) ---")

    # 1. Load Data
    if not os.path.exists(DATA_FILE):
        print("❌ Error: Master Data not found.")
        return
    gdf = gpd.read_file(DATA_FILE)

    # 2. Merge Risks (Flood/Pop)
    if os.path.exists(RISK_FILE):
        risk_df = pd.read_csv(RISK_FILE)
        gdf = gdf.merge(
            risk_df[
                ["ward_id", "Risk_Category", "flood_risk_score", "building_density"]
            ],
            on="ward_id",
            how="left",
        )
        gdf["Risk_Category"] = gdf["Risk_Category"].fillna("Safe")
        gdf["flood_display"] = (gdf["flood_risk_score"] * 100).round(1).astype(
            str
        ) + "%"

    # 3. Merge Names (The Critical Fix)
    if os.path.exists(NAMES_FILE):
        names_df = pd.read_csv(NAMES_FILE)
        # Keep just ID and Name
        gdf = gdf.merge(
            names_df[["Ward_ID", "Identified_Area"]],
            left_on="ward_id",
            right_on="Ward_ID",
            how="left",
        )
        # Clean up text (remove "Near", "(Area)") for the map label to keep it short
        gdf["Short_Name"] = (
            gdf["Identified_Area"]
            .str.split(",")
            .str[0]
            .str.replace("Near ", "")
            .str.replace(r" \(.*\)", "", regex=True)
        )
    else:
        gdf["Identified_Area"] = "Unknown"
        gdf["Short_Name"] = ""

    gdf = gdf.to_crs(epsg=4326)

    # 4. Setup Map
    m = folium.Map(location=[22.3072, 73.1812], zoom_start=12, tiles="CartoDB positron")

    # Color Scale
    colormap = cm.LinearColormap(
        colors=["#d73027", "#fee08b", "#1a9850"],
        vmin=gdf["UOI_Score"].min(),
        vmax=gdf["UOI_Score"].max(),
        caption="Urban Opportunity Index",
    )

    # 5. Add Polygons with Rich Tooltips
    folium.GeoJson(
        gdf,
        name="Ward Analysis",
        style_function=lambda feature: {
            "fillColor": colormap(feature["properties"]["UOI_Score"]),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.6,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "Identified_Area", "UOI_Score", "Risk_Category"],
            aliases=["WARD:", "NEIGHBORHOOD:", "SCORE:", "RISK:"],
            style=(
                "background-color: white; color: #333; font-family: arial; font-size: 14px; padding: 10px;"
            ),
        ),
    ).add_to(m)

    # 6. Add STATIC LABELS (The "No Confusion" Feature)
    for _, row in gdf.iterrows():
        centroid = row["geometry"].centroid

        # We display "Ward X" AND "Alkapuri" right on the map
        label_text = f"Ward {int(row['ward_id'])}<br><span style='font-size:8pt; font-weight:normal'>{row['Short_Name']}</span>"

        folium.map.Marker(
            [centroid.y, centroid.x],
            icon=DivIcon(
                icon_size=(150, 36),
                icon_anchor=(75, 18),  # Center it
                html=f'<div style="font-size: 10pt; font-weight: bold; text-align: center; text-shadow: 1px 1px 0 #fff;">{label_text}</div>',
            ),
        ).add_to(m)

    # Finalize
    colormap.add_to(m)
    folium.LayerControl().add_to(m)
    m.save(OUTPUT_HTML)
    print(f"✅ Final Map Saved: {OUTPUT_HTML}")


if __name__ == "__main__":
    generate_professional_map()
