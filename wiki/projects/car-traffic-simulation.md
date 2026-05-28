# Car Traffic Simulation — SUMO Chișinău

> Semestrial Multimedia Technology project
> **Last synced**: 2026-04-20

**Path**: `Code/car-traffic-simulation/urban-traffic-sim/`
**Stack**: Python 3, SUMO 1.26+, TraCI, sumolib, PyYAML, matplotlib, pandas, numpy, pytest
**Context**: TUM — Multimedia Technology. Microscopic urban traffic sim for Chișinău using real OSM data.

---

## Structure

```
car-traffic-simulation/
  src/main.py                      # stub (unused)
  urban-traffic-sim/               # ACTIVE project
    main.py                        # CLI entry: --gui, --steps, --debug, --edit
    config/simulation.yaml         # sim + traffic + persistence config
    maps/                          # generated (git-ignored): .net.xml, .rou.xml, .poly.xml
    scripts/
      prepare_map.py               # OSM -> netconvert -> randomTrips pipeline
      edit_network.py              # launches NETEDIT on the active net
      regenerate_routes.py         # re-runs randomTrips only (after editing the net)
    src/
      agents/vehicle.py            # VehicleAgent — TraCI wrapper
      agents/spawner.py            # VehicleSpawner — runtime injection + reachability check
      network/road_network.py      # sumolib wrapper
      simulation/runner.py         # orchestrator — TraCI lifecycle
      simulation/persistence.py    # never-despawn: loop + reroute blocked vehicles
      simulation/statistics.py     # per-step KPI collector
      simulation/vehicle_type_loader.py
      traffic_control/traffic_light.py
      traffic_control/adaptive_controller.py
      visualization/stats_plotter.py
      utils/config.py, utils/logger.py
    tests/unit/, tests/integration/
```

---

## What It Does

- Downloads Chișinău OSM data via Overpass API, converts to SUMO `.net.xml` with `netconvert`.
- Runs a microscopic traffic simulation via TraCI (headless `sumo` or visual `sumo-gui`).
- Spawns car/bus/truck vehicles at runtime with random reachable source/destination pairs.
- Adaptive traffic lights extend green phases under congestion.
- Persistence controller: vehicles never despawn — they reroute around blockages and loop onto a new random destination when they arrive.
- Collects per-step KPIs (speed, wait time, CO₂, fuel, teleports) → CSV + matplotlib dashboard.

---

## How to Run

```bash
cd urban-traffic-sim
python scripts/prepare_map.py     # one-time: download OSM + netconvert
python main.py --gui              # SUMO-GUI visual mode
python main.py --steps 500        # quick headless test
python main.py --edit             # open NETEDIT to edit roads
pytest tests/                     # run tests
```

Requires `SUMO_HOME` env var pointing at the SUMO install (so `netedit`, `netconvert`, `randomTrips.py` resolve).

---

## Editing the Road Network

1. `python main.py --edit` — opens NETEDIT on `maps/chisinau.net.xml`.
2. Add/delete/reshape edges, junctions, lanes, connections, traffic lights. Ctrl+S to save.
3. `python scripts/regenerate_routes.py` — rebuilds `maps/chisinau.rou.xml` against the new network (old routes may reference deleted edges).
4. `python main.py --gui` — run with the edited network.

---

## Notes & Gotchas

- **`maps/` is git-ignored** — the `.net.xml` is generated, never committed. Run `prepare_map.py` after clone.
- **`--time-to-teleport` is driven by config** (`traffic.persistence.disable_teleport: true` → `-1`). Turn off to see stuck-car metrics instead of silent teleportation.
- **`--ignore-route-errors true`** is a safety net; connectivity is validated pre-spawn via `sumolib.getShortestPath()`. Route errors should be rare.
- **Fallback route file** `urban-traffic-sim/routes.rou.xml` (top-level, 559 KB) duplicates `maps/chisinau.rou.xml` — prefer the latter.
- Vehicle IDs: XML-predefined routes use integer IDs; runtime spawns use `v_<counter>`. The persistence controller only loops the `v_` ones.

---

## Backup Log

See [[../chat-history/car-traffic-simulation-chats|Chat History]] · [[../backups/car-traffic-simulation-backup|Backup History]]
