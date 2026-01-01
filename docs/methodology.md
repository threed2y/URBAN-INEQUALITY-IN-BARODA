# Methodology

This chapter describes the analytical approach adopted to model urban
inequality in Vadodara. The methodology is designed to ensure transparency,
replicability, and alignment with established practices in spatial analysis.

The process moves from spatial data construction to statistical validation,
with each step informed by the theoretical framework discussed earlier.

---

## Study Area and Spatial Units

The study focuses on Vadodara city, divided into 19 administrative wards.
These wards serve as the primary spatial units of analysis.

Ward boundaries were digitized to reflect current administrative realities,
addressing the lack of updated post-2011 census spatial data.

<div class="note">
Using wards ensures policy relevance while maintaining analytical clarity.
</div>

---

## Data Preparation

Spatial data for roads and service locations were obtained from
OpenStreetMap. The road network was cleaned and processed to ensure
topological consistency.

Key services considered include:
- healthcare facilities,
- educational institutions,
- public transport access points.

---

## Network-Based Accessibility Analysis

The city was modeled as a road network where:
- nodes represent intersections,
- edges represent road segments,
- edge weights approximate travel time.

Shortest-path algorithms were used to estimate accessibility from each ward
to essential services.

<div class="callout">
This approach captures how residents actually navigate the city, rather than
how close services appear on a map.
</div>

---

## Construction of the Urban Opportunity Index

Multiple accessibility indicators were standardized and combined using
Principal Component Analysis (PCA).

The first principal component was retained as the Urban Opportunity Index,
representing the dominant dimension of access across wards.

---

## Spatial Statistical Validation

To assess whether observed inequalities were random or structured, spatial
autocorrelation was examined using:
- Global Moran’s I
- Local Indicators of Spatial Association (LISA)

These tools enabled identification of spatial clusters and localized
patterns of advantage and deprivation.
