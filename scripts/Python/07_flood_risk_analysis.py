import geopandas as gpd
import pandas as pd
import osmnx as ox
import matplotlib.pyplot as plt
import os
from shapely.geometry import box

# --- CONFIGURATION ---
WARDS_FILE = "/home/ethan/Downloads/URBAN-INEQUALITY-IN-BARODA/data/interim/vadodara_project.gpkg"
OUTPUT_FILE = "/home/ethan/Downloads/URBAN-INEQUALITY-IN-BARODA/data/processed/ward_flood_risk.csv"
MAP_OUTPUT = (
    "/home/ethan/Downloads/URBAN-INEQUALITY-IN-BARODA/output/maps/flood_risk_map.png"
)
BUFFER_DIST_METERS = 500  # 500m "Danger Zone" around the river


def analyze_flood_risk():
    print("--- STEP 7: FLOOD VULNERABILITY ANALYSIS (Safe Mode) ---")

    # 1. Load Wards
    if not os.path.exists(WARDS_FILE):
        print(f"❌ Error: {WARDS_FILE} not found.")
        return

    wards = gpd.read_file(WARDS_FILE)

    # Force Wards to UTM Zone 43N (Meters) for accurate area calc
    if wards.crs.to_epsg() != 32643:
        print("-> Reprojecting wards to UTM Zone 43N...")
        wards = wards.to_crs(epsg=32643)

    # 2. Fetch River Data (Fixed Strategy)
    # Instead of calculating bounds, we ask for everything within 15km of Vadodara Center
    # Center of Vadodara: 22.3072° N, 73.1812° E
    print("-> Fetching Vishwamitri River data (15km radius)...")

    try:
        # Use features_from_point (Safe & Fast)
        river = ox.features_from_point(
            (22.3072, 73.1812), tags={"waterway": "river"}, dist=15000
        )

        if river.empty:
            print("⚠️ No rivers found! (Check internet connection)")
            return

        # Filter for Vishwamitri if possible, but keep all main river segments
        # This regex looks for 'Vishwamitri' case-insensitive
        mask = (
            river["name"].astype(str).str.contains("Vishwamitri", case=False, na=False)
        )
        main_river = river[mask]

        # If specific filtering fails, just use all river lines found (fallback)
        if main_river.empty:
            print(
                "-> Specific 'Vishwamitri' name not found, using all detected river channels."
            )
            main_river = river
        else:
            print(f"-> Identified {len(main_river)} segments of Vishwamitri River.")

    except Exception as e:
        print(f"❌ Error fetching OSM data: {e}")
        return

    # 3. Create the "Flood Danger Zone"
    print(f"-> Creating {BUFFER_DIST_METERS}m Flood Risk Buffer...")

    # Project river to match Wards (UTM)
    main_river = main_river.to_crs(wards.crs)

    # Buffer logic
    flood_zone = main_river.buffer(BUFFER_DIST_METERS).unary_union
    flood_gdf = gpd.GeoDataFrame({"geometry": [flood_zone]}, crs=wards.crs)

    # 4. Calculate Intersection (Vulnerability Score)
    print("-> Calculating Ward Vulnerability Scores...")

    results = []
    for idx, ward in wards.iterrows():
        ward_area = ward.geometry.area

        # Intersection: How much of the ward is inside the flood zone?
        intersection = ward.geometry.intersection(flood_zone)
        flood_area = intersection.area

        # Score: Percentage of ward area at risk (0.00 to 1.00)
        risk_score = flood_area / ward_area

        results.append(
            {
                "ward_id": ward["ward_id"],
                "flood_risk_score": round(risk_score, 4),
                "risk_area_sqm": round(flood_area, 2),
            }
        )

    # Save Data
    df_risk = pd.DataFrame(results)
    df_risk.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved Flood Risk Data to {OUTPUT_FILE}")

    # 5. Visualization
    print("-> Generating Flood Risk Map...")
    fig, ax = plt.subplots(figsize=(12, 12))

    # A. Plot Risk Levels (Choropleth)
    wards_risk = wards.merge(df_risk, on="ward_id")
    wards_risk.plot(
        column="flood_risk_score",
        cmap="Blues",
        linewidth=0.5,
        edgecolor="black",
        legend=True,
        ax=ax,
        alpha=0.7,
        legend_kwds={
            "label": "Flood Vulnerability (0 = Safe, 1 = High Risk)",
            "shrink": 0.6,
        },
    )

    # B. Plot the River Channel
    main_river.plot(ax=ax, color="darkblue", linewidth=2, label="River Channel")

    # C. Plot the Buffer Zone (Hatched)
    flood_gdf.plot(
        ax=ax,
        facecolor="none",
        edgecolor="blue",
        hatch="///",
        alpha=0.3,
        label="500m Danger Zone",
    )

    plt.title(
        f"Flood Vulnerability Analysis: {BUFFER_DIST_METERS}m Proximity Risk",
        fontsize=16,
        weight="bold",
    )
    plt.legend(loc="upper right")
    ax.axis("off")

    # Save Map
    os.makedirs("results/maps", exist_ok=True)
    plt.savefig(MAP_OUTPUT, dpi=300, bbox_inches="tight")
    print(f"✅ Map saved to {MAP_OUTPUT}")
    plt.show()


if __name__ == "__main__":
    analyze_flood_risk()
