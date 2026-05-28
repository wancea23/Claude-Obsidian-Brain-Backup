"""
vault_sync.py — Auto-updates wiki/projects/*.md when project files change.

Runs via PostToolUse hook after every Edit/Write, and via git post-commit.
Does NOT require LLM. Purely structural: detects new files, stack changes,
updates tables, timestamps, and queues AI-review items.

Usage:
  python vault_sync.py                    # full sync
  python vault_sync.py --project Site     # sync one project
  python vault_sync.py --check            # only report what needs updating
"""

import json, os, re, sys, hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Config ────────────────────────────────────────────────────────────────────
CODE_ROOT  = Path("C:/Users/johns/OneDrive - Technical University of Moldova/Code")
VAULT      = CODE_ROOT / "graphify-out" / "wiki"
PROJECTS   = VAULT / "projects"
PENDING    = VAULT / "pending-updates.md"
GRAPH      = CODE_ROOT / "graphify-out" / "graph.json"
MTIME_CACHE = CODE_ROOT / "graphify-out" / ".vault_cache.json"

# Source file extensions worth tracking for content changes
TRACK_EXTS = {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".lua", ".luau", ".bat", ".sh"}
# Paths to skip when tracking mtimes
SKIP_DIRS  = {"__pycache__", ".git", "node_modules", "venv", "build", "dist",
              "graphify-out", ".claude", "data", "images", "hof", "showcase"}

# Map folder name → wiki file stem
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

# File extensions → stack language
EXT_LANG = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".html": "HTML", ".css": "CSS", ".java": "Java", ".c": "C",
    ".cpp": "C++", ".lua": "Lua", ".luau": "Luau", ".json": "JSON",
    ".md": "Markdown", ".sh": "Shell", ".bat": "Batch",
}

# Files/patterns that signal a significant change worth flagging
SIGNIFICANT_PATTERNS = [
    r"requirements\.txt$", r"package\.json$", r"\.spec$",
    r"BUILD\.", r"Makefile", r"README", r"CHANGELOG",
    r"main\.(py|js|java|c)$", r"app\.(py|js)$",
]

def get_stack(folder: Path) -> list[str]:
    """Detect languages used in a project folder."""
    counts = defaultdict(int)
    for f in folder.rglob("*"):
        if f.is_file() and not any(p in str(f) for p in ["__pycache__", ".git", "node_modules", "venv", "build", "dist", ".spec"]):
            lang = EXT_LANG.get(f.suffix.lower())
            if lang:
                counts[lang] += 1
    return [lang for lang, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]]

def get_file_list(folder: Path, max_depth: int = 1) -> list[Path]:
    """Get immediate files + one level deep."""
    files = []
    try:
        for f in sorted(folder.iterdir()):
            if f.name.startswith(".") or f.name in ["__pycache__", "node_modules", "venv", "build", "dist"]:
                continue
            files.append(f)
    except PermissionError:
        pass
    return files

def folder_hash(folder: Path) -> str:
    """Hash of folder structure to detect changes."""
    items = []
    for f in sorted(folder.rglob("*")):
        if f.is_file() and not any(p in str(f) for p in ["__pycache__", ".git", "venv"]):
            items.append(f"{f.relative_to(folder)}:{f.stat().st_mtime:.0f}")
    return hashlib.md5("\n".join(items).encode()).hexdigest()[:8]

def is_significant(filename: str) -> bool:
    return any(re.search(p, filename, re.I) for p in SIGNIFICANT_PATTERNS)

def read_wiki_page(wiki_file: Path) -> str:
    return wiki_file.read_text(encoding="utf-8") if wiki_file.exists() else ""

def update_timestamp(content: str, project: str) -> str:
    """Update or add 'Last synced' line near top of wiki page."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tag = f"**Last synced**: {ts}"
    if "**Last synced**" in content:
        content = re.sub(r"\*\*Last synced\*\*:.*", tag, content)
    else:
        # Insert after first blockquote line
        content = re.sub(r"(^>.*$)", r"\1\n> " + tag, content, count=1, flags=re.MULTILINE)
    return content

def update_stack_line(content: str, stack: list[str]) -> tuple[str, bool]:
    """Update the **Stack**: line if it changed."""
    stack_str = ", ".join(stack)
    new_line = f"**Stack**: {stack_str}"
    old_match = re.search(r"\*\*Stack\*\*:.*", content)
    if old_match:
        old_val = old_match.group(0)
        if old_val != new_line:
            return content.replace(old_val, new_line), True
    return content, False

def append_pending(project: str, change_type: str, detail: str):
    """Queue an item for AI review in pending-updates.md."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n### [{ts}] {project}\n**Change type**: {change_type}\n**Detail**: {detail}\n**Status**: pending\n"

    if not PENDING.exists():
        PENDING.write_text("# Pending Wiki Updates\n\n> Items queued for AI review. Run /vault-update to process.\n", encoding="utf-8")

    current = PENDING.read_text(encoding="utf-8")
    if detail not in current:  # dedup
        PENDING.write_text(current + entry, encoding="utf-8")

def load_mtime_cache() -> dict:
    if MTIME_CACHE.exists():
        try:
            return json.loads(MTIME_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_mtime_cache(cache: dict):
    MTIME_CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

def get_source_files(folder: Path) -> list[Path]:
    """Return key source files in project (root + 1 level, skip data/asset dirs)."""
    files = []
    try:
        for f in folder.rglob("*"):
            if not f.is_file():
                continue
            # skip unwanted dirs
            if any(skip in f.parts for skip in SKIP_DIRS):
                continue
            if f.suffix.lower() in TRACK_EXTS:
                files.append(f)
    except PermissionError:
        pass
    return files

def check_source_changes(folder_name: str, folder: Path, cache: dict, check_only: bool) -> list[str]:
    """Detect source files modified since last vault_sync. Queue pending entries."""
    changes = []
    source_files = get_source_files(folder)
    for f in source_files:
        key = str(f)
        try:
            mtime = f.stat().st_mtime
        except OSError:
            continue
        cached_mtime = cache.get(key)
        if cached_mtime is None:
            # First time seeing this file — just record it, don't flag
            if not check_only:
                cache[key] = mtime
        elif mtime > cached_mtime + 2:  # >2s tolerance for filesystem noise
            rel = f.relative_to(folder)
            changes.append(f"Source changed: {rel}")
            if not check_only:
                append_pending(folder_name, "SOURCE CHANGE",
                               f"`{rel}` was modified in {folder_name} — wiki Notes/Gotchas may need updating")
                cache[key] = mtime
    return changes

def write_session_end_note(projects_touched: list[str]):
    """Write a session-end pending entry so next session prompts chat history update."""
    if not projects_touched:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    proj_list = ", ".join(projects_touched)
    entry = (f"\n### [{ts}] SESSION END\n"
             f"**Change type**: SESSION END\n"
             f"**Detail**: Session closed. Projects with source changes: {proj_list}. "
             f"Update chat history files for these projects.\n"
             f"**Status**: pending\n")
    if not PENDING.exists():
        PENDING.write_text("# Pending Wiki Updates\n\n> Items queued for AI review.\n", encoding="utf-8")
    current = PENDING.read_text(encoding="utf-8")
    # Only add if no recent SESSION END already pending
    if "SESSION END" not in current.split("**Status**: pending")[0].split("### [")[-1]:
        PENDING.write_text(current + entry, encoding="utf-8")

def sync_project(folder_name: str, wiki_stem: str, check_only: bool = False) -> list[str]:
    """Sync one project. Returns list of changes made."""
    folder = CODE_ROOT / folder_name
    wiki_file = PROJECTS / f"{wiki_stem}.md"
    changes = []

    if not folder.exists():
        return changes

    content = read_wiki_page(wiki_file)
    if not content:
        append_pending(folder_name, "NEW PROJECT", f"Folder exists but no wiki page found at {wiki_file.name}")
        return [f"QUEUED: {folder_name} needs new wiki page"]

    original = content

    # 1. Detect new significant files
    for f in get_file_list(folder):
        if f.is_file() and is_significant(f.name):
            if f.name not in content:
                changes.append(f"New significant file: {f.name}")
                if not check_only:
                    append_pending(folder_name, "NEW SIGNIFICANT FILE",
                                   f"`{f.name}` added to {folder_name} but not in wiki page")

    # 2. Detect new subdirectories (new labs, new modules)
    for f in get_file_list(folder):
        if f.is_dir() and f.name not in content and not f.name.startswith("."):
            changes.append(f"New subfolder: {f.name}/")
            if not check_only:
                append_pending(folder_name, "NEW SUBFOLDER",
                               f"New directory `{f.name}/` appeared in {folder_name}")

    # 3. Update stack detection
    stack = get_stack(folder)
    if stack and not check_only:
        content, stack_changed = update_stack_line(content, stack)
        if stack_changed:
            changes.append(f"Stack updated: {', '.join(stack)}")

    # 4. Update timestamp
    if not check_only:
        content = update_timestamp(content, folder_name)

    # 5. Write back if changed
    if content != original and not check_only:
        wiki_file.write_text(content, encoding="utf-8")

    return changes

def main():
    check_only   = "--check" in sys.argv
    session_end  = "--session-end" in sys.argv
    target_project = None
    if "--project" in sys.argv:
        idx = sys.argv.index("--project")
        if idx + 1 < len(sys.argv):
            target_project = sys.argv[idx + 1]

    cache = load_mtime_cache()
    all_changes = {}
    projects_with_source_changes = []

    for folder_name, wiki_stem in PROJECT_MAP.items():
        if target_project and folder_name != target_project:
            continue
        # Deduplicate (POO LAB2 and POO Labs both map to POO-Labs)
        if wiki_stem in [v for k, v in list(all_changes.items())]:
            continue

        folder = CODE_ROOT / folder_name
        changes = sync_project(folder_name, wiki_stem, check_only)

        # Check source file mtimes
        if folder.exists():
            src_changes = check_source_changes(folder_name, folder, cache, check_only)
            if src_changes:
                changes.extend(src_changes)
                projects_with_source_changes.append(folder_name)

        if changes:
            all_changes[folder_name] = changes

    if not check_only:
        save_mtime_cache(cache)

    # Session-end: write chat history reminder to pending queue
    if session_end and projects_with_source_changes:
        write_session_end_note(projects_with_source_changes)

    if all_changes:
        print("vault_sync: changes detected")
        for proj, changes in all_changes.items():
            for c in changes:
                print(f"  [{proj}] {c}")
        if check_only:
            print("Run without --check to apply updates.")
    else:
        print("vault_sync: everything up to date")

if __name__ == "__main__":
    main()
