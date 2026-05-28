"""
vault_session_end.py — Generate chat history template + session summary at session end.

Called by Stop hook. Reads .vault_cache.json to find which project files were modified
this session, then:
  1. Writes a fillable template to each touched project's chat-history file
  2. Adds a FILL CHAT HISTORY pending entry to pending-updates.md
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

CODE_ROOT    = Path("C:/Users/johns/OneDrive - Technical University of Moldova/Code")
VAULT        = CODE_ROOT / "graphify-out" / "wiki"
CHAT_HISTORY = VAULT / "chat-history"
PENDING      = VAULT / "pending-updates.md"
MTIME_CACHE  = CODE_ROOT / "graphify-out" / ".vault_cache.json"

# Map project folder name → wiki/chat-history stem
PROJECT_MAP = {
    "999 AutoPost":  "999-AutoPost",
    "ASP Scrapper":  "ASP-Scrapper",
    "Site":          "Site",
    "m99gadgets":    "m99gadgets",
    "Python":        "Python",
    "C":             "C-Labs",
    "Java":          "Java-OOP",
    "POO Labs":      "POO-Labs",
    "POO LAB2":      "POO-Labs",
    "AA Labs":       "AA-Labs",
    "Tournament":    "Tournament",
    "Roblox":        "Roblox",
}

SKIP_DIRS = {"graphify-out", "__pycache__", "node_modules", "venv", "data", "images",
             "dist", "build", ".git"}


def load_cache() -> dict:
    if MTIME_CACHE.exists():
        try:
            return json.loads(MTIME_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def get_touched_projects(cache: dict) -> dict[str, list[str]]:
    """Return {project_stem: [relative_file_paths]} for files modified this session."""
    touched: dict[str, list[str]] = {}
    now = datetime.now().timestamp()

    for file_str, cached_mtime in cache.items():
        path = Path(file_str)
        if not path.exists():
            continue
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        try:
            current_mtime = path.stat().st_mtime
        except OSError:
            continue
        # Modified in last 8 hours (session window)
        if current_mtime > cached_mtime + 2 and (now - current_mtime) < 28800:
            # Identify which project this belongs to
            for folder_name, stem in PROJECT_MAP.items():
                project_folder = CODE_ROOT / folder_name
                try:
                    path.relative_to(project_folder)
                    rel = str(path.relative_to(project_folder))
                    if stem not in touched:
                        touched[stem] = []
                    if rel not in touched[stem]:
                        touched[stem].append(rel)
                    break
                except ValueError:
                    continue
    return touched


def write_template(stem: str, changed_files: list[str]):
    """Write a fillable session template to the project's chat-history file."""
    chat_file = CHAT_HISTORY / f"{stem}-chats.md"
    if not chat_file.exists():
        return

    ts   = datetime.now().strftime("%Y-%m-%d")
    files_list = "\n".join(f"- `{f}`" for f in sorted(changed_files))

    template = (
        f"\n---\n\n"
        f"### [{ts}] — SESSION *(fill in title)*\n\n"
        f"**What was asked**: *(fill in)*\n\n"
        f"**What was done**: *(fill in)*\n\n"
        f"**Files changed**:\n{files_list}\n\n"
        f"**Key decisions**: *(fill in — or 'none')*\n\n"
        f"**Mistakes made**: *(fill in — or 'none')*\n\n"
        f"**Outcome**: *(fill in)*\n"
    )

    current = chat_file.read_text(encoding="utf-8")
    # Don't add duplicate template for same date
    if f"### [{ts}]" in current and "fill in title" in current:
        return

    chat_file.write_text(current + template, encoding="utf-8")


def add_pending_entry(projects: list[str]):
    """Add FILL CHAT HISTORY pending entry to pending-updates.md."""
    if not projects:
        return

    ts        = datetime.now().strftime("%Y-%m-%d %H:%M")
    proj_list = ", ".join(projects)
    entry = (
        f"\n### [{ts}] SESSION END\n"
        f"**Change type**: FILL CHAT HISTORY\n"
        f"**Detail**: Session ended. Fill in chat history templates for: {proj_list}\n"
        f"**Status**: pending\n"
    )

    if not PENDING.exists():
        PENDING.write_text("# Pending Wiki Updates\n\n> Items queued for AI review.\n",
                           encoding="utf-8")

    current = PENDING.read_text(encoding="utf-8")
    # Dedup: only add if no FILL CHAT HISTORY entry is already pending
    pending_section = current.split("**Status**: pending")[0] if "**Status**: pending" in current else current
    if "FILL CHAT HISTORY" not in pending_section.split("### [")[-1]:
        PENDING.write_text(current + entry, encoding="utf-8")


def main():
    cache   = load_cache()
    touched = get_touched_projects(cache)

    if not touched:
        return

    written = []
    for stem, files in touched.items():
        write_template(stem, files)
        written.append(stem)

    if written:
        add_pending_entry(written)
        print(f"vault_session_end: templates written for {', '.join(written)}")


if __name__ == "__main__":
    main()
