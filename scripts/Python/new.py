import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import contextily as ctx
import folium
from folium.plugins import MiniMap, Fullscreen
import branca.colormap as cm
import os
import numpy as np

# ==========================================
# 🔹 CONFIGURATION & PATHS
# ==========================================
RESULT_PATH      = "data/processed/vadodara_final_uoi_balanced.gpkg"
LAYER_NAME       = "gnn_bym2_results"
OUTPUT_MAP       = "outputs/vadodara_real_map.png"
INTERACTIVE_MAP  = "outputs/vadodara_interactive.html"

BG_COLOR    = "#0d1117"
PANEL_COLOR = "#161b22"
ACCENT      = "#58a6ff"
CMAP_STATIC = "plasma"


def _detect_col(gdf, candidates):
    return next((c for c in candidates if c in gdf.columns), None)


def generate_vadodara_maps():
    if not os.path.exists(RESULT_PATH):
        print(f"❌  {RESULT_PATH} not found. Run GNN.py first!")
        return

    os.makedirs(os.path.dirname(OUTPUT_MAP), exist_ok=True)

    gdf = gpd.read_file(RESULT_PATH, layer=LAYER_NAME)
    gdf = gdf.to_crs(epsg=32643)

    id_col = _detect_col(gdf, ["ward_name","Ward_Name","WARD_NAME",
                                "ward_id","Ward_ID","name","Name","NAME","id","ID"])
    if id_col is None:
        id_col = next((c for c in gdf.columns
                       if c != "geometry" and gdf[c].dtype == object), None)
    if id_col is None:
        gdf["_zone_id"] = gdf.index.astype(str)
        id_col = "_zone_id"

    flood_col = _detect_col(gdf, ["swmm_flood_road_pct","flood_road_pct","flood_pct","flood_risk"])
    score_col = "hybrid_opportunity_score"

    print(f"ℹ️  ID column   : {id_col}")
    print(f"ℹ️  Flood column: {flood_col}")
    print(f"ℹ️  Columns     : {list(gdf.columns)}")

    # ══════════════════════════════════════════════════════════════════════
    # TASK 1 — STATIC MAP
    # ══════════════════════════════════════════════════════════════════════
    print("\n🎨  Generating static map …")

    fig = plt.figure(figsize=(16, 16), facecolor=BG_COLOR)
    ax  = fig.add_axes([0.02, 0.08, 0.72, 0.82])
    ax.set_facecolor(BG_COLOR)

    vmin = gdf[score_col].quantile(0.02)
    vmax = gdf[score_col].quantile(0.98)

    gdf.plot(
        column=score_col, cmap=CMAP_STATIC,
        vmin=vmin, vmax=vmax,
        alpha=0.82, edgecolor="#ffffff", linewidth=0.25,
        ax=ax, legend=False,
    )

    ctx.add_basemap(
        ax, crs=gdf.crs.to_string(),
        source=ctx.providers.CartoDB.DarkMatter,
        zoom="auto", attribution=False,
    )
    ax.set_axis_off()

    # Colourbar
    cax  = fig.add_axes([0.76, 0.22, 0.025, 0.48])
    norm = Normalize(vmin=vmin, vmax=vmax)
    sm   = ScalarMappable(cmap=CMAP_STATIC, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.outline.set_edgecolor("#444")
    cbar.ax.yaxis.set_tick_params(color="#cccccc", labelcolor="#cccccc", labelsize=9)
    cbar.set_label("Urban Opportunity Index", color="#cccccc", fontsize=10, labelpad=12)

    for val, label in [(vmin, "Low"), (vmax, "High")]:
        cax.text(1.6, (val - vmin) / (vmax - vmin), label,
                 va="center", ha="left", fontsize=8,
                 color="#aaaaaa", transform=cax.transAxes)

    # Stats panel
    pax = fig.add_axes([0.75, 0.74, 0.22, 0.16])
    pax.set_facecolor(PANEL_COLOR)
    pax.set_axis_off()
    stats = [
        ("Wards analysed", f"{len(gdf):,}"),
        ("Mean UOI",       f"{gdf[score_col].mean():.3f}"),
        ("Std dev",        f"{gdf[score_col].std():.3f}"),
        ("Min / Max",      f"{gdf[score_col].min():.2f} / {gdf[score_col].max():.2f}"),
    ]
    pax.text(0.5, 0.95, "Summary Statistics", va="top", ha="center",
             fontsize=9, color=ACCENT, fontweight="bold", transform=pax.transAxes)
    for i, (label, val) in enumerate(stats):
        y = 0.78 - i * 0.19
        pax.text(0.05, y, label, va="top", fontsize=8,
                 color="#888888", transform=pax.transAxes)
        pax.text(0.95, y, val, va="top", ha="right", fontsize=8,
                 color="#e6edf3", fontweight="bold", transform=pax.transAxes)

    # Title
    fig.text(0.02, 0.955, "VADODARA  ·  URBAN INEQUALITY INDEX",
             fontsize=20, fontweight="bold", color="#e6edf3", va="bottom")
    fig.text(0.02, 0.932,
             "Graph Convolutional Network + BYM2 Spatial Model  ·  Ward-level analysis",
             fontsize=10, color="#8b949e", va="bottom")

    # North arrow
    ax.annotate("N",  xy=(0.965, 0.055), xycoords="axes fraction",
                fontsize=13, color="#cccccc", ha="center", va="bottom", fontweight="bold")
    ax.annotate("▲", xy=(0.965, 0.040), xycoords="axes fraction",
                fontsize=14, color=ACCENT, ha="center", va="top")

    fig.text(0.98, 0.01, "© OpenStreetMap contributors · CartoDB",
             fontsize=6.5, color="#444", ha="right")

    plt.savefig(OUTPUT_MAP, dpi=300, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)
    print(f"✅  Static map saved → {OUTPUT_MAP}")

    # ══════════════════════════════════════════════════════════════════════
    # TASK 2 — INTERACTIVE FOLIUM MAP
    # ══════════════════════════════════════════════════════════════════════
    print("\n🌐  Generating interactive map …")
    gdf_web = gdf.to_crs(epsg=4326)

    colormap = cm.LinearColormap(
        colors=["#440154", "#31688e", "#35b779", "#fde725"],
        vmin=gdf_web[score_col].min(),
        vmax=gdf_web[score_col].max(),
        caption="GCN-BYM2 Urban Opportunity Index",
    )

    m = folium.Map(location=[22.3072, 73.1812], zoom_start=12, tiles=None)
    folium.TileLayer("CartoDB dark_matter", name="Dark (default)", show=True).add_to(m)
    folium.TileLayer("CartoDB positron",    name="Light").add_to(m)
    folium.TileLayer("OpenStreetMap",       name="Street map").add_to(m)

    def style_fn(feature):
        val = feature["properties"].get(score_col, 0) or 0
        return {"fillColor": colormap(val), "color": "#ffffff",
                "weight": 0.4, "fillOpacity": 0.75}

    def highlight_fn(feature):
        return {"fillColor": "#ffffff", "color": "#ffffff",
                "weight": 2.5, "fillOpacity": 0.9}

    tooltip_fields  = [id_col, score_col]
    tooltip_aliases = ["Ward:", "UOI Score:"]
    if flood_col:
        tooltip_fields.append(flood_col)
        tooltip_aliases.append("Flood Risk %:")

    folium.GeoJson(
        gdf_web,
        name="Urban Opportunity Index",
        style_function=style_fn,
        highlight_function=highlight_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields, aliases=tooltip_aliases,
            localize=True, sticky=True, labels=True,
            style="""
                background-color:#161b22;border:1px solid #30363d;
                border-radius:6px;color:#e6edf3;
                font-family:'Segoe UI',Arial,sans-serif;
                font-size:13px;padding:10px 14px;
                box-shadow:0 4px 16px rgba(0,0,0,.5);
            """,
        ),
        popup=folium.GeoJsonPopup(
            fields=tooltip_fields, aliases=tooltip_aliases,
            localize=True, labels=True,
            style="""
                background-color:#161b22;border:1px solid #58a6ff;
                border-radius:8px;color:#e6edf3;
                font-family:'Segoe UI',Arial,sans-serif;
                font-size:13px;padding:12px 16px;
            """,
        ),
    ).add_to(m)

    colormap.add_to(m)
    MiniMap(tile_layer="CartoDB dark_matter", position="bottomright",
            width=140, height=140, collapsed=False).add_to(m)
    Fullscreen(position="topright").add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    custom_html = """
    <style>
      body{background:#0d1117}
      .map-title-card{
        position:absolute;top:12px;left:52px;z-index:1000;
        background:rgba(22,27,34,.92);border:1px solid #30363d;
        border-radius:10px;padding:10px 18px 8px;
        backdrop-filter:blur(6px);box-shadow:0 4px 24px rgba(0,0,0,.6);
        pointer-events:none;
      }
      .map-title-card h2{
        margin:0 0 2px;font-size:15px;font-weight:700;color:#e6edf3;
        font-family:'Segoe UI',Arial,sans-serif;letter-spacing:.5px;
      }
      .map-title-card p{
        margin:0;font-size:11px;color:#8b949e;
        font-family:'Segoe UI',Arial,sans-serif;
      }
      .map-title-card .accent{color:#58a6ff}
      .legend{
        border-radius:8px!important;background:rgba(22,27,34,.92)!important;
        border:1px solid #30363d!important;color:#e6edf3!important;
        font-family:'Segoe UI',Arial,sans-serif!important;font-size:12px!important;
        box-shadow:0 4px 16px rgba(0,0,0,.4)!important;
      }
      .leaflet-control-fullscreen a,.leaflet-control-layers{
        background:rgba(22,27,34,.92)!important;
        border:1px solid #30363d!important;border-radius:8px!important;
        color:#e6edf3!important;font-family:'Segoe UI',Arial,sans-serif!important;
        font-size:12px!important;
      }
    </style>
    <div class="map-title-card">
      <h2>🏙️ Vadodara <span class="accent">Urban Inequality</span> Index</h2>
      <p>GCN-BYM2 Spatial Model &middot; Ward-level opportunity scores</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(custom_html))

    m.save(INTERACTIVE_MAP)
    print(f"✅  Interactive map saved → {INTERACTIVE_MAP}")
    print("\n🎉  All done!")


if __name__ == "__main__":
    generate_vadodara_maps()