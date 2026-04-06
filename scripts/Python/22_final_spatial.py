import geopandas as gpd
import pandas as pd
import numpy as np
from libpysal.weights import KNN
from esda.moran import Moran, Moran_Local
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

UOI_GPKG = os.path.join(
    BASE_DIR, "data", "processed", "vadodara_final_uoi_balanced.gpkg"
)
FLOOD_CSV = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")

OUT_DIR = os.path.join(BASE_DIR, "results", "spatial_statistics")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_CSV = os.path.join(OUT_DIR, "spatial_statistics_summary.csv")


# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def normalize(s):
    return (s - s.min()) / (s.max() - s.min())


def kolm_pollak_ede(x, kappa):
    x = np.array(x)
    return -(1 / kappa) * np.log(np.mean(np.exp(-kappa * x)))


# HELPER FUNCTION
def spatial_diagnostics_table(df, w, variable, moran, out_path):
    diagnostics = pd.DataFrame(
        {
            "Variable": [variable],
            "N": [len(df)],
            "Spatial_Weights": ["KNN-4 (row-standardized)"],
            "Mean_Neighbors": [np.mean([len(w.neighbors[i]) for i in w.neighbors])],
            "Min_Neighbors": [min(len(v) for v in w.neighbors.values())],
            "Max_Neighbors": [max(len(v) for v in w.neighbors.values())],
            "Expected_I": [round(moran.EI, 4)],
            "Moran_I": [round(moran.I, 4)],
            "Z_Score": [round(moran.z_sim, 3)],
            "P_Value": [round(moran.p_sim, 4)],
            "Permutations": [moran.permutations],
        }
    )

    diagnostics.to_csv(out_path, index=False)
    print(f"✓ Spatial diagnostics table saved → {out_path}")


# SPATIAL STATISTICS
def spatial_diagnostics_all(df, w, variables, out_path):
    rows = []

    neighbor_counts = [len(w.neighbors[i]) for i in w.neighbors]

    for var in variables:
        y = df[var].values
        moran = Moran(y, w, permutations=9999)

        rows.append(
            {
                "Variable": var,
                "N": len(df),
                "Spatial_Weights": "KNN-4 (row-standardized)",
                "Mean_Neighbors": round(np.mean(neighbor_counts), 2),
                "Min_Neighbors": min(neighbor_counts),
                "Max_Neighbors": max(neighbor_counts),
                "Expected_I": round(moran.EI, 4),
                "Moran_I": round(moran.I, 4),
                "Z_Score": round(moran.z_sim, 3),
                "P_Value": round(moran.p_sim, 4),
                "Permutations": moran.permutations,
            }
        )

    diagnostics = pd.DataFrame(rows)
    diagnostics.to_csv(out_path, index=False)

    print(f"✓ Appendix spatial diagnostics saved → {out_path}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def export_spatial_statistics():
    print("→ Generating spatial statistics dataset")

    # ----------------------------
    # LOAD DATA
    # ----------------------------
    gdf = gpd.read_file(UOI_GPKG)
    flood = pd.read_csv(FLOOD_CSV)

    # ----------------------------
    # STANDARDIZE ward_id
    # ----------------------------
    gdf["ward_id"] = pd.to_numeric(gdf["ward_id"], errors="coerce")
    flood["ward_id"] = pd.to_numeric(flood["ward_id"], errors="coerce")

    gdf = gdf.dropna(subset=["ward_id"])
    flood = flood.dropna(subset=["ward_id"])

    gdf["ward_id"] = gdf["ward_id"].astype(int)
    flood["ward_id"] = flood["ward_id"].astype(int)

    # ----------------------------
    # DETECT FLOOD COLUMN IN CSV
    # ----------------------------
    flood_col = next(
        (c for c in flood.columns if "flood" in c.lower()),
        None,
    )

    if flood_col is None:
        raise RuntimeError("❌ No flood-related column found in ward_risk_metrics.csv")

    print(f"✓ Using flood column: {flood_col}")

    # ----------------------------
    # REMOVE EXISTING FLOOD COLUMN
    # (prevents _x / _y merge bug)
    # ----------------------------
    if "flood_exposure_pct" in gdf.columns:
        print("⚠️ Dropping existing flood_exposure_pct from GPKG")
        gdf = gdf.drop(columns=["flood_exposure_pct"])

    # ----------------------------
    # SAFE MERGE
    # ----------------------------
    flood_subset = flood[["ward_id", flood_col]].rename(
        columns={flood_col: "flood_exposure_pct"}
    )

    df = gdf.merge(flood_subset, on="ward_id", how="left", validate="one_to_one")

    # ----------------------------
    # SANITY CHECKS
    # ----------------------------
    if "flood_exposure_pct" not in df.columns:
        raise RuntimeError("❌ Flood column missing after merge")

    if df["flood_exposure_pct"].isna().all():
        raise RuntimeError("❌ Flood values are all NaN after merge")

    # ----------------------------
    # CVI COMPONENTS
    # ----------------------------
    df["Low_Opportunity"] = 1 - normalize(df["UOI_Score"])
    df["High_Flood_Risk"] = normalize(df["flood_exposure_pct"])
    df["High_Density"] = normalize(df["building_density_pct"])

    eps = 1e-3
    df["CVI"] = (
        (df["Low_Opportunity"] + eps)
        * (df["High_Flood_Risk"] + eps)
        * (df["High_Density"] + eps)
    ) ** (1 / 3)

    # ----------------------------
    # SPATIAL AUTOCORRELATION
    # ----------------------------
    w = KNN.from_dataframe(df, k=4)
    w.transform = "r"

    y = df["UOI_Score"].values

    moran = Moran(y, w, permutations=9999)
    local = Moran_Local(y, w, permutations=9999)

    df["local_moran_I"] = local.Is
    df["spatial_lag_uoi"] = local.z_sim
    df["num_neighbors"] = [len(w.neighbors[i]) for i in range(len(df))]

    def lisa_label(q, p):
        if p > 0.05:
            return "Not Significant"
        return {
            1: "High–High",
            2: "Low–High",
            3: "Low–Low",
            4: "High–Low",
        }[q]

    df["lisa_cluster"] = [
        lisa_label(local.q[i], local.p_sim[i]) for i in range(len(df))
    ]

    # ----------------------------
    # INEQUALITY (KOLM–POLLAK EDE)
    # ----------------------------
    uoi_norm = normalize(df["UOI_Score"]) + 1e-6
    mean_uoi = uoi_norm.mean()

    ede_05 = kolm_pollak_ede(uoi_norm, 0.5)
    ede_10 = kolm_pollak_ede(uoi_norm, 1.0)
    ede_20 = kolm_pollak_ede(uoi_norm, 2.0)

    # ----------------------------
    # APPENDIX: SPATIAL DIAGNOSTICS (ALL VARIABLES)
    # ----------------------------
    DIAG_ALL_CSV = os.path.join(
        OUT_DIR, "appendix_spatial_diagnostics_all_variables.csv"
    )

    diagnostic_vars = [
        "UOI_Score",
        "CVI",
        "Low_Opportunity",
        "High_Flood_Risk",
        "High_Density",
        "building_density_pct",
        "flood_exposure_pct",
    ]

    spatial_diagnostics_all(
        df=df, w=w, variables=diagnostic_vars, out_path=DIAG_ALL_CSV
    )

    # ----------------------------
    # FINAL EXPORT
    # ----------------------------
    out = pd.DataFrame(df.drop(columns="geometry"))

    out["global_moran_I"] = round(moran.I, 3)
    out["global_moran_p"] = round(moran.p_sim, 4)
    out["spatial_weights"] = "KNN-4 (row-standardized)"

    out["mean_uoi"] = round(mean_uoi, 3)
    out["ede_kappa_0_5"] = round(ede_05, 3)
    out["ede_kappa_1_0"] = round(ede_10, 3)
    out["ede_kappa_2_0"] = round(ede_20, 3)
    out["inequality_penalty_k1"] = round(mean_uoi - ede_10, 3)

    out.to_csv(OUT_CSV, index=False)
    print(f"✓ Saved → {OUT_CSV}")


# --------------------------------------------------
if __name__ == "__main__":
    export_spatial_statistics()
