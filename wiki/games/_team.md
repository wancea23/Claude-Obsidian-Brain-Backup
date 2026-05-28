# Gamedev Team — Reference

> Navigable summary of the 10-agent team. The **canonical** files live at
> `Code/Games/.claude/agents/gamedev/*.md` (Claude Code loads them from there).
> This page mirrors *what each agent does* so you can browse the team in
> Obsidian without leaving the vault.
>
> If a role description here drifts from the source file, the source file wins.
> Edits should always be made in `Code/Games/.claude/agents/gamedev/<name>.md`.

## Shared protocol files

- **`Code/Games/CLAUDE.md`** — workspace config, auto-loaded for any session
  under `Code/Games/`. Contains: Godot 4.3 engine declaration, 3.x→4.x
  GDScript syntax cheat sheet, project layout convention, smoke-test
  commands, hard rules.
- **`Code/Games/.claude/agents/gamedev/VAULT.md`** — vault protocol every
  agent reads first. Vault root, layout, ownership table (who writes where),
  storyline-graph rules, end-of-cycle cross-check list.

## The 10 agents

| # | Agent | One-liner | Owns / writes |
|---|---|---|---|
| 1 | **director** | Orchestrator. Reads tasks.md, spawns one specialist per cycle via Task tool, resolves conflicts. The only agent the user invokes. | overview.md, todo.md, conflict resolution log |
| 2 | **architect** | Runs ONCE per game. Scaffolds the Godot 4 project: project.godot, globals/Constants.gd autoload, scenes/Main.tscn, content JSON skeletons. | project skeleton, Constants.gd |
| 3 | **game-designer** | Owns mechanics + design log. Writes GDD.md, mechanics/*.md, decisions.md. Maintains storyline-graph.md structure (branches, locks, ending reachability). | GDD.md, mechanics/, decisions.md, storyline-graph (structure) |
| 4 | **artist** | Generates pixel-art sprites via SD 1.5 + pixel-art LoRA. Reads asset_requests.json, runs gamedev-tools/artist_agent.py, postprocesses. | assets/sprites/, asset_requests.json status |
| 5 | **coder** | Implements ONE game system per session in GDScript. TileMap for grid, CanvasGroup for shaders, signals for cross-system comm. | scenes/<domain>/, scripts inside, tests/run_*.gd harnesses |
| 6 | **narrative-writer** | Writes every word the player reads. Owns content/*.json AND the narrative leaves of the storyline graph. | content/*.json, narrative/{events,characters,endings,whispers} |
| 7 | **audio-engineer** | Generates ambient music + SFX via AudioCraft (MusicGen→AudioGen with VRAM unload between). Reads audio_requests.json. | assets/audio/, audio_manifest.json |
| 8 | **ui-agent** | Builds menus, HUD, pause, dialogue as Godot Control-node scenes under scenes/ui/. Reads game state via signals only. | scenes/ui/ + theme.tres |
| 9 | **tester** | Runs godot --headless smoke + windowed pyautogui flows. Screenshots, palette violations check, ending-reachability tests. | bugs.md, test_logs/ |
| 10 | **reviewer** | Cross-checks vault↔code consistency. Flags `[STYLE]`, `[GD3]` (3.x syntax in 4.x project), `[MAGIC]`, `[MISSING]`, `[BOUNDARY]`, `[CRASH]`, `[VAULT]`. Never edits, only reports. | review.md (append) |

## How they communicate

**They don't talk directly.** Subagents in Claude Code can't call each other —
only Director can spawn them via the Task tool. All cross-agent communication
is **file-mediated**:

- `asset_requests.json` ← Coder/UI append, Artist consumes
- `audio_requests.json` ← Coder/Director append, Audio Engineer consumes
- `content/*.json` ← Narrative Writer writes, Coder + UI Agent read
- `<vault>/mechanics/*.md` ← Game Designer writes, Coder reads
- `<vault>/narrative/storyline-graph.md` ← Designer (structure) + Writer (leaves)
- `<vault>/chat-history.md` ← every agent appends after a task
- `review.md` ← every agent appends one line per task; Reviewer audits
- `bugs.md` ← any agent that hits an error logs here

The diagram lines aren't conversations — they're data flow through these files.
This is intentional: every "conversation" leaves a written trace, the workflow
is auditable and resumable across sessions.

## How to start a new game

1. Create `Code/Games/<NewGame>/` with its own `STYLE.md`, `tasks.md`,
   `audio_requests.json`, `asset_requests.json`, `review.md`, `bugs.md`,
   `.gitignore`.
2. Create `graphify-out/wiki/games/<NewGame>/` with its own `overview.md`,
   `decisions.md`, `chat-history.md`, `todo.md`, and the `narrative/`
   subfolder structure.
3. Add a row to [[index]] under Projects / Decisions / Todo / Chat History.
4. Create a `projects/<NewGame>.md` global index entry pointing at the
   per-game vault.
5. From inside the game folder: `claude --dangerously-skip-permissions`.
   Tell director: *"Run Phase 0 — spawn architect first."*

The same 10 agents and ML tools work as-is.
