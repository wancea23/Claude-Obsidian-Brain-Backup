# car-traffic-simulation — Chat History

> Log of important Claude Code sessions for this project.

---

## Sessions

### [2026-04-20] Initial vault entry + NETEDIT editor + never-despawn fix

**What was asked**:
1. Add car-traffic-simulation to the graphify vault.
2. Add a UI to add/edit/delete roads.
3. Fix cars that reach a place, get blocked, and disappear from the map.

**What was done**:
- Created vault files: `projects/car-traffic-simulation.md`, `decisions/…-decisions.md`, `todo/…-todo.md`, `chat-history/…-chats.md`; added the project to `index.md` and `projects.md`.
- **Road editor** = SUMO's bundled **NETEDIT** (no custom UI). Added `scripts/edit_network.py`, `scripts/regenerate_routes.py`, a `--edit` flag on `main.py`, and a README section. `prepare_map.generate_routes()` gained a `force=True` param so edits to the net can trigger a clean route rebuild.
- **Never-despawn fix**:
  - New `traffic.persistence` config block (`never_despawn`, `disable_teleport`, `blocked_reroute.{enabled,speed_threshold,patience_steps}`).
  - New `src/simulation/persistence.py` — `VehiclePersistenceController`: loops `v_*` arrivals via `spawner.respawn_like()`, calls `traci.vehicle.rerouteTraveltime()` on stuck vehicles after `patience_steps`.
  - `VehicleSpawner` now validates reachability with `sumolib.getShortestPath()` before `traci.route.add` (root cause of silent "car vanishes" events with `--ignore-route-errors true`).
  - `runner.py` reads teleport value from config (`-1` when `disable_teleport: true`) and wires the persistence controller into `_on_step`.
- Added 4 unit tests in `tests/unit/test_persistence.py` (arrival respawn, stuck reroute after patience, moving car not rerouted, static XML vehicles ignored).

**Key decisions** (see `decisions/car-traffic-simulation-decisions.md`):
- NETEDIT over custom UI — ships with SUMO, full-featured.
- Cars loop on arrival + reroute when stuck + teleport disabled — matches "cars should not disappear from the map".
- Reachability pre-check via sumolib instead of relying on `--ignore-route-errors`.

**Files changed**:
- Created: `src/simulation/persistence.py`, `scripts/edit_network.py`, `scripts/regenerate_routes.py`, `tests/unit/test_persistence.py`, three vault files.
- Modified: `main.py` (`--edit` flag), `src/simulation/runner.py`, `src/agents/spawner.py`, `scripts/prepare_map.py` (`force` param + User-Agent header), `config/simulation.yaml` (persistence block + shrunk bbox to ~5×5 km).
- Vault index/catalog: `graphify-out/wiki/index.md`, `projects.md`.

**Setup notes (captured during run-through)**:
- Project must be run from `car-traffic-simulation/urban-traffic-sim/`, not the parent. `main.py` lives in the subfolder.
- Needs SUMO installed + `SUMO_HOME` env var + `%SUMO_HOME%\bin` on PATH. The user's install: `C:\Program Files (x86)\Eclipse\Sumo` (SUMO 1.26.0).
- Requires a venv (`python -m venv venv` then `.\venv\Scripts\Activate.ps1`) with `pip install -r requirements.txt`.
- First-time run: `python scripts\prepare_map.py` downloads OSM + runs netconvert + generates routes.

**Outcome**:
- Code compiles (`py_compile` clean on all modified/new files).
- Tests not executed here (no global pytest; runs inside venv).
- **Open issue at end of session**: Overpass `/api/map` returned HTTP 406 on the original 0.16°×0.12° bbox. Mitigations applied:
  1. Shrunk bbox to ~5×5 km city-centre.
  2. Added `User-Agent` header + longer timeout in `download_osm()`.
  - Next step if it still fails: fall back to `osmnx` (already in requirements) or use a narrower bbox / manual OSM export.

**Follow-up (resolved during same session)**:
- Overpass download: fixed by shrinking bbox to ~5×5 km city centre + `User-Agent` header.
- SUMO install verified (`C:\Program Files (x86)\Eclipse\Sumo`, 1.26.0) — env vars set via `[Environment]::SetEnvironmentVariable(…, "User")`.
- User confirmed sim runs; headless-by-default caught (`--gui` flag required; SUMO-GUI opens paused — must click ▶).
- Added full **Windows PowerShell walkthrough** and **NETEDIT road-editing walkthrough** to `urban-traffic-sim/README.md` (install → env vars → venv → `prepare_map.py` → `main.py --gui`; then NETEDIT modes E/N/C/T/I/D/M, add/edit/delete flow, F5 Recompute, Ctrl+S, `regenerate_routes.py`, common pitfalls).

**Status**: Ready to commit. Suggested message:
```
car-traffic-simulation: NETEDIT road editor + never-despawn vehicles
```

**Next session**:
- Run `graphify update .` from `Code/` root to refresh the knowledge graph with the new files.
- If user reports cars still disappearing after a long run, check teleport count in `data/output/statistics.csv` — `disable_teleport: true` should keep it zero.

---

[[../projects/car-traffic-simulation|Back to project]] · [[../index|Vault Index]]
