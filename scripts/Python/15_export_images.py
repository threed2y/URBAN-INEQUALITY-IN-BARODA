import geopandas as gpd
import matplotlib.pyplot as plt
import os
from libpysal.weights import KNN
from esda.moran import Moran_Local
from splot.esda import lisa_cluster


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(BASE_DIR, "data", "processed", "vadodara_final_uoi.gpkg")
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_maps")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def export_uoi_map():
    print("-> Exporting UOI Map...")
    gdf = gpd.read_file(INPUT_GPKG)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    gdf.plot(
        column="UOI_Score",
        cmap="RdYlBu",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        ax=ax,
    )

    ax.set_title("Urban Opportunity Index (UOI)", fontsize=16, fontweight="bold")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_06_UOI_Map.png"), dpi=300, bbox_inches="tight"
    )
    plt.close()


def export_flood_map():
    print("-> Exporting Flood Risk Map...")
    gdf = gpd.read_file(INPUT_GPKG)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    gdf.plot(
        column="flood_risk_pct",
        cmap="Blues",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        ax=ax,
    )

    ax.set_title("Flood Vulnerability (% Area at Risk)", fontsize=16, fontweight="bold")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_07_Flood_Risk_Map.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


def export_lisa_map():
    print("-> Exporting LISA Segregation Map...")
    gdf = gpd.read_file(INPUT_GPKG)

    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"
    y = gdf["UOI_Score"].values
    m_local = Moran_Local(y, w)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    lisa_cluster(m_local, gdf, p=0.05, ax=ax)

    ax.set_title(
        "Spatial Segregation of Opportunity (LISA Clusters)",
        fontsize=16,
        fontweight="bold",
    )
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_08_LISA_Segregation_Map.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


TYPOLOGY_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_typology.gpkg"
)


def export_typology_map():
    print("-> Exporting Ward Typology Map...")
    gdf = gpd.read_file(TYPOLOGY_GPKG)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    gdf.plot(
        column="Ward_Type",
        categorical=True,
        legend=True,
        linewidth=0.5,
        edgecolor="black",
        ax=ax,
    )

    ax.set_title(
        "Ward Typology: Opportunity–Risk Classes", fontsize=16, fontweight="bold"
    )
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_09_Ward_Typology_Map.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


if __name__ == "__main__":
    export_uoi_map()
    export_flood_map()
    export_lisa_map()
    export_typology_map()
