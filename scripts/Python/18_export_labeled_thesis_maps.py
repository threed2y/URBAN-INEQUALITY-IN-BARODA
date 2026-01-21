import geopandas as gpd
import matplotlib.pyplot as plt
import os
import pandas as pd
from libpysal.weights import KNN
from esda.moran import Moran_Local
from splot.esda import lisa_cluster


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_named.gpkg"
)
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_maps_labeled")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def export_uoi_labeled():
    print("-> Exporting labeled UOI map...")
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

    # Label top & bottom wards
    highlight = pd.concat([gdf.nlargest(5, "UOI_Score"), gdf.nsmallest(5, "UOI_Score")])

    for _, row in highlight.iterrows():
        x, y = row.geometry.centroid.xy
        ax.text(
            x[0],
            y[0],
            row["ward_name"],
            fontsize=8,
            ha="center",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
        )

    ax.set_title(
        "Urban Opportunity Index (Top & Bottom Wards Labeled)", fontweight="bold"
    )
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_10_UOI_Labeled.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


def export_flood_labeled():
    print("-> Exporting labeled flood map...")
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

    high_risk = gdf[gdf["flood_risk_pct"] > gdf["flood_risk_pct"].quantile(0.75)]

    for _, row in high_risk.iterrows():
        x, y = row.geometry.centroid.xy
        ax.text(x[0], y[0], row["ward_name"], fontsize=8, ha="center", color="darkblue")

    ax.set_title("Flood Vulnerability (High-Risk Wards Labeled)", fontweight="bold")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_11_Flood_Labeled.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


def export_lisa_labeled():
    print("-> Exporting labeled LISA map...")
    gdf = gpd.read_file(INPUT_GPKG)

    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"
    y = gdf["UOI_Score"].values
    m_local = Moran_Local(y, w)

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    lisa_cluster(m_local, gdf, p=0.05, ax=ax)

    # Label only significant clusters
    sig = gdf[m_local.p_sim < 0.05]

    for _, row in sig.iterrows():
        x, y = row.geometry.centroid.xy
        ax.text(x[0], y[0], row["ward_name"], fontsize=7, ha="center")

    ax.set_title("Spatial Segregation (LISA Clusters Labeled)", fontweight="bold")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_12_LISA_Labeled.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


TYPOLOGY_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_typology_named.gpkg"
)


def export_typology_labeled():
    print("-> Exporting labeled typology map...")
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

    for _, row in gdf.iterrows():
        x, y = row.geometry.centroid.xy
        ax.text(x[0], y[0], row["ward_name"], fontsize=7, ha="center")

    ax.set_title("Ward Typology (All Wards Labeled)", fontweight="bold")
    ax.axis("off")

    plt.savefig(
        os.path.join(OUTPUT_DIR, "Figure_13_Typology_Labeled.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


if __name__ == "__main__":
    export_uoi_labeled()
    export_flood_labeled()
    export_lisa_labeled()
    export_typology_labeled()
