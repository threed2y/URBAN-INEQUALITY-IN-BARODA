Creation of 19-Ward Base Map

1. The Problem

    Publicly available datasets (DataMeet, etc.) only contain the 2011 Census Boundaries (12 Wards).

    The current administrative reality is 19 Wards (reorganized post-2015).

    Analysis using 12 wards would be outdated and inaccurate for current policy recommendations.

2. Methodology (Primary Data Creation)

    The Method: Voronoi Tesselation

        To define the spatial boundaries of the 19 administrative wards in Vadodara, this study employed the Voronoi Tessellation (Thiessen Polygon) method.

        In the absence of open-source cadastral shapefiles from the municipal corporation, Voronoi tessellation is the standard scientific proxy for approximating administrative zones.
        It partitions a plane into regions close to a specific set of "seed points."

    The Procedure:

        The ward boundaries were computationally generated using the following algorithm:

        1.Seed Point Identification:

            Coordinates for the 19 Ward Centers were identified based on the location of Ward Offices and major civic clusters within Vadodara.

            Tools: Geocoding via OpenStreetMap APIs.

        2.Tessellation Generation:

            The scipy.spatial.Voronoi algorithm was applied to these 19 seed points.

            Logic: Mathematically, perpendicular bisectors are drawn between all seed points. The intersection of these bisectors forms polygons where every point inside the polygon is closer to its specific ward center than to any other ward center.

        3.Spatial Clipping (The City Limit):

            Since Voronoi polygons extend to infinity, a 9km Radial Buffer centered on Mandvi Gate (the historic city center) was used as a "Hard Clip."

            Result: This restricts the analysis to the functional urban area (approx. 254 sq km), covering both the dense core and the developing periphery.

        4.Geometric Standardization:

        The resulting geometry was reprojected to EPSG:32643 (UTM Zone 43N) to ensure accurate calculation of density and travel distances in meters.

3. Literature Context

    The use of Voronoi diagrams as a proxy for administrative and service catchment areas is well-established in urban geography and spatial analysis.

    Proximal Regions: Voronoi polygons represent the "natural catchment" of a center. In urban planning, this assumes that residents are most likely to access services or be governed by the administrative node closest to them (Aurenhammer, 1991).

    Data Scarcity Solutions: Standard GIS literature (Burrough & McDonnell, 1998) cites Thiessen polygons as the primary method for qualitative spatial division when continuous boundary data is unavailable.

    Service Area Analysis: The method is widely used in healthcare and retail geography to define "Hospital Service Areas" (HSAs) when patient data is aggregated by point locations (Dartmouth Atlas of Health Care).

4. References

    Aurenhammer, F. (1991). Voronoi diagrams—a survey of a fundamental geometric data structure. ACM Computing Surveys (CSUR).

    Burrough, P. A., & McDonnell, R. A. (1998). Principles of Geographical Information Systems. Oxford University Press.
