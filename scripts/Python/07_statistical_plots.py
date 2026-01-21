import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_named.gpkg"
)
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_figures_clean")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# COMMON STYLE
# --------------------------------------------------
plt.rcParams.update(
    {
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "axes.edgecolor": "black",
        "axes.linewidth": 0.8,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    }
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
gdf = gpd.read_file(INPUT_GPKG)
df = pd.DataFrame(gdf.drop(columns="geometry"))


# --------------------------------------------------
# FIGURE 14: FLOOD RISK vs OPPORTUNITY (FORMAL)
# --------------------------------------------------
def plot_vulnerability_trap():
    x = df["flood_risk_pct"]
    y = df["UOI_Score"]

    r, p = pearsonr(x, y)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(x, y, color="#b2182b", alpha=0.7, s=40)

    # Regression line
    m, c = np.polyfit(x, y, 1)
    ax.plot(x, m * x + c, color="#2166ac", linewidth=2)

    ax.set_title("Flood Risk vs Urban Opportunity")
    ax.set_xlabel("Flood Risk (% of Ward Area)")
    ax.set_ylabel("Urban Opportunity Index (UOI)")

    ax.text(
        0.02,
        0.95,
        f"Pearson r = {r:.2f}\np = {p:.4f}",
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=10,
    )

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_14_Flood_vs_UOI.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# FIGURE 15: DISTRIBUTION OF OPPORTUNITY
# --------------------------------------------------
def plot_distribution():
    fig, ax = plt.subplots(figsize=(7, 5))

    ax.hist(df["UOI_Score"], bins=10, color="#2166ac", edgecolor="black")

    mean_val = df["UOI_Score"].mean()
    ax.axvline(mean_val, color="grey", linestyle="--", linewidth=1)

    ax.set_title("Distribution of Urban Opportunity")
    ax.set_xlabel("Urban Opportunity Index (UOI)")
    ax.set_ylabel("Number of Wards")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_15_UOI_Distribution.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# FIGURE 16: LORENZ CURVE (INEQUALITY)
# --------------------------------------------------
def plot_lorenz():
    values = np.sort(df["UOI_Score"].values)
    cum_values = np.cumsum(values) / values.sum()
    cum_pop = np.linspace(0, 1, len(values))

    fig, ax = plt.subplots(figsize=(6, 6))

    ax.plot(cum_pop, cum_values, color="#b2182b", linewidth=2, label="Observed")
    ax.plot([0, 1], [0, 1], color="black", linestyle="--", label="Perfect Equality")

    ax.fill_between(cum_pop, cum_pop, cum_values, color="#b2182b", alpha=0.1)

    ax.set_title("Lorenz Curve of Urban Opportunity")
    ax.set_xlabel("Cumulative Share of Wards")
    ax.set_ylabel("Cumulative Share of Opportunity")

    ax.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_16_Lorenz_Curve.png"), dpi=300)
    plt.close()


# --------------------------------------------------
# RUN ALL
# --------------------------------------------------
if __name__ == "__main__":
    plot_vulnerability_trap()
    plot_distribution()
    plot_lorenz()
