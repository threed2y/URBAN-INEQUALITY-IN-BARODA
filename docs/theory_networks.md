Network-Based Accessibility: The Friction of Distance

Access to urban services is not merely a function of proximity; it is defined by the structure of the networks that facilitate movement.

In this study, Accessibility is conceptualized not as a geometric property (how close is X?), but as a functional property (how long does it take to reach X?). This approach acknowledges that the urban fabric—composed of winding streets, traffic bottlenecks, and physical barriers—imposes a "friction of distance" that shapes daily life.

    Core Premise: Opportunity is constrained by the road network. A hospital 500 meters away is inaccessible if it sits across a river with no bridge.

1. The Euclidean Fallacy

Traditional spatial analysis often relies on Euclidean (straight-line) distance, which assumes a frictionless, barrier-free plane. In complex urban environments like Vadodara, this approach fails to capture reality:

    Tortuosity: Roads rarely follow straight lines; they wind around existing settlements.

    Barriers: The Vishwamitri River and the Railway Line act as "hard cuts" in the city's fabric, severing connectivity between geographically close neighborhoods.

    Hierarchy: A highway allows for speed, while a neighborhood lane restricts it. Euclidean measures treat all space as equal.

2. Cities as Graphs (Methodology)

To model this reality, this study represents the city as a Primal Planar Graph (G={N,E}), where:

    Nodes (N): Represent intersections and dead-ends.

    Edges (E): Represent street segments, weighted by their length, speed limit, and tortuosity.

By applying Dijkstra’s Shortest Path Algorithm to this graph, we calculate the true cost of travel (in minutes) rather than the theoretical distance. This transforms the map from a representation of space into a representation of time.

3. Academic Foundations

This network-centric approach is grounded in the evolution of transport geography:

    Hansen (1959): First defined accessibility as the "potential of opportunities for interaction," shifting the focus from transport infrastructure to human utility.

    Porta et al. (2006): Demonstrated how "Multiple Centrality Assessment" (MCA) on street networks correlates with economic activity and service density.

    Boeing (2017): Revolutionized modern urban analytics with OSMnx, proving that topological indicators (like intersection density) are better predictors of walkability than simple density metrics.

Relevance to This Study

For Vadodara, a network-based approach is critical. The "Access Map" generated in this project reveals that while the Euclidean Buffer of a hospital might cover 80% of a ward, the Network Isochrone (10-minute drive zone) often covers less than 50% due to the city's limited bridge crossings and winding periphery roads.
