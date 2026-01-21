# 📂 Step 1: Spatial Database Construction

**Date:** December 24, 2025
**Objective:** To standardize disparate raw geospatial inputs into a unified, metric-projected database for downstream network analysis.

## 1. Data Inputs (Raw)
The following datasets were manually collected and staged in `data/raw/`:

| Dataset | Format | Description |
| :--- | :--- | :--- |
| **Hospitals** | `.csv` | Locations of government hospitals, Urban Health Centers (UHC), and Urban Primary Health Centers (UPHC). |
| **Schools** | `.csv` | Locations of government and grant-in-aid higher secondary schools. |
| **Transport** | `.csv` | Locations of major city bus depots and transit hubs. |
| **Wards** | `.geojson` | Administrative boundaries of Vadodara (2011 Census definitions). |

## 2. Methodology

### A. Ingestion & Cleaning
* Raw CSV files are ingested as Pandas DataFrames.
* Administrative boundaries are loaded from GeoJSON format.

### B. Spatial Conversion
* Lat/Long coordinates (Columns: `latitude`, `longitude`) are converted into geometric Point objects using the `sf` (Simple Features) standard.
* **Coordinate Reference System (CRS):** Initial assignment is **WGS84 (EPSG: 4326)**, the global standard for GPS data.

### C. Projection Standardization
* All layers are reprojected to **UTM Zone 43N (EPSG: 32643)**.
* **Rationale:** WGS84 uses degrees (angular), which are unsuitable for distance calculations.  UTM 43N is the specific planar grid for Gujarat, enabling accurate Euclidean measurement in **meters**.

### D. Consolidation
* All standardized layers are serialized into a single **GeoPackage (`.gpkg`)**.
* This ensures topological consistency and simplifies data management across the project pipeline.

## 3. Outputs
* **Primary Database:** `data/processed/vadodara_db.gpkg`
* **Layers:** `wards` (Polygon), `hospitals` (Point), `schools` (Point), `transport` (Point).
