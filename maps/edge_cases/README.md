# Custom Imaginative Edge-Case Maps

A suite of 26 standalone custom map files (`.txt`) designed from first principles to test extreme topological scenarios, physical constraints, queue dynamics, and algorithmic edge cases beyond the standard project maps.

---

## Map Catalog

| Map File | Drones | Turns | Key Edge Case Tested |
| :--- | :---: | :---: | :--- |
| `01_restricted_funnel_hazard.txt` | 6 | 8 | Burst connection capacity (`max_link_capacity=4`) feeding a single-drone restricted zone (`max_drones=1`). Verifies destination reservation. |
| `02_chained_restricted_corridor.txt` | 4 | 13 | Sequential pipeline of 3 consecutive restricted zones (`r1 -> r2 -> r3`). Tests continuous 2-turn caterpillar leapfrogging. |
| `03_triple_convergence_bottleneck.txt` | 6 | 14 | Three feeder corridors (North, Center, South) simultaneously converging into a single restricted bottleneck hub. |
| `04_priority_express_vs_bulk_freeway.txt` | 8 | 6 | Dijkstra cost weighing: narrow priority express lane (cost 5, cap 1) vs 3-lane bulk freeway (cost 10, cap 3). |
| `05_accordion_capacity_shock.txt` | 7 | 11 | Alternating extreme capacity expansion and contraction: Plaza (cap 5) -> Needle 1 (cap 1) -> Reservoir (cap 4) -> Needle 2 (cap 1). |
| `06_star_crossroads_junction.txt` | 8 | 11 | 2-in, 2-out crossroads through a central restricted roundabout (`max_drones=2`). Multi-ingress and multi-egress coordination. |
| `07_single_drone_tactical_puzzle.txt` | 1 | 3 | Single drone navigating a graph with `zone=blocked` hazard avoidance and priority lane selection. |
| `08_high_concurrency_dual_freeway.txt` | 24 | 9 | High concurrency stress test: 24 drones streaming across twin parallel highways with sustained concurrent waves. |
| `09_zigzag_dead_end_maze.txt` | 4 | 6 | Pathfinder immunity to deceptive branches and high-capacity dead ends leading to cul-de-sacs. |
| `10_diamond_mesh_weave.txt` | 6 | 6 | Braided double-diamond mesh network with alternating priority and normal zones and diagonal interconnects. |
| `11_restricted_island_hop.txt` | 5 | 16 | Heterogeneous zone-type transitions across an alternating chain: `normal -> restricted -> priority -> restricted -> normal`. |
| `12_mega_swarm_tritrack.txt` | 30 | 8 | 30-drone massive fleet flood across 3 parallel multi-lane tracks with heavy concurrency. |
| `13_pulsing_chokepoint_resistor.txt` | 8 | 4 | Wheatstone bridge lattice with diagonal cross-links and concurrent multi-path load distribution. |
| `14_priority_switchback_detour.txt` | 6 | 7 | Dijkstra cost parity load balancing: 2-hop normal path vs 4-hop priority switchback detour. |
| `15_hourglass_funnel_surge.txt` | 6 | 15 | 3-inflow funnel narrowing into a single-capacity restricted waist then expanding into 3 exit lanes. |
| `16_dead_end_decoy_galaxy.txt` | 4 | 5 | Pathfinder immunity to 4 enticing high-capacity priority/normal dead ends surrounding the true path. |
| `17_fifty_drone_tsunami.txt` | 50 | 6 | Massive 50-drone high-throughput stress test across 4 high-concurrency corridors. |
| `18_nested_restricted_loops.txt` | 6 | 4 | Concentric rings with inner restricted bypass and outer normal routes testing multi-route coordination. |
| `19_reverse_funnel_expansion.txt` | 10 | 13 | Inverted funnel: initial 1-drone needle chokepoint bursting into 4 diverse parallel fan-out channels. |
| `20_bidirectional_corridor_squeeze.txt` | 12 | 6 | Twin parallel highways with high zone capacities linked by capacity-1 diagonal cross-over squeeze links. |
| `21_restricted_tollbooth_cluster.txt` | 9 | 10 | 3 parallel restricted tollbooths feeding a shared holding plaza, emptying into dual priority exit gates. |
| `22_asymmetric_bipartite_mesh.txt` | 12 | 8 | Fully connected bipartite mesh with heterogeneous zone-type pairings across 9 distinct cross-edges. |
| `23_cascading_priority_waterfall.txt` | 12 | 11 | 3-tier cascade where saturated priority lanes dynamically spill overflow drones into normal bypasses. |
| `24_labyrinth_of_knossos.txt` | 6 | 13 | Complex maze with blocked barriers, priority traps, haven dead ends, and a serpentine restricted route. |
| `25_massive_link_choke_high_zone_cap.txt` | 8 | 11 | Binding link capacity test: large 10-drone chambers connected by strictly throttled capacity-1 links. |
| `26_single_drone_marathon.txt` | 1 | 14 | Single drone 10-hop marathon traversing alternating zone types flanked by blocked obstacles and decoys. |


---

## How to Run

To run individual maps:
```bash
python3 main.py maps/edge_cases/01_restricted_funnel_hazard.txt
python3 main.py maps/edge_cases/02_chained_restricted_corridor.txt
python3 main.py maps/edge_cases/08_high_concurrency_dual_freeway.txt
python3 main.py maps/edge_cases/12_mega_swarm_tritrack.txt
```

To run the automated verification suite:
```bash
python3 test_custom_edge_cases.py
# or via Makefile
make test
```
