Step 1: Creation of 19-Ward Base Map

Date: December 24, 2025 Objective: To generate a topologically correct digital shapefile of the current 19 Administrative Wards of Vadodara.
1. The Problem

    Publicly available datasets (DataMeet, etc.) only contain the 2011 Census Boundaries (12 Wards).

    The current administrative reality is 19 Wards (reorganized post-2015).

    Analysis using 12 wards would be outdated and inaccurate for current policy recommendations.

2. Methodology (Primary Data Creation)

    Source: Official "New Administrative Ward-19" PDF Map from VMC (Vadodara Municipal Corporation).

    Process:

        Georeferencing: The PDF map will be overlaid onto a satellite basemap in QGIS and aligned using ground control points (GCPs) like major road intersections.

        Digitization: The 19 ward boundaries will be manually traced to create a new vector layer.

        Attribute Entry: Ward Names and IDs will be added manually.

    Validation: Total area will be compared against official VMC figures to ensure accuracy.

3. Output

    File: data/raw/wards_19.geojson

    CRS: EPSG:4326 (Lat/Long) -> Reprojected to EPSG:32643 (UTM 43N) for analysis.