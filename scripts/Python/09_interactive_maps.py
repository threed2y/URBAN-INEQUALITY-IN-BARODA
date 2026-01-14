import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import branca.colormap as cm
import os

# --- CONFIGURATION ---
# Use absolute paths to be safe
BASE_DIR = os.path.expanduser("~/Downloads/URBAN-INEQUALITY-IN-BARODA")
DATA_FILE = os.path.join(BASE_DIR, "data/processed/vadodara_final_index.gpkg")
RISK_FILE = os.path.join(BASE_DIR, "results/ward_flood_population_analysis.csv")
OUTPUT_HTML = os.path.join(BASE_DIR, "results/maps/interactive_dashboard.html")


def generate_interactive_map():
    print("--- STEP 9: GENERATING INTERACTIVE WEB MAP ---")

    # 1. Load Data
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: Master GPKG not found at {DATA_FILE}")
        return

    gdf = gpd.read_file(DATA_FILE)

    # Merge with Flood Risk Data
    if os.path.exists(RISK_FILE):
        print("-> Merging Flood Risk Data...")
        risk_df = pd.read_csv(RISK_FILE)
        gdf = gdf.merge(
            risk_df[
                ["ward_id", "Risk_Category", "flood_risk_score", "building_density"]
            ],
            on="ward_id",
            how="left",
        )
        gdf["Risk_Category"] = gdf["Risk_Category"].fillna("Safe")
    else:
        print("⚠️ Warning: Risk CSV not found. Map will lack flood data.")

    # Reproject to Lat/Lon for Web Map
    gdf = gdf.to_crs(epsg=4326)

    # 2. Setup Map Center (Vadodara)
    m = folium.Map(
        location=[22.3072, 73.1812], zoom_start=12, tiles="CartoDB dark_matter"
    )

    # 3. Color Scale (UOI Score)
    uoi_colormap = cm.LinearColormap(
        colors=["#440154", "#21908d", "#fde725"],
        vmin=gdf["UOI_Score"].min(),
        vmax=gdf["UOI_Score"].max(),
        caption="Urban Opportunity Index",
    )

    # 4. Add Polygons (The Wards)
    folium.GeoJson(
        gdf,
        name="Opportunity Index",
        style_function=lambda feature: {
            "fillColor": uoi_colormap(feature["properties"]["UOI_Score"]),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "UOI_Score", "flood_risk_score"],
            aliases=["Ward ID:", "Opportunity Score:", "Flood Risk (%):"],
            localize=True,
        ),
    ).add_to(m)

    # 5. Add "Danger" Markers
    # Highlight wards with > 25% Flood Risk
    for _, row in gdf.iterrows():
        if row["flood_risk_score"] > 0.25:
            # Calculate center for the marker
            centroid = row["geometry"].centroid
            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=10,
                color="red",
                fill=True,
                fill_color="red",
                popup=f"<b>HIGH FLOOD RISK</b><br>Ward {row['ward_id']}<br>Area Flooded: {row['flood_risk_score'] * 100:.1f}%",
            ).add_to(m)

    # 6. Save
    uoi_colormap.add_to(m)
    folium.LayerControl().add_to(m)

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    m.save(OUTPUT_HTML)
    print(f"✅ Interactive Map Saved: {OUTPUT_HTML}")
    print("-> Double-click this file to open in your browser.")


if __name__ == "__main__":
    generate_interactive_map()
