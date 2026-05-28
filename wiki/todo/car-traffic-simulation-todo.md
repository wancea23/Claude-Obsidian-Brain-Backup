# Car Traffic Simulation — Todo & Known Issues

---

## High Priority
- Verify the NETEDIT → regenerate_routes → run round-trip on a clone without `maps/` pre-populated.

## Improvements
- Add a `trip_count` per vehicle in `statistics.py` now that vehicles loop indefinitely — current arrival count is meaningless.
- Route variety: `_spawn_batch` currently uses uniform vtype weights; consider OD-matrix or time-of-day weighting.
- Add NETEDIT keyboard shortcut hint to the in-app log when `--edit` is used.
- Expose `persistence.blocked_reroute.patience_steps` as a CLI override for quick tuning.

## Known Issues
- `urban-traffic-sim/routes.rou.xml` (559 KB) duplicates `maps/chisinau.rou.xml` — delete the stale one or wire the config to the right file.
- `VehicleAgent.reroute()` used to be unused; now called from persistence controller. Keep both in sync if signature changes.

## Completed ✓
- 2026-04-20: Add graphify vault entries.
- 2026-04-20: Add NETEDIT launcher (`--edit`) and `regenerate_routes.py`.
- 2026-04-20: Implement never-despawn persistence controller (loop + reroute + reachability check).

[[../projects/car-traffic-simulation|← Back to project wiki]]
