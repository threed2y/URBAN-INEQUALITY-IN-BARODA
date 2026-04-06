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
TYPOLOGY_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_typology.gpkg"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_maps")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROJECT_CRS = "EPSG:32643"  # REQUIRED for spatial stats


# --------------------------------------------------
# COMMON STYLE
# --------------------------------------------------
plt.rcParams.update(
    {
        "font.size": 11,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
        "axes.edgecolor": "black",
        "axes.linewidth": 0.8,
    }
)


# --------------------------------------------------
# UOI MAP
# --------------------------------------------------
def export_uoi_map():
    print("-> Exporting UOI Map...")
    gdf = gpd.read_file(UOI_GPKG)

    # Safety
    gdf = gdf.dropna(subset=["UOI_Score"])
    if gdf.crs.is_geographic:
        gdf = gdf.to_crs(PROJECT_CRS)

    vmin = gdf["UOI_Score"].quantile(0.05)
    vmax = gdf["UOI_Score"].quantile(0.95)

    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(
        column="UOI_Score",
        cmap="RdYlBu",
        vmin=vmin,
        vmax=vmax,
        linewidth=0.4,
        edgecolor="black",
        legend=True,
        ax=ax,
    )

    ax.set_title("Urban Opportunity Index (Balanced)")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_06_UOI_Map.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# FLOOD RISK MAP
# --------------------------------------------------
def export_flood_map():
    print("-> Exporting Flood Risk Map...")
    gdf = gpd.read_file(UOI_GPKG)

    gdf = gdf.dropna(subset=["flood_exposure_pct"])
    if gdf.crs.is_geographic:
        gdf = gdf.to_crs(PROJECT_CRS)

    vmax = gdf["flood_exposure_pct"].quantile(0.95)

    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(
        column="flood_exposure_pct",
        cmap="Blues",
        vmin=0,
        vmax=vmax,
        linewidth=0.4,
        edgecolor="black",
        legend=True,
        ax=ax,
    )

    ax.set_title("Flood Vulnerability (% Ward Area at Risk)")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_07_Flood_Risk_Map.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# LISA MAP (SPATIAL SEGREGATION)
# --------------------------------------------------
def export_lisa_map():
    print("-> Exporting LISA Segregation Map...")
    gdf = gpd.read_file(UOI_GPKG)

    # CRITICAL cleaning
    gdf = gdf.dropna(subset=["UOI_Score"]).reset_index(drop=True)
    if gdf.crs.is_geographic:
        gdf = gdf.to_crs(PROJECT_CRS)

    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"

    y = gdf["UOI_Score"].values
    m_local = Moran_Local(y, w)

    fig, ax = plt.subplots(figsize=(10, 10))
    lisa_cluster(m_local, gdf, p=0.05, ax=ax, legend=True)

    ax.set_title("Spatial Segregation of Urban Opportunity (LISA)")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_08_LISA_Segregation_Map.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# TYPOLOGY MAP
# --------------------------------------------------
def export_typology_map():
    print("-> Exporting Ward Typology Map...")
    gdf = gpd.read_file(TYPOLOGY_GPKG)

    gdf = gdf.dropna(subset=["Ward_Type"])
    if gdf.crs.is_geographic:
        gdf = gdf.to_crs(PROJECT_CRS)

    category_order = [
        "High Opportunity / Low Risk",
        "High Opportunity / High Risk",
        "Low Opportunity / Low Risk",
        "Low Opportunity / High Risk",
    ]

    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(
        column="Ward_Type",
        categorical=True,
        categories=category_order,
        legend=True,
        linewidth=0.4,
        edgecolor="black",
        ax=ax,
    )

    ax.set_title("Ward Typology: Opportunity–Risk Classification")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_09_Ward_Typology_Map.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# RUN ALL
# --------------------------------------------------
if __name__ == "__main__":
    export_uoi_map()
    export_flood_map()
    export_lisa_map()
    export_typology_map()
