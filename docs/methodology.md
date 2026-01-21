Methodology

This chapter details the analytical pipeline used to model urban inequality in Vadodara. The methodology is designed to ensure transparency, replicability, and alignment with global standards in spatial econometrics.

The process follows a "Three-Engine" approach: Accessibility, Vulnerability, and Statistical Validation.
1. Study Area & Spatial Units

The study focuses on the functional urban area of Vadodara, Gujarat.

    Spatial Unit: The analysis is conducted at the level of the 19 Administrative Wards.

    Boundary Generation: In the absence of open-source cadastral maps, ward boundaries were mathematically reconstructed using Voronoi Tessellation based on civic center locations.

    The "Urban Limit": A 9km radial buffer was applied to the city center (Mandvi Gate) to capture the "Core-Periphery" dynamic, covering both the historic walled city and the developing outer ring.

<div class="note"> <strong>Why Synthetic Wards?</strong> Using Voronoi polygons ensures we have a topologically consistent, gap-free spatial fabric that approximates administrative reality for statistical modeling. </div>
2. Data Preparation (The ETL Pipeline)

Spatial data was harvested from OpenStreetMap (OSM) and government records, then processed through a rigorous Extract-Transform-Load (ETL) pipeline.

    Road Network: extracted via OSMnx, cleaned to remove isolated nodes, and simplified to a primal planar graph.

    Key Services (Destinations):

        Healthcare: Hospitals, Urban Health Centers (UHC).

        Education: Higher Secondary Schools.

        Transport: Bus Depots and Railway Stations.

    Projection: All data was projected to UTM Zone 43N (EPSG: 32643) to ensure metric accuracy for distance calculations.

3. Network-Based Accessibility Analysis

Unlike traditional "Euclidean Buffer" methods (drawing a circle on a map), this study models the city as a living network.

    Graph Theory: The city is represented as a graph G(N,E) where N are intersections and E are roads weighted by length and speed limit.

    Algorithm: We employed Dijkstra’s Shortest Path Algorithm to calculate the minimum travel time (minutes) from every ward centroid to the nearest service.

    Traffic Modeling: A "friction factor" was applied to account for real-world congestion and tortuosity (winding roads).

<div class="callout"> This approach measures <strong>Functional Accessibility</strong> (time-cost) rather than theoretical proximity, revealing the true "friction of distance" faced by peripheral residents. </div>
4. The Risk Engine (Vulnerability Modeling)

To capture the "Vulnerability Trap," we integrated environmental constraints:

    Flood Risk: Modeled by intersecting ward geometries with a 500m buffer of the Vishwamitri River.

    Metric: Percentage of ward area susceptible to inundation.

5. Construction of the Urban Opportunity Index (UOI)

The UOI serves as the master metric for the thesis.

    Normalization: All raw indicators (travel minutes, flood %) were normalized to a 0-100 scale using Min-Max Scaling.

    Aggregation: Instead of a simple average, we utilized the Geometric Mean (similar to the UN Human Development Index).
    UOI=3ScoreHealth​×ScoreEducation​×ScoreMobility​​

    Why Geometric? This penalizes imbalance. A ward with excellent roads but zero hospitals will score significantly lower than in an arithmetic average.

6. Spatial Statistical Validation

To prove that inequality is structural and not random, we applied Spatial Autocorrelation techniques using PySAL:

    Global Moran’s I: A summary statistic to test the null hypothesis of spatial randomness. (Result: I>0 implies clustering).

    LISA (Local Indicators of Spatial Association): Used to generate the "Cluster Map," identifying specific "Hotspots" (Elite Enclaves) and "Coldspots" (Deprivation Pockets).

This statistical validation transforms the thesis from a descriptive observation into a quantifiable proof of segregation.
