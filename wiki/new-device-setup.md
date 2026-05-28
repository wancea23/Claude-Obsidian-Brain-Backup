# New Device Setup

How to bring a fresh machine to the same Claude Code + vault + memory state as the primary one.

Everything that should be shared lives in OneDrive. Everything ephemeral (plugins, cache, sessions) stays local per machine.

---

## Prerequisites

Install on the new machine:

1. **OneDrive**, signed in with the same account that holds `OneDrive - Technical University of Moldova/`. Let it finish syncing the full `.claude-sync/` and `Code/` folders before continuing.
2. **Claude Code** — https://docs.claude.com/claude-code
3. **Python 3.13+** — required by the vault hooks (`vault_pre_edit.py`, `vault_sync.py`, `vault_session_end.py`).
4. **Node.js** — for any npm-based tooling.
5. **graphify CLI** — required for `graphify update .` to refresh `graph.json` after edits. Install with whatever method was used originally (likely `npm i -g graphify-cli` or `pipx install graphify`). Verify with `graphify --version`.
6. **jq** — optional, no longer required by hooks but useful elsewhere. `choco install jq` or via MSYS2.

Right-click the OneDrive `.claude-sync/` folder in Explorer → **Always keep on this device**. Do the same for `Code/` if you want projects offline-available.

---

## What lives where

| Location | Synced via OneDrive? | What it is |
|---|---|---|
| `OneDrive\.claude-sync\CLAUDE.md` | yes | global instructions |
| `OneDrive\.claude-sync\settings.json` | yes | global Claude Code settings |
| `OneDrive\.claude-sync\skills\` | yes | custom skills (graphify, vault-update, emil-design-eng) |
| `OneDrive\.claude-sync\plans\` | yes | plan-mode plan files |
| `OneDrive\.claude-sync\projects\<slug>\memory\` | yes | per-project auto-memory |
| `OneDrive\...\Code\` | yes | all code + each project's `.claude\settings.json` + `graphify-out\` vault |
| `~\.claude\plugins\` | no | installed plugins — reinstall per machine |
| `~\.claude\cache\`, `sessions\`, `file-history\`, `history.jsonl` | no | runtime state |

---

## Setup script (run once per new machine)

With Claude Code **closed**:

```
"C:\Users\SURFACE\OneDrive - Technical University of Moldova\.claude-sync\setup-machine.bat"
```

This creates 5 links in `%USERPROFILE%\.claude\`:

- `CLAUDE.md` → hardlink → OneDrive
- `settings.json` → hardlink → OneDrive
- `skills\` → junction → OneDrive
- `plans\` → junction → OneDrive
- `projects\` → junction → OneDrive (so **every** project's memory is shared, not just one)

If the machine already has content in those spots, the script renames it to `*.premerge` so nothing is lost — review those folders afterwards and delete once you've confirmed nothing useful got shadowed.

After the script completes, open Claude Code. Memory, skills, plans, and global instructions are all shared with the primary machine.

---

## Path-slug gotcha

Claude's per-project memory folder is named after the project's absolute path:

```
C--Users-SURFACE-OneDrive---Technical-University-of-Moldova-Code
```

For auto-memory to resolve to the same folder on both machines, **both machines need**:

- Same Windows username (`SURFACE`)
- Same OneDrive folder name (`OneDrive - Technical University of Moldova`)

If either differs, edit `setup-machine.bat` and adjust the `C` and `SYNC` variables before running. The slug itself will re-derive from the actual path on the new machine — the existing memory won't be picked up unless the slug matches.

---

## Project-level hooks (vault)

The `graphify-out/` vault and its hooks live inside `OneDrive\...\Code\`, so they travel automatically. The project `.claude\settings.json` in the repo configures:

- **PreToolUse(Edit|Write)** → `vault_pre_edit.py` → appends old content to `graphify-out/wiki/file-history.md`
- **PostToolUse(Edit|Write)** → `graphify update .` (refreshes `graph.json`) + `vault_sync.py` (queues pending wiki updates)
- **Stop** → `vault_session_end.py` generates a chat-history template

These all just work on the new machine as long as Python and graphify are installed.

---

## Rules of the road

- **Never run Claude Code on both machines at the same time.** OneDrive will produce `MEMORY-MachineA.md` conflict copies. Close on one before opening on the other.
- **Plugins don't sync.** Install them again on each machine via `/plugins` or however you originally added them.
- **Files On-Demand lag.** If Claude ever errors on a cold file, make sure the folder is pinned with "Always keep on this device".
- **Session logs accumulate** under `~\.claude\projects\<slug>\*.jsonl` per machine. They now sync via OneDrive (since `projects\` is a junction). This is fine, but means both machines contribute to the same project's transcript store.
- **Secrets.** `settings.json` is shared. Don't put machine-specific secrets there — use `.claude\settings.local.json` (local-only, not symlinked) for anything that shouldn't leave a given machine.

---

## Rollback

If you ever want to decouple a machine:

```
cd %USERPROFILE%\.claude
rmdir skills plans projects
del CLAUDE.md settings.json
```

(These commands only remove the links/hardlinks — the actual data stays safe in OneDrive.) Then copy the OneDrive contents back into `~\.claude\` as real files if you want to keep using them locally.

---

## Related

- [[index|Vault Index]]
- [[pending-updates|Pending Updates]]
- Setup scripts: `OneDrive\.claude-sync\setup-machine.bat`, `finish-sync.bat`
