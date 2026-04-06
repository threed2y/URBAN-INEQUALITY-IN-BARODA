import geopandas as gpd
import folium
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "results", "interactive_bivariate_maps")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUT_MAP = os.path.join(OUTPUT_DIR, "Bivariate_UOI_Flood_Toggle.html")


# --------------------------------------------------
# LEGEND
# --------------------------------------------------
def add_bivariate_legend(m):
    legend = """
    <div style="
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 270px;
        background-color: white;
        border: 2px solid #444;
        z-index: 9999;
        font-size: 13px;
        padding: 10px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    ">
    <b>Bivariate Legend</b><br>
    <i>Urban Opportunity × Flood Risk</i><br><br>

    <div><span style="background:#31a354;width:18px;height:18px;display:inline-block;"></span>
    &nbsp; High Opportunity / Low Risk</div>

    <div><span style="background:#2b8cbe;width:18px;height:18px;display:inline-block;"></span>
    &nbsp; High Opportunity / High Risk</div>

    <div><span style="background:#de2d26;width:18px;height:18px;display:inline-block;"></span>
    &nbsp; Low Opportunity / Low Risk</div>

    <div><span style="background:#8c2d04;width:18px;height:18px;display:inline-block;"></span>
    &nbsp; <b>Low Opportunity / High Risk</b></div>

    <hr>
    <small>
    Opportunity ↑ = Better access<br>
    Flood Risk ↑ = Higher exposure
    </small>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend))


# --------------------------------------------------
# TOOLTIP
# --------------------------------------------------
def tooltip():
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
            "UOI Score",
            "Flood Risk (%)",
            "Building Density (%)",
            "Hospital Access (min)",
            "School Access (min)",
            "Bus Access (min)",
            "Highway Access (min)",
        ],
        localize=True,
        sticky=True,
    )


# --------------------------------------------------
# MAIN MAP
# --------------------------------------------------
def build_bivariate_map():
    print("→ Creating bivariate map with toggle layers...")

    gdf = gpd.read_file(INPUT_GPKG).to_crs("EPSG:4326")

    uoi_thr = gdf["UOI_Score"].median()
    flood_thr = gdf["flood_exposure_pct"].median()

    def classify(row):
        if row["UOI_Score"] >= uoi_thr and row["flood_exposure_pct"] < flood_thr:
            return "High Opportunity / Low Risk"
        if row["UOI_Score"] >= uoi_thr and row["flood_exposure_pct"] >= flood_thr:
            return "High Opportunity / High Risk"
        if row["UOI_Score"] < uoi_thr and row["flood_exposure_pct"] < flood_thr:
            return "Low Opportunity / Low Risk"
        return "Low Opportunity / High Risk"

    gdf["Bivariate"] = gdf.apply(classify, axis=1)

    palette = {
        "High Opportunity / Low Risk": "#31a354",
        "High Opportunity / High Risk": "#2b8cbe",
        "Low Opportunity / Low Risk": "#de2d26",
        "Low Opportunity / High Risk": "#8c2d04",
    }

    center = gdf.geometry.union_all().centroid

    m = folium.Map(
        location=[center.y, center.x],
        zoom_start=12,
        tiles=None,
    )

    # Basemaps
    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Satellite",
        attr="Esri",
    ).add_to(m)

    folium.TileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        name="Terrain",
        attr="Esri",
    ).add_to(m)

    # --------------------------------------------------
    # TOGGLE LAYERS (ONE PER CLASS)
    # --------------------------------------------------
    for label, color in palette.items():
        subset = gdf[gdf["Bivariate"] == label]

        opacity = 0.45 if "High Risk" in label else 0.75

        folium.GeoJson(
            subset,
            name=label,
            style_function=lambda f, col=color, op=opacity: {
                "fillColor": col,
                "color": "#000000",
                "weight": 0.4,
                "fillOpacity": op,
            },
            tooltip=tooltip(),
        ).add_to(m)

    add_bivariate_legend(m)
    folium.LayerControl(collapsed=False).add_to(m)

    m.save(OUT_MAP)
    print(f"✓ Saved: {OUT_MAP}")


# --------------------------------------------------
if __name__ == "__main__":
    build_bivariate_map()
