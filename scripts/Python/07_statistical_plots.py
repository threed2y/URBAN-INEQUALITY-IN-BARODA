import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

UOI_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)

FLOOD_CSV = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")

OUT_DIR = os.path.join(BASE_DIR, "results", "thesis_figures_clean")

os.makedirs(OUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", context="talk")


# --------------------------------------------------
# LOAD + MERGE (HARD SCHEMA LOCK)
# --------------------------------------------------
def load_analysis_df():
    # ---- existence checks (fail fast) ----
    if not os.path.exists(UOI_GPKG):
        sys.exit(f"❌ Missing file: {UOI_GPKG}")

    if not os.path.exists(FLOOD_CSV):
        sys.exit(f"❌ Missing file: {FLOOD_CSV}")

    gdf = gpd.read_file(UOI_GPKG)
    flood = pd.read_csv(FLOOD_CSV)

    # ---- normalize column names ----
    flood.columns = flood.columns.str.strip()

    # ---- schema lock ----
    REQUIRED_COLS = {"ward_id", "flood_exposure_pct"}

    if not REQUIRED_COLS.issubset(flood.columns):
        sys.exit(
            f"❌ Flood CSV schema mismatch.\n"
            f"Expected: {REQUIRED_COLS}\n"
            f"Found: {set(flood.columns)}"
        )

    # ---- type alignment ----
    gdf["ward_id"] = gdf["ward_id"].astype(int)
    flood["ward_id"] = flood["ward_id"].astype(int)

    df = gdf.merge(
        flood[["ward_id", "flood_exposure_pct"]],
        on="ward_id",
        how="left",
    )

    if df["flood_exposure_pct"].isna().any():
        print("⚠️ Warning: Some wards missing flood data")

    return pd.DataFrame(df.drop(columns="geometry"))


# --------------------------------------------------
# 1. FLOOD × UOI (VULNERABILITY TRAP)
# --------------------------------------------------
def plot_vulnerability_trap():
    df = load_analysis_df()
    df = df.dropna(subset=["flood_exposure_pct", "UOI_Score"])

    plt.figure(figsize=(7, 6))

    sns.scatterplot(
        data=df,
        x="flood_exposure_pct",
        y="UOI_Score",
        s=90,
        color="#2166ac",
        edgecolor="black",
        alpha=0.85,
    )

    sns.regplot(
        data=df,
        x="flood_exposure_pct",
        y="UOI_Score",
        scatter=False,
        color="#b2182b",
        line_kws={"linewidth": 2},
    )

    plt.xlabel("Flood Exposure (% of Ward Area)")
    plt.ylabel("Urban Opportunity Index (UOI)")
    plt.title("Flood Exposure vs Urban Opportunity")

    plt.tight_layout()
    plt.savefig(
        os.path.join(OUT_DIR, "Figure_14_Flood_vs_UOI.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# 2. UOI DISTRIBUTION
# --------------------------------------------------
def plot_uoi_distribution():
    df = load_analysis_df()

    plt.figure(figsize=(7, 5))

    sns.histplot(
        df["UOI_Score"].dropna(),
        bins=12,
        kde=True,
        color="#3288bd",
        edgecolor="black",
    )

    plt.xlabel("Urban Opportunity Index (UOI)")
    plt.ylabel("Number of Wards")
    plt.title("Distribution of Urban Opportunity")

    plt.tight_layout()
    plt.savefig(
        os.path.join(OUT_DIR, "Figure_15_UOI_Distribution.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# 3. LORENZ CURVE
# --------------------------------------------------
def plot_lorenz_curve():
    df = load_analysis_df()
    x = df["UOI_Score"].dropna().sort_values().values
    n = len(x)

    cum_x = x.cumsum() / x.sum()
    cum_pop = [i / n for i in range(1, n + 1)]

    plt.figure(figsize=(6, 6))
    plt.plot([0] + cum_pop, [0] + list(cum_x), linewidth=2, color="#2166ac")
    plt.plot([0, 1], [0, 1], "--", color="black")

    plt.xlabel("Cumulative Share of Wards")
    plt.ylabel("Cumulative Share of Opportunity")
    plt.title("Inequality in Urban Opportunity")

    plt.tight_layout()
    plt.savefig(
        os.path.join(OUT_DIR, "Figure_16_Lorenz_Curve.png"),
        dpi=300,
        bbox_inches="tight",
    )
    plt.close()


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    print("--- STEP 7: STATISTICAL FIGURES ---")

    plot_vulnerability_trap()
    plot_uoi_distribution()
    plot_lorenz_curve()

    print("✅ All statistical figures generated successfully")
