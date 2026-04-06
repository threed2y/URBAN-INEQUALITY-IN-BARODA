import geopandas as gpd
import numpy as np
import pandas as pd
from libpysal.weights import Queen
import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import pymc as pm
import arviz as az
import os

# ==========================================
# 🔹 STEP 1: LOAD INTEGRATED DATA
# ==========================================
FILE_PATH = "/home/ethan/Downloads/URBAN-INEQUALITY-IN-BARODA/data/processed/vadodara_final_uoi_balanced.gpkg"

if not os.path.exists(FILE_PATH):
    raise FileNotFoundError(f"Missing data file: {FILE_PATH}")

gdf = gpd.read_file(FILE_PATH)

# ==========================================
# 🔹 STEP 2: FEATURES (Including SWMM Results)
# ==========================================
feature_cols = [
    "Score_Health",
    "Score_Edu",
    "Score_Mobility",
    "bus_access_score",
    "building_density_pct",
    "swmm_flood_road_pct",  # Success: 1003 failures found
    "swmm_mean_depth",
    "bus_stop_density"
]

target_col = "UOI_Score"

# Cleanup: remove rows with missing features or target
gdf = gdf.dropna(subset=feature_cols + [target_col]).reset_index(drop=True)

X = gdf[feature_cols].values
y = gdf[target_col].values

# Normalize features (Z-score)
X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-6)

# ==========================================
# 🔹 STEP 3: GRAPH & SPATIAL WEIGHTS
# ==========================================
# Build adjacency from geometries
w = Queen.from_dataframe(gdf, use_index=False)
W_binary = w.full()[0]
W_sparse = (W_binary > 0).astype(int)

# Convert to PyTorch Geometric Edge Index
edge_index = torch.tensor(np.array(np.nonzero(W_binary)), dtype=torch.long)

# ==========================================
# 🔹 STEP 4: GNN MODEL (FIXED)
# ==========================================
class GCN(torch.nn.Module):
    def __init__(self, in_channels):
        super().__init__()
        self.conv1 = GCNConv(in_channels, 32)
        self.conv2 = GCNConv(32, 16)
        self.conv3 = GCNConv(16, 1)

    def forward(self, x, edge_index):
        # Pass edge_index through ALL layers for spatial convolution
        x = torch.relu(self.conv1(x, edge_index))
        x = torch.relu(self.conv2(x, edge_index))
        x = self.conv3(x, edge_index) # FIXED: Added edge_index
        return x.squeeze()

# Train GNN
x_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)
data = Data(x=x_tensor, edge_index=edge_index, y=y_tensor)

model = GCN(in_channels=X.shape[1])
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

print("🚀 Training GNN with SWMM Hydraulic Features...")
for epoch in range(201):
    model.train()
    optimizer.zero_grad()
    out = model(data.x, data.edge_index)
    loss = torch.nn.MSELoss()(out, data.y)
    loss.backward()
    optimizer.step()
    if epoch % 50 == 0:
        print(f"  Epoch {epoch}, Loss: {loss.item():.4f}")

# Extract GNN Predictions for Bayesian Stage
model.eval()
gnn_pred = model(data.x, data.edge_index).detach().numpy()

# ==========================================
# 🔹 STEP 5: BAYESIAN BYM2 REFINEMENT
# ==========================================
print("🧠 Running BYM2 Spatial Decomposition (Stabilized)...")
n = len(y)

with pm.Model() as bym2_model:
    # 1. Base Mean components
    intercept = pm.Normal("intercept", mu=y.mean(), sigma=1)
    beta_gnn = pm.Normal("beta_gnn", mu=1.0, sigma=0.2) 

    # 2. Variance Components (Stabilized Priors)
    sigma_total = pm.Exponential("sigma_total", 2.0)
    rho = pm.Beta("rho", alpha=2, beta=2) # Balances spatial vs. noise
    
    # 3. Spatial Structured Effect (CAR)
    phi = pm.CAR("phi", mu=np.zeros(n), W=W_sparse, alpha=0.99, tau=1.0, shape=n)
    
    # 4. Spatial Unstructured Noise
    epsilon = pm.Normal("epsilon", mu=0, sigma=1, shape=n)

    # 5. BYM2 Combination
    spatial_effect = sigma_total * (pm.math.sqrt(rho) * phi + pm.math.sqrt(1 - rho) * epsilon)

    # 6. Predictor
    mu = intercept + (beta_gnn * gnn_pred) + spatial_effect

    # 7. Likelihood
    sigma_obs = pm.Exponential("sigma_obs", 2.0)
    y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma_obs, observed=y)

    # 8. Sampling
    trace = pm.sample(draws=1000, tune=1000, chains=2, target_accept=0.95, init="jitter+adapt_diag")

# ==========================================
# 🔹 STEP 6: AGGREGATE RESULTS & SAVE
# ==========================================
print("📊 Aggregating GNN+BYM2 results to GeoPackage...")

# Extract posterior means
post_means = trace.posterior.mean(dim=("chain", "draw"))

# Create results DataFrame
results_df = pd.DataFrame({
    'gnn_prediction': gnn_pred,
    'bym2_spatial_phi': post_means['phi'].values,
    'hybrid_opportunity_score': (post_means['intercept'].values + 
                                post_means['beta_gnn'].values * gnn_pred + 
                                post_means['sigma_total'].values * (np.sqrt(post_means['rho'].values) * post_means['phi'].values))
})

# --- FIX: Drop existing columns if they exist to avoid 'no suffix specified' error ---
cols_to_drop = ['gnn_prediction', 'bym2_spatial_phi', 'hybrid_opportunity_score']
gdf = gdf.drop(columns=[c for c in cols_to_drop if c in gdf.columns])

# Join new results
gdf = gdf.join(results_df).fillna(0)

# Save to GeoPackage
gdf.to_file(FILE_PATH, layer="gnn_bym2_results", driver="GPKG")

print(f"\n--- SUCCESS ---")
print(f"Results saved to: {FILE_PATH} (Layer: gnn_bym2_results)")
print(f"GNN Regression Weight (Beta): {post_means['beta_gnn'].values:.3f}")
print(f"Spatial Connectivity Weight (Rho): {post_means['rho'].values:.3f}")