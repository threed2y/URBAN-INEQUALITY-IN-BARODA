import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from libpysal.weights import KNN
from esda.moran import Moran_Local
from splot.esda import lisa_cluster
from scipy.stats import pearsonr
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_figures_FINAL_PRESENTATION")
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({"font.size": 11, "axes.titlesize": 15, "axes.labelsize": 12})


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
gdf = gpd.read_file(INPUT_GPKG)
gdf = gdf.dropna(subset=["UOI_Score", "flood_risk_pct"]).reset_index(drop=True)


# --------------------------------------------------
# FIGURE 1: UOI MAP
# --------------------------------------------------
def fig_uoi_map():
    fig, ax = plt.subplots(figsize=(9, 9))
    gdf.plot(
        column="UOI_Score",
        cmap="RdYlBu_r",
        scheme="quantiles",
        k=5,
        linewidth=0.4,
        edgecolor="black",
        legend=True,
        legend_kwds={"title": "Urban Opportunity Index"},
        ax=ax,
    )
    ax.set_title("Urban Opportunity Index (UOI)")
    ax.axis("off")
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_01_UOI_Map.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# FIGURE 2: FLOOD RISK MAP
# --------------------------------------------------
def fig_flood_map():
    fig, ax = plt.subplots(figsize=(9, 9))
    gdf.plot(
        column="flood_risk_pct",
        cmap="Blues",
        linewidth=0.4,
        edgecolor="black",
        legend=True,
        legend_kwds={"label": "Flood Risk (% of Ward Area)"},
        ax=ax,
    )
    ax.set_title("Flood Vulnerability")
    ax.axis("off")
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_02_Flood_Map.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# FIGURE 3: OPPORTUNITY–RISK TYPOLOGY
# --------------------------------------------------
def fig_typology():
    uoi_m = gdf["UOI_Score"].median()
    flood_m = gdf["flood_risk_pct"].median()

    def classify(r):
        if r["UOI_Score"] < uoi_m and r["flood_risk_pct"] > flood_m:
            return "Low Opportunity / High Risk"
        if r["UOI_Score"] > uoi_m and r["flood_risk_pct"] < flood_m:
            return "High Opportunity / Low Risk"
        if r["UOI_Score"] > uoi_m and r["flood_risk_pct"] > flood_m:
            return "High Opportunity / High Risk"
        return "Low Opportunity / Low Risk"

    gdf["Typology"] = gdf.apply(classify, axis=1)

    fig, ax = plt.subplots(figsize=(9, 9))
    gdf.plot(
        column="Typology",
        categorical=True,
        legend=True,
        linewidth=0.4,
        edgecolor="black",
        ax=ax,
    )
    ax.set_title("Opportunity–Risk Ward Typology")
    ax.axis("off")
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_03_Typology_Map.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# FIGURE 4: RANKED UOI DISTRIBUTION
# --------------------------------------------------
def fig_ranked_uoi():
    df = gdf.sort_values("UOI_Score", ascending=False).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(range(1, len(df) + 1), df["UOI_Score"], marker="o")
    ax.axhline(df["UOI_Score"].mean(), linestyle="--", color="black", label="Mean")

    ax.set_xlabel("Ward Rank")
    ax.set_ylabel("Urban Opportunity Index")
    ax.set_title("Ranked Distribution of Urban Opportunity")
    ax.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_04_Ranked_UOI.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# FIGURE 5: FLOOD vs OPPORTUNITY
# --------------------------------------------------
def fig_scatter():
    x = gdf["flood_risk_pct"]
    y = gdf["UOI_Score"]
    r, p = pearsonr(x, y)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(x, y, s=60)
    m, c = np.polyfit(x, y, 1)
    ax.plot(x, m * x + c)

    ax.set_xlabel("Flood Risk (% Area)")
    ax.set_ylabel("Urban Opportunity Index")
    ax.set_title("Flood Risk vs Urban Opportunity")

    ax.text(0.02, 0.95, f"r = {r:.2f}, p = {p:.3f}", transform=ax.transAxes, va="top")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_05_Flood_vs_UOI.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# FIGURE 6: LORENZ CURVE
# --------------------------------------------------
def fig_lorenz():
    values = np.sort(gdf["UOI_Score"].values)
    cum = np.cumsum(values) / values.sum()
    cum = np.insert(cum, 0, 0)
    pop = np.linspace(0, 1, len(cum))

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(pop, cum, linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color="black")
    ax.fill_between(pop, pop, cum, alpha=0.2)

    ax.set_xlabel("Cumulative Share of Wards")
    ax.set_ylabel("Cumulative Share of Opportunity")
    ax.set_title("Lorenz Curve of Urban Opportunity")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_06_Lorenz_Curve.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# FIGURE 7: LISA CLUSTERS
# --------------------------------------------------
def fig_lisa():
    w = KNN.from_dataframe(gdf, k=4)
    w.transform = "r"
    m = Moran_Local(gdf["UOI_Score"], w)

    fig, ax = plt.subplots(figsize=(9, 9))
    lisa_cluster(m, gdf, p=0.05, ax=ax)
    ax.set_title("Spatial Clustering of Urban Opportunity (LISA)")
    ax.axis("off")

    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_07_LISA_Clusters.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# RUN ALL
# --------------------------------------------------
if __name__ == "__main__":
    fig_uoi_map()
    fig_flood_map()
    fig_typology()
    fig_ranked_uoi()
    fig_scatter()
    fig_lorenz()
    fig_lisa()

    print("✅ Thesis-grade figures generated successfully.")
    print(f"📁 Output folder: {OUTPUT_DIR}")
