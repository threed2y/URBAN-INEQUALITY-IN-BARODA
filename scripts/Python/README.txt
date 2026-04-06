URBAN INEQUALITY IN BARODA — Fixed Python Scripts
==================================================
Version: v2.0  |  Date: March 2026

WHAT'S IN THIS ZIP
------------------
37 Python scripts — all bugs fixed, P-01 (FEI) integrated, P-02 (VMC wards) added.

WHAT CHANGED FROM YOUR ORIGINAL SCRIPTS
----------------------------------------
00_replace_wards_with_vmc.py  [NEW]
    Installs digitised VMC official ward boundaries into the pipeline.
    Run this ONCE before step 03. Backs up your synthetic wards automatically.

02_generate_wards_9km.py      [FIX I-07]
    Road midpoints now clipped to boundary before KMeans sampling.
    Prevents off-boundary Voronoi seeds generating sliver wards.

03_accessibility_engine.py    [FIX I-06, I-10, I-11]
    I-06: TRAFFIC_FACTOR now applied to drive speed (not just penalty).
    I-10: unary_union() replaced with union_all() for Shapely 2.x.
    I-11: Bus stops now filtered on highway=bus_stop (not amenity=bus_stop).

03b_transit_accessibility.py  [FIX I-01]
    LATLAN coordinate swap fixed: lat=coords[0], lon=coords[1].
    Bounding-box assertion added to catch future failures.

04_risk_assessment.py         [FIX I-08, P-01]
    I-08: MultiLineString added to water geometry filter (Vishwamitri River).
    P-01: Full 7-component Flood Exposure Index (FEI):
          F1 Elevation (SRTM), F2 River proximity (continuous),
          F3 Imperviousness, F4 Population density (WorldPop),
          F5 Precipitation (CHIRPS), F6 Drainage density, F7 Slope.
    flood_exposure_pct preserved as alias for backward compatibility.

05_calculate_uoi.py           [FIX I-02, I-03]
    I-02: All sub-scores explicitly clipped to [0,1] before geometric mean.
    I-03: UOI_Score stays on [0,1]. UOI_Display (x100) added for maps only.

08_spatial_analysis.py        [FIX I-05]
    permutations raised to 9999. E[I] and z-score now printed.

08c_moran_i.py                [FIX I-05, I-13]
    I-05: permutations=9999.
    I-13: Both scatter axes demeaned. Quadrant labels now correct.

12_robustness_checks.py       [FIX I-09]
    Hardcoded normalization bounds replaced with data-driven percentiles.

13_vulnerability_index.py     [FIX I-04]
    flood_risk_pct renamed to flood_exposure_pct.

14_ward_typology.py           [FIX I-04, I-14]
    I-04: flood_risk_pct renamed to flood_exposure_pct.
    I-14: Threshold metadata saved to companion CSV (not just gdf.attrs).

19_kolm_pollak_ede.py         [FIX I-12]
    Epsilon moved after normalisation. Kappa range updated to [0.5, 1.0, 2.0].

22_final_spatial.py           [FIX I-05]
    permutations=9999.

07b, 07c, 07d, 07e, 07f, 09, 10, 15, 18, 21  [FIX I-04]
    flood_risk_pct renamed to flood_exposure_pct in all visualisation
    and reporting scripts.

HOW TO RUN
----------
1. Copy wards_19_vmcdigitised.gpkg to:  data/raw/
2. python3 Python/00_replace_wards_with_vmc.py
3. python3 Python/01_data_mining_9km.py       (skip if data already mined)
4. python3 Python/03_accessibility_engine.py
5. python3 Python/03b_transit_accessibility.py
6. python3 Python/04_risk_assessment.py       (downloads SRTM/WorldPop/CHIRPS on first run)
7. python3 Python/05_calculate_uoi.py
8. python3 Python/13_vulnerability_index.py
9. python3 Python/08_spatial_analysis.py
10. python3 Python/19_kolm_pollak_ede.py
11. python3 Python/23_final_Summary.py

FEI RASTER DEPENDENCIES (for 04_risk_assessment.py)
----------------------------------------------------
pip install rasterio rasterstats elevatr
Rasters are downloaded automatically on first run and cached in data/rasters/.
If download fails, affected components (F1/F4/F5/F7) are skipped gracefully
and FEI is computed from the remaining components with re-normalised weights.

THESIS METHODOLOGY NOTE (for 00_replace_wards_with_vmc.py)
------------------------------------------------------------
Ward boundaries were digitised from the official Vadodara Municipal Corporation
ward boundary map using watershed segmentation seeded by ward number positions.
Georeferencing was calibrated using the map scale bar (8 km reference) anchored
to Mandvi Gate (22.2973N, 73.2062E), yielding ~53 m/pixel resolution and
positional accuracy of approximately +/-150 m. Total digitised area: 206 km2
(VMC official: 204 km2, 98.4% accuracy).
