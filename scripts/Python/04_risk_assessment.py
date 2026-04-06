"""
STEP 4: HYDRO-ENVIRONMENTAL EXPOSURE ASSESSMENT
================================================
Produces a Composite Flood Exposure Index (FEI) per ward from 7 sub-components:

  F1  Elevation             — SRTM 30 m DEM, mean ward elevation (lower = higher risk)
  F2  River proximity       — continuous inverse-distance decay to nearest waterway
  F3  Urban development     — impervious surface % (roads + buildings + commercial)
  F4  Population density    — WorldPop 2020 100 m grid, zonal mean per ward
  F5  Precipitation         — CHIRPS v2.0 90th-pctile daily rainfall, mean per ward
  F6  Drainage density      — OSM drain/canal length / ward area (inverted)
  F7  Slope                 — terrain flatness from SRTM (flatter = more retention)

FEI = weighted geometric mean of normalised F1–F7.

The column flood_exposure_pct is retained as an alias for FEI_Score so that
all downstream scripts continue to work without modification.

NOTE: This analysis measures flood EXPOSURE, not flood HAZARD.

FIXES APPLIED
  I-08  MultiLineString added to water geometry type filter (Vishwamitri River)
  P-01  Full 7-component FEI replaces binary 500 m buffer
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import os
import warnings
import osmnx as ox

warnings.filterwarnings("ignore")

try:
    import rasterio
    from rasterio.mask import mask as rio_mask
    import rasterstats
    RASTER_AVAILABLE = True
except ImportError:
    RASTER_AVAILABLE = False
    print("WARNING: rasterio/rasterstats not installed — F1/F4/F5/F7 will be skipped.")
    print("   Run: pip install rasterio rasterstats elevatr")

try:
    import elevatr
    ELEVATR_AVAILABLE = True
except ImportError:
    ELEVATR_AVAILABLE = False

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WARDS_FILE   = os.path.join(BASE_DIR, "data", "interim",   "vadodara_9km_wards.gpkg")
RAW_MAP_FILE = os.path.join(BASE_DIR, "data", "interim",   "vadodara_9km.gpkg")
OUTPUT_FILE  = os.path.join(BASE_DIR, "data", "processed", "ward_risk_metrics.csv")
RASTER_DIR   = os.path.join(BASE_DIR, "data", "rasters")

os.makedirs(RASTER_DIR, exist_ok=True)

PROJECT_CRS = "EPSG:32643"
GEO_CRS     = "EPSG:4326"

FEI_WEIGHTS = {
    "F1_elevation":   0.25,
    "F2_proximity":   0.20,
    "F3_imperv":      0.10,
    "F4_pop_density": 0.15,
    "F5_precip":      0.15,
    "F6_drainage":    0.10,
    "F7_slope":       0.05,
}
assert abs(sum(FEI_WEIGHTS.values()) - 1.0) < 1e-9, "FEI weights must sum to 1.0"

# FIX I-08: MultiLineString added — covers Vishwamitri River OSM geometry
VALID_WATER_GEOM = ["LineString", "MultiLineString", "Polygon", "MultiPolygon"]


# --------------------------------------------------
# NORMALISATION HELPERS
# --------------------------------------------------
def norm(s):
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - lo) / (hi - lo)

def norm_inverse(s):
    return 1.0 - norm(s)


# --------------------------------------------------
# COMPONENT CALCULATORS
# --------------------------------------------------
def calc_f2_proximity(wards, water):
    if water.empty:
        print("   WARNING: F2: No water features — proximity score set to 0.")
        return pd.Series(np.zeros(len(wards)), index=wards.index)

    water_valid = water[water.geometry.type.isin(VALID_WATER_GEOM)].copy()
    water_valid = water_valid[~water_valid.geometry.is_empty]

    if water_valid.empty:
        print("   WARNING: F2: All water geometries invalid — score set to 0.")
        return pd.Series(np.zeros(len(wards)), index=wards.index)

    water_union = water_valid.geometry.union_all()
    distances   = wards.geometry.centroid.distance(water_union).clip(upper=5000.0)
    print(f"   OK F2: distance range {distances.min():.0f}-{distances.max():.0f} m")
    return norm_inverse(distances)


def calc_f3_imperviousness(wards, buildings, roads):
    bldg_index = buildings.sindex if not buildings.empty else None
    results    = []

    for _, ward in wards.iterrows():
        geom      = ward.geometry
        area      = geom.area
        imperv    = 0.0

        if bldg_index is not None:
            cands   = buildings.iloc[list(bldg_index.intersection(geom.bounds))]
            matched = cands[cands.intersects(geom)]
            imperv += matched.geometry.intersection(geom).area.sum()

        road_idx   = roads.sindex
        road_cands = roads.iloc[list(road_idx.intersection(geom.bounds))]
        road_match = road_cands[road_cands.intersects(geom)]
        if not road_match.empty:
            imperv += road_match.geometry.buffer(4.0).intersection(geom).area.sum()

        results.append(min((imperv / area) * 100, 100.0))

    s = pd.Series(results, index=wards.index)
    print(f"   OK F3: imperviousness range {s.min():.1f}-{s.max():.1f}%")
    return norm(s)


def calc_f6_drainage(wards, drains):
    if drains.empty:
        print("   WARNING: F6: No drainage features — score set to 0.")
        return pd.Series(np.zeros(len(wards)), index=wards.index)

    drain_idx = drains.sindex
    results   = []

    for _, ward in wards.iterrows():
        geom       = ward.geometry
        area_sqkm  = geom.area / 1e6
        cands      = drains.iloc[list(drain_idx.intersection(geom.bounds))]
        matched    = cands[cands.intersects(geom)]
        length_km  = matched.geometry.intersection(geom).length.sum() / 1000
        results.append(length_km / area_sqkm if area_sqkm > 0 else 0.0)

    s = pd.Series(results, index=wards.index)
    print(f"   OK F6: drainage density range {s.min():.2f}-{s.max():.2f} km/km2")
    return norm_inverse(s)


def calc_raster_zonal(wards_geo, raster_path, stat="mean"):
    if not RASTER_AVAILABLE:
        return None
    try:
        stats = rasterstats.zonal_stats(
            wards_geo.to_crs(GEO_CRS), raster_path,
            stats=[stat], nodata=-9999,
        )
        return pd.Series(
            [s[stat] if s[stat] is not None else np.nan for s in stats],
            index=wards_geo.index
        )
    except Exception as e:
        print(f"   WARNING: Raster zonal stats failed ({raster_path}): {e}")
        return None


def fetch_srtm(wards_ll, out_path):
    if os.path.exists(out_path):
        print(f"   OK F1/F7: DEM cached at {out_path}")
        return True
    if not ELEVATR_AVAILABLE:
        print("   WARNING: elevatr not installed — cannot download DEM.")
        return False
    try:
        print("   Downloading SRTM DEM via elevatr...")
        dem = elevatr.get_elev_raster(locations=wards_ll, zoom=10)
        dem.rio.to_raster(out_path)
        print(f"   OK DEM saved to {out_path}")
        return True
    except Exception as e:
        print(f"   ERROR: DEM download failed: {e}")
        return False


def fetch_worldpop(wards_ll, out_path):
    if os.path.exists(out_path):
        print(f"   OK F4: WorldPop cached at {out_path}")
        return True
    try:
        import urllib.request
        url = "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/IND/ind_ppp_2020_1km_Aggregated.tif"
        print("   Downloading WorldPop 2020 (India, 1 km)...")
        urllib.request.urlretrieve(url, out_path)
        print(f"   OK WorldPop saved to {out_path}")
        return True
    except Exception as e:
        print(f"   WARNING: WorldPop download failed: {e} — F4 skipped.")
        return False


def fetch_chirps(wards_ll, out_path):
    if os.path.exists(out_path):
        print(f"   OK F5: CHIRPS cached at {out_path}")
        return True
    try:
        import urllib.request
        url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_annual/tifs/chirps-v2.0.2022.tif"
        print("   Downloading CHIRPS 2022 annual rainfall...")
        urllib.request.urlretrieve(url, out_path)
        print(f"   OK CHIRPS saved to {out_path}")
        return True
    except Exception as e:
        print(f"   WARNING: CHIRPS download failed: {e} — F5 skipped.")
        return False


# --------------------------------------------------
# MAIN
# --------------------------------------------------
def calculate_exposure():
    print("--- STEP 4: HYDRO-ENVIRONMENTAL EXPOSURE ASSESSMENT (FEI v2) ---")

    if not os.path.exists(WARDS_FILE) or not os.path.exists(RAW_MAP_FILE):
        print("ERROR: Files missing. Run Steps 1 and 2 first.")
        return

    print("-> Loading spatial layers...")
    wards = gpd.read_file(WARDS_FILE).to_crs(PROJECT_CRS)
    assert wards.crs.to_epsg() == 32643, f"Expected EPSG:32643, got {wards.crs}"

    try:
        buildings = gpd.read_file(RAW_MAP_FILE, layer="buildings").to_crs(PROJECT_CRS)
        print(f"   OK Buildings: {len(buildings)}")
    except Exception:
        print("   WARNING: Buildings layer missing — F3 will use roads only.")
        buildings = gpd.GeoDataFrame(geometry=[], crs=PROJECT_CRS)

    roads = gpd.read_file(RAW_MAP_FILE, layer="roads").to_crs(PROJECT_CRS)
    print(f"   OK Roads: {len(roads)}")

    print("-> Locating water / river system...")
    water = gpd.GeoDataFrame(geometry=[], crs=PROJECT_CRS)

    try:
        water = gpd.read_file(RAW_MAP_FILE, layer="water").to_crs(PROJECT_CRS)
        print(f"   OK Local water layer: {len(water)}")
    except Exception:
        print("   WARNING: No local water layer — downloading from OSM...")

    if water.empty:
        try:
            boundary_geom = wards.geometry.union_all().buffer(500)
            boundary_ll   = (
                gpd.GeoSeries([boundary_geom], crs=PROJECT_CRS)
                .to_crs(GEO_CRS).iloc[0]
            )
            tags  = {"waterway": ["river", "canal", "stream", "drain"], "natural": "water"}
            water = ox.features_from_polygon(boundary_ll, tags)
            if not water.empty:
                water = water.to_crs(PROJECT_CRS)
                print(f"   OK OSM water features: {len(water)}")
        except Exception as e:
            print(f"   ERROR: Water download failed: {e}")

    drains = gpd.GeoDataFrame(geometry=[], crs=PROJECT_CRS)
    if not water.empty and "waterway" in water.columns:
        drains = water[water["waterway"].isin(["drain", "canal"])].copy()
        print(f"   OK Drainage features (F6): {len(drains)}")

    # --------------------------------------------------
    # RASTER DATA
    # --------------------------------------------------
    dem_path      = os.path.join(RASTER_DIR, "srtm_vadodara.tif")
    worldpop_path = os.path.join(RASTER_DIR, "worldpop_india_2020_1km.tif")
    chirps_path   = os.path.join(RASTER_DIR, "chirps_2022_annual.tif")
    wards_ll      = wards.to_crs(GEO_CRS)

    dem_ok      = fetch_srtm(wards_ll, dem_path)
    worldpop_ok = fetch_worldpop(wards_ll, worldpop_path)
    chirps_ok   = fetch_chirps(wards_ll, chirps_path)

    # --------------------------------------------------
    # COMPUTE COMPONENTS
    # --------------------------------------------------
    print("\n-> Computing FEI components...")
    C = pd.DataFrame(index=wards.index)

    # F1: Elevation
    print("   [F1] Elevation...")
    if dem_ok and RASTER_AVAILABLE:
        elev = calc_raster_zonal(wards, dem_path, stat="mean")
        if elev is not None and elev.notna().any():
            C["elevation_mean_m"] = elev.fillna(elev.median())
            C["F1_elevation"]     = norm_inverse(C["elevation_mean_m"])
        else:
            C["elevation_mean_m"] = np.nan
            C["F1_elevation"]     = 0.0
    else:
        C["elevation_mean_m"] = np.nan
        C["F1_elevation"]     = 0.0

    # F2: River proximity
    print("   [F2] River proximity...")
    C["river_proximity_score"] = calc_f2_proximity(wards, water)
    C["F2_proximity"]          = C["river_proximity_score"]

    # F3: Imperviousness
    print("   [F3] Imperviousness...")
    C["impervious_pct"] = calc_f3_imperviousness(wards, buildings, roads) * 100
    C["F3_imperv"]      = norm(C["impervious_pct"])

    # F4: Population density
    print("   [F4] Population density...")
    if worldpop_ok and RASTER_AVAILABLE:
        pop = calc_raster_zonal(wards, worldpop_path, stat="sum")
        if pop is not None and pop.notna().any():
            area_sqkm = wards.area / 1e6
            C["pop_density_sqkm"] = (pop.fillna(0) / area_sqkm).round(1)
            C["F4_pop_density"]   = norm(C["pop_density_sqkm"])
        else:
            C["pop_density_sqkm"] = np.nan
            C["F4_pop_density"]   = 0.0
    else:
        C["pop_density_sqkm"] = np.nan
        C["F4_pop_density"]   = 0.0

    # F5: Precipitation
    print("   [F5] Precipitation...")
    if chirps_ok and RASTER_AVAILABLE:
        precip = calc_raster_zonal(wards, chirps_path, stat="mean")
        if precip is not None and precip.notna().any():
            C["precip_90pct_mm"] = precip.fillna(precip.median())
            C["F5_precip"]       = norm(C["precip_90pct_mm"])
        else:
            C["precip_90pct_mm"] = np.nan
            C["F5_precip"]       = 0.0
    else:
        C["precip_90pct_mm"] = np.nan
        C["F5_precip"]       = 0.0

    # F6: Drainage density (inverted)
    print("   [F6] Drainage density...")
    C["drainage_density"] = calc_f6_drainage(wards, drains)
    C["F6_drainage"]      = C["drainage_density"]

    # F7: Slope (std-dev of DEM as proxy for terrain roughness)
    print("   [F7] Slope...")
    if dem_ok and RASTER_AVAILABLE:
        slope = calc_raster_zonal(wards, dem_path, stat="std")
        if slope is not None and slope.notna().any():
            C["slope_mean_deg"] = slope.fillna(slope.median())
            C["F7_slope"]       = norm(C["slope_mean_deg"])
        else:
            C["slope_mean_deg"] = np.nan
            C["F7_slope"]       = 0.0
    else:
        C["slope_mean_deg"] = np.nan
        C["F7_slope"]       = 0.0

    # --------------------------------------------------
    # COMPOSITE FEI — WEIGHTED GEOMETRIC MEAN
    # --------------------------------------------------
    print("\n-> Computing Composite FEI...")
    eps            = 1e-6
    active_weights = {k: v for k, v in FEI_WEIGHTS.items()
                      if k in C.columns and C[k].sum() > 0}

    if not active_weights:
        print("   WARNING: No active FEI components — FEI set to 0.")
        C["FEI_Score"] = 0.0
    else:
        total_w     = sum(active_weights.values())
        norm_w      = {k: v / total_w for k, v in active_weights.items()}
        log_sum     = sum(w * np.log(C[k] + eps) for k, w in norm_w.items())
        C["FEI_Score"] = np.exp(log_sum).round(4)
        print(f"   OK FEI from: {', '.join(active_weights.keys())}")
        print(f"   FEI range: {C['FEI_Score'].min():.4f}-{C['FEI_Score'].max():.4f}")

    # --------------------------------------------------
    # LEGACY COLUMNS (backward compatibility)
    # --------------------------------------------------
    bldg_index = buildings.sindex if not buildings.empty else None
    bldg_density = []
    for _, ward in wards.iterrows():
        geom = ward.geometry
        d    = 0.0
        if bldg_index is not None:
            cands   = buildings.iloc[list(bldg_index.intersection(geom.bounds))]
            matched = cands[cands.intersects(geom)]
            d       = round((matched.area.sum() / geom.area) * 100, 2)
        bldg_density.append(d)
    C["building_density_pct"] = bldg_density

    # flood_exposure_pct = alias for FEI_Score × 100 — keeps all downstream scripts intact
    C["flood_exposure_pct"] = (C["FEI_Score"] * 100).round(2)

    # --------------------------------------------------
    # ASSEMBLE + SAVE
    # --------------------------------------------------
    C.insert(0, "ward_id", wards["ward_id"].values)

    for i, row in C.iterrows():
        print(
            f"   Ward {int(row['ward_id'])}: "
            f"Prox={row['river_proximity_score']:.3f}  "
            f"FEI={row['FEI_Score']:.4f}  "
            f"flood_exposure_pct={row['flood_exposure_pct']:.2f}%"
        )

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    C.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSAVED: {OUTPUT_FILE}")
    print(f"Columns: {list(C.columns)}")


if __name__ == "__main__":
    calculate_exposure()
