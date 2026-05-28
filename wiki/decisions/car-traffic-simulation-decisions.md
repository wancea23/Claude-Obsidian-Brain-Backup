# Car Traffic Simulation — Design Decisions

> WHY things were built the way they are. Add entries as decisions are made.

---

## 2026-04-20 — Road editor: NETEDIT over custom UI

**Decision**: Use SUMO's bundled NETEDIT as the road editor; no custom PyQt/Tkinter/web GUI.

**Why**: NETEDIT ships with SUMO, natively edits `.net.xml`, and supports edges, junctions, lanes, connections, and traffic lights. A custom editor would take days and still be a worse tool. We only add a launcher script and a route-regeneration script around it.

**Trade-off**: User has to install SUMO (already required). UX is not embedded in our Python app — they alt-tab to NETEDIT.

---

## 2026-04-20 — Cars never despawn: reroute + loop

**Decision**: Vehicles do not disappear from the map. On arrival they are re-injected with a new random destination. Stuck vehicles (low speed beyond patience) trigger `traci.vehicle.rerouteTraveltime()`. Teleport is disabled by default (`--time-to-teleport -1`).

**Why**: The user reports "cars go to a certain place, get blocked and disappear". Root causes were: SUMO's default removal on arrival, teleport-on-stuck, and silent route-build failures for unreachable src/dst pairs (hidden by `--ignore-route-errors true`). Validating reachability pre-spawn + looping arrivals + rerouting blocked cars keeps the population visible and behaviorally realistic.

**Trade-off**: Statistics like "arrived vehicle count" are no longer meaningful — the population is effectively infinite. If we need throughput metrics later, add a per-vehicle "trip count" to stats.

---

## 2026-04-20 — Route validation via sumolib, not try/except

**Decision**: `VehicleSpawner` calls `sumolib.net.getShortestPath(src, dst)` before `traci.route.add` and resamples up to N times if unreachable.

**Why**: `--ignore-route-errors true` was previously masking the failure mode — vehicles would be created with bad routes and immediately vanish. Explicit pre-check is cheaper than TraCI round-trips and gives us a clear log message.

---

[[../projects/car-traffic-simulation|← Back to project wiki]] · [[../decisions|← Global Decisions]]
