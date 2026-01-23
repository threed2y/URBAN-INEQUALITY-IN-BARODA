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
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "thesis_figures_clean")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# COMMON STYLE (THESIS STANDARD)
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


# ==================================================
# FIGURE 14: FLOOD RISK vs OPPORTUNITY
# ==================================================
def plot_vulnerability_trap():
    df_plot = df[["flood_risk_pct", "UOI_Score"]].dropna()

    x = df_plot["flood_risk_pct"].values
    y = df_plot["UOI_Score"].values

    r, p = pearsonr(x, y)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(x, y, color="#b2182b", alpha=0.7, s=60, zorder=3)

    # Regression line
    m, c = np.polyfit(x, y, 1)
    xx = np.linspace(x.min(), x.max(), 100)
    ax.plot(xx, m * xx + c, color="#2166ac", linewidth=2, zorder=2)

    ax.set_title("Flood Risk vs Urban Opportunity")
    ax.set_xlabel("Flood Risk (% of Ward Area)")
    ax.set_ylabel("Urban Opportunity Index (UOI)")

    ax.text(
        0.02,
        0.95,
        f"Pearson r = {r:.2f}\np = {p:.3f}",
        transform=ax.transAxes,
        va="top",
    )

    ax.text(
        0.02,
        0.82,
        f"n = {len(x)} wards",
        transform=ax.transAxes,
    )

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_14_Flood_vs_UOI.png"), dpi=300)
    plt.close()


# ==================================================
# FIGURE 15: DISTRIBUTION OF OPPORTUNITY
# ==================================================
def plot_distribution():
    values = df["UOI_Score"].dropna()

    # Quantile-based bins (robust for small n)
    bins = np.quantile(values, np.linspace(0, 1, 7))

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(values, bins=bins, color="#2166ac", edgecolor="black")

    ax.axvline(values.mean(), color="black", linestyle="--", label="Mean")
    ax.axvline(values.median(), color="grey", linestyle=":", label="Median")

    ax.set_title("Distribution of Urban Opportunity")
    ax.set_xlabel("Urban Opportunity Index (UOI)")
    ax.set_ylabel("Number of Wards")
    ax.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_15_UOI_Distribution.png"), dpi=300)
    plt.close()


# ==================================================
# FIGURE 16: LORENZ CURVE (INEQUALITY)
# ==================================================
def plot_lorenz():
    values = np.sort(df["UOI_Score"].dropna().values)

    cum_values = np.cumsum(values)
    cum_values = np.insert(cum_values, 0, 0)
    cum_values = cum_values / cum_values[-1]

    cum_pop = np.linspace(0, 1, len(cum_values))

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(cum_pop, cum_values, color="#b2182b", linewidth=2, label="Observed")
    ax.plot([0, 1], [0, 1], linestyle="--", color="black", label="Perfect Equality")

    ax.fill_between(cum_pop, cum_pop, cum_values, color="#b2182b", alpha=0.15)

    ax.set_title("Lorenz Curve of Urban Opportunity")
    ax.set_xlabel("Cumulative Share of Wards (Lowest to Highest UOI)")
    ax.set_ylabel("Cumulative Share of Opportunity")
    ax.legend(frameon=False)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "Figure_16_Lorenz_Curve.png"), dpi=300)
    plt.close()


# ==================================================
# RUN ALL
# ==================================================
if __name__ == "__main__":
    plot_vulnerability_trap()
    plot_distribution()
    plot_lorenz()
