import geopandas as gpd
import pandas as pd
import folium
import branca.colormap as cm
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UOI_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
FLOOD_CSV = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")

OUTPUT_DIR = os.path.join(BASE_DIR, "results", "interactive_maps")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUT_UOI = os.path.join(OUTPUT_DIR, "map_uoi.html")
OUT_FLOOD = os.path.join(OUTPUT_DIR, "map_flood.html")


# --------------------------------------------------
def generate_maps():
    print("--- STEP 6 (FINAL): THESIS MAPS ---")

    # -------------------------------
    # LOAD DATA
    # -------------------------------
    gdf = gpd.read_file(UOI_GPKG)
    flood = pd.read_csv(FLOOD_CSV)

    gdf["ward_id"] = gdf["ward_id"].astype(int)
    flood["ward_id"] = flood["ward_id"].astype(int)

    # -------------------------------
    # DETECT FLOOD COLUMN
    # -------------------------------
    flood_col = next(c for c in flood.columns if "flood" in c.lower())
    print(f"→ Using flood column: {flood_col}")

    # -------------------------------
    # MERGE FLOOD DATA
    # -------------------------------
    gdf = gdf.merge(
        flood[["ward_id", flood_col]],
        on="ward_id",
        how="left",
    )

    # Handle suffixes safely
    if f"{flood_col}_y" in gdf.columns:
        gdf["flood_exposure_pct"] = gdf[f"{flood_col}_y"]
    elif flood_col in gdf.columns:
        gdf["flood_exposure_pct"] = gdf[flood_col]
    else:
        raise RuntimeError("❌ Flood column could not be resolved after merge")

    # -------------------------------
    # CRS + MAP CENTER
    # -------------------------------
    if gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    center = gdf.geometry.union_all().centroid

    # ==================================================
    # MAP 1: URBAN OPPORTUNITY INDEX
    # ==================================================
    print("→ Rendering UOI map")

    m1 = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles="CartoDB positron",
    )

    uoi_min = gdf["UOI_Score"].quantile(0.05)
    uoi_max = gdf["UOI_Score"].quantile(0.95)

    cmap_uoi = cm.LinearColormap(
        colors=["#9e0142", "#f46d43", "#fdae61", "#abdda4", "#3288bd"],
        vmin=uoi_min,
        vmax=uoi_max,
        caption="Urban Opportunity Index (0–100)",
    )

    folium.GeoJson(
        gdf,
        name="UOI",
        style_function=lambda f: {
            "fillColor": cmap_uoi(f["properties"]["UOI_Score"]),
            "color": "#333333",
            "weight": 0.4,
            "fillOpacity": 0.85,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "UOI_Score"],
            aliases=["Ward", "UOI"],
            localize=True,
        ),
    ).add_to(m1)

    cmap_uoi.add_to(m1)
    folium.LayerControl().add_to(m1)
    m1.save(OUT_UOI)

    # ==================================================
    # MAP 2: FLOOD EXPOSURE
    # ==================================================
    print("→ Rendering Flood map")

    m2 = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles="CartoDB dark_matter",
    )

    flood_max = gdf["flood_exposure_pct"].quantile(0.95)

    cmap_flood = cm.LinearColormap(
        colors=["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
        vmin=0,
        vmax=flood_max,
        caption="Flood Exposure (% of Ward Area)",
    )

    folium.GeoJson(
        gdf,
        name="Flood Exposure",
        style_function=lambda f: {
            "fillColor": cmap_flood(f["properties"]["flood_exposure_pct"]),
            "color": "#ffffff",
            "weight": 0.4,
            "fillOpacity": 0.85,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["ward_id", "flood_exposure_pct"],
            aliases=["Ward", "Flood Exposure (%)"],
            localize=True,
        ),
    ).add_to(m2)

    cmap_flood.add_to(m2)
    folium.LayerControl().add_to(m2)
    m2.save(OUT_FLOOD)

    print("✅ Maps generated successfully")
    print(f"   → {OUT_UOI}")
    print(f"   → {OUT_FLOOD}")


# --------------------------------------------------
if __name__ == "__main__":
    generate_maps()
