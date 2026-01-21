Composite Index Construction: The Geometric Approach

Urban inequality is multidimensional. No single indicator can fully capture the complex reality of deprivation. Access to a bus stop does not matter if there is no hospital at the end of the route; flood safety is irrelevant if there are no schools for social mobility.

To measure this, we construct the Urban Opportunity Index (UOI) as a composite measure of spatial justice.

<div class="callout"> <strong>The Core Challenge:</strong> How do we combine disparate metrics (minutes, meters, percentages) into a single score without masking critical failures in specific sectors? </div>

1. Aggregation Method: The Geometric Mean

Unlike traditional indices that use a simple arithmetic average (or PCA), this study utilizes Geometric Aggregation. This method, adopted by the United Nations Human Development Index (HDI) in 2010, multiplies the dimensional scores and takes the n-th root.
UOI=3IHealth​⋅IEducation​⋅IMobility​​

2. Justification: The "Non-Compensatory" Principle

The choice of Geometric Mean is driven by the theoretical requirement of Non-Compensation.

    In Arithmetic/PCA models: A severe deficit in one dimension (e.g., 0% Healthcare Access) can be mathematically "offset" by a surplus in another (e.g., 100% Road Density).

    In Geometric models: If any single dimension tends toward zero, the total index tends toward zero.

    Relevance: This ensures that the UOI reflects a holistic standard of living. A ward cannot be considered "High Opportunity" if it fails completely in healthcare, regardless of its transport score.

3. Standardization (Min-Max)

Before aggregation, all raw indicators (travel time in minutes, risk in %) were standardized to a unit-free scale of 0 to 100.

    Directionality: Indicators where "higher is better" (e.g., Building Density) were scaled directly. Indicators where "lower is better" (e.g., Travel Time, Flood Risk) were inverted (100−x).

4. Academic Standards

This methodology aligns with established frameworks for composite indicator construction:

    OECD (2008): Handbook on Constructing Composite Indicators. (Standardizes the use of Geometric aggregation for heterogeneous variables).

    UNDP (2010): The Real Wealth of Nations. (Established the geometric mean as the gold standard for human development measurement).
