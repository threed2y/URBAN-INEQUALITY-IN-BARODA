File: docs/database_log.md
Step 1: Spatial Database Construction

Date: December 24, 2025 Objective: To standardize disparate raw data sources into a unified geospatial database for analysis.
1. Inputs (Raw Data)

The following datasets were manually collected and placed in data/raw/:

    hospitals.csv: Locations of government hospitals, UHCs, and UPHCs.

    schools.csv: Locations of government and grant-in-aid higher secondary schools.

    transport.csv: Locations of major city bus depots and transit hubs.

    wards.geojson: Administrative boundaries of Vadodara (2011 Census definitions).

2. Methodology

    Data Cleaning: Raw CSVs are read as simple dataframes.

    Spatial Conversion: Lat/Long coordinates (WGS84) are converted to sf (Simple Features) point objects.

    Projection Standardization: All layers are reprojected to UTM Zone 43N (EPSG: 32643). This is critical because:

        Input data is in Degrees (Lat/Long), which cannot measure distance accurately.

        UTM 43N is the specific metric grid for Gujarat, allowing for accurate calculations in meters.

    Consolidation: All layers are saved into a single GeoPackage (.gpkg) to ensure data integrity.

3. Outputs

    File: data/processed/vadodara_db.gpkg

    Layers: wards, hospitals, schools, transport.