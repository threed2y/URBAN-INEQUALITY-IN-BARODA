import pandas as pd
import geopandas as gpd
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
import os

# --- FILES ---
INPUT_CSV = "ward_accessibility_scores_realistic.csv"
INPUT_GPKG = "vadodara_project_data.gpkg"
OUTPUT_CSV = "ward_pca_scores.csv" 
LAYER_NAME = "wards_final_index"

print("--- GENERATING PCA SCORES ---")

# 1. LOAD DATA
if not os.path.exists(INPUT_CSV):
    print(f"❌ Error: '{INPUT_CSV}' not found. Run the accessibility script first.")
    exit()

df = pd.read_csv(INPUT_CSV)
print(f"Loaded data for {len(df)} wards.")

# 2. PREPARE DATA FOR PCA
# We use the 3 key variables: Time to Hospital, School, Transport
features = ['time_hospital_min', 'time_school_min', 'time_transport_min']

# Fill missing values (if any ward has no path) with a high penalty
X = df[features].fillna(df[features].max() * 1.1)

# 3. INVERT VARIABLS (Crucial Step)
# Currently: High Time = BAD (30 mins is worse than 5 mins)
# PCA needs: High Score = GOOD
# So we multiply by -1. Now -30 is "lower" than -5.
X_inverted = X * -1 

# 4. RUN PCA
# We assume these 3 variables are correlated (if you are far from a school, you are likely far from a hospital)
# PCA condenses them into 1 "Master Variable" (PC1)
pca = PCA(n_components=1)
principal_components = pca.fit_transform(X_inverted)

# 5. NORMALIZE TO 0-100 (The "UOI Score")
# This makes it readable. 0 = Most Deprived, 100 = Most Privileged.
scaler = MinMaxScaler(feature_range=(0, 100))
uoi_scores = scaler.fit_transform(principal_components)

# 6. ADD SCORES TO DATAFRAME
df['PCA_Raw_Value'] = principal_components # The raw statistical output
df['UOI_Score'] = uoi_scores             # The readable 0-100 score
df['Rank'] = df['UOI_Score'].rank(ascending=False).astype(int)

# 7. SAVE TO CSV
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ CSV Saved: '{OUTPUT_CSV}' (Check this file to see the numbers!)")

# 8. SAVE TO GEOPACKAGE (For QGIS)
try:
    # Load the ward shapes
    # We try 'wards_realistic_scores' first, if not found, we try 'wards'
    try:
        wards_map = gpd.read_file(INPUT_GPKG, layer="wards_realistic_scores")
    except:
        wards_map = gpd.read_file(INPUT_GPKG, layer="wards")
    
    # Add the new scores to the map
    wards_map['UOI_Score'] = df['UOI_Score']
    wards_map['Rank'] = df['Rank']
    
    # Save as the final layer
    wards_map.to_file(INPUT_GPKG, layer=LAYER_NAME, driver="GPKG")
    print(f"✅ Map Layer Saved: '{LAYER_NAME}' inside '{INPUT_GPKG}'")
except Exception as e:
    print(f"⚠️ Could not update GeoPackage: {e}")

# 9. PRINT PREVIEW
print("\n--- RESULTS PREVIEW ---")
print(df[['Rank', 'UOI_Score', 'time_hospital_min']].sort_values('Rank').head(5))
print("...")
print(df[['Rank', 'UOI_Score', 'time_hospital_min']].sort_values('Rank').tail(5))