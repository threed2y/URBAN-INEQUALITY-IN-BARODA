import geopandas as gpd
import matplotlib.pyplot as plt
import os
from libpysal.weights import KNN
from esda.moran import Moran_Local
from splot.esda import lisa_cluster

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UOI_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

# ⬇️ IMPORTANT: NO NAMED FILES IN ANALYSIS
TYPOLOGY_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_typology.gpkg"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_maps_clean")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------
# COMMON MAP STYLE
# --------------------------------------------------
def setup_ax(title):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.set_title(title, fontsize=15, fontweight="bold", pad=12)
    ax.axis("off")
    return fig, ax


# --------------------------------------------------
# MAP 1: URBAN OPPORTUNITY INDEX (NO LABELS)
# --------------------------------------------------
def export_uoi_clean():
    print("-> Exporting clean UOI map...")
    gdf = gpd.read_file(UOI_GPKG)

    fig, ax = setup_ax("Urban Opportunity Index (UOI)")
    gdf.plot(
        column="UOI_Score",
        cmap="RdYlBu",
        linewidth=0.4,
        edgecolor="black",
        legend=True,
        legend_kwds={"label": "UOI Score", "shrink": 0.7},
        ax=ax,
    )

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_10_UOI_Clean.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# MAP 2: FLOOD VULNERABILITY (NO LABELS)
# --------------------------------------------------
def export_flood_clean():
    print("-> Exporting clean flood map...")
    gdf = gpd.read_file(UOI_GPKG)

    fig, ax = setup_ax("Flood Vulnerability (% Area Exposed)")
    gdf.plot(
        column="flood_risk_pct",
        cmap="Blues",
        linewidth=0.4,
        edgecolor="black",
        legend=True,
        legend_kwds={"label": "Flood Risk (%)", "shrink": 0.7},
        ax=ax,
    )

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_11_Flood_Clean.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# MAP 3: SPATIAL SEGREGATION (LISA)
# --------------------------------------------------
def export_lisa_clean():
    print("-> Exporting clean LISA map...")
    gdf = gpd.read_file(UOI_GPKG)

    # CRITICAL: remove NaNs before spatial stats
    gdf = gdf.dropna(subset=["UOI_Score"]).reset_index(drop=True)

    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"
    y = gdf["UOI_Score"].values
    m_local = Moran_Local(y, w)

    fig, ax = setup_ax("Spatial Clustering of Opportunity (LISA)")
    lisa_cluster(m_local, gdf, p=0.05, ax=ax)

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_12_LISA_Clean.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# MAP 4: WARD TYPOLOGY (CATEGORICAL, ID-ONLY)
# --------------------------------------------------
def export_typology_clean():
    print("-> Exporting clean typology map...")
    gdf = gpd.read_file(TYPOLOGY_GPKG)

    fig, ax = setup_ax("Ward Typology: Opportunity–Risk Classes")
    gdf.plot(
        column="Ward_Type",
        categorical=True,
        linewidth=0.4,
        edgecolor="black",
        legend=True,
        legend_kwds={"title": "Ward Type", "loc": "lower left"},
        ax=ax,
    )

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_13_Typology_Clean.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# RUN ALL
# --------------------------------------------------
if __name__ == "__main__":
    export_uoi_clean()
    export_flood_clean()
    export_lisa_clean()
    export_typology_clean()
