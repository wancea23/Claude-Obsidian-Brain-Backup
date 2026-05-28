"""
vault_pre_edit.py — Auto-backup file content before Claude edits it.

Called by PreToolUse hook on Edit|Write tool calls.
Reads JSON from stdin, extracts old content, appends to file-history.md.

- Edit tool:  captures old_string (the exact text being replaced)
- Write tool: captures current file content if file exists and is ≤150 lines

Key files only: .css .html .py .js .ts .java .c .cpp .bat
Skips: graphify-out/, __pycache__/, node_modules/, data/, images/, venv/
Dedup: won't re-backup same file within 5 minutes
"""

import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime

CODE_ROOT    = Path("C:/Users/johns/OneDrive - Technical University of Moldova/Code")
FILE_HISTORY = CODE_ROOT / "graphify-out" / "wiki" / "file-history.md"

KEY_EXTS  = {".css", ".html", ".py", ".js", ".ts", ".java", ".c", ".cpp", ".bat", ".sh"}
SKIP_DIRS = {"graphify-out", "__pycache__", "node_modules", "venv", "data", "images",
             "dist", "build", ".git"}
MAX_LINES = 150
DEDUP_SECONDS = 300


def is_key_file(path: Path) -> bool:
    if path.suffix.lower() not in KEY_EXTS:
        return False
    parts = set(path.parts)
    return not parts.intersection(SKIP_DIRS)


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(CODE_ROOT))
    except ValueError:
        return path.name


def was_recently_backed_up(rel: str, content: str) -> bool:
    pattern = rf"### \[(\d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}})\] {re.escape(rel)}"
    matches = re.findall(pattern, content)
    if not matches:
        return False
    try:
        last_ts = datetime.strptime(matches[-1], "%Y-%m-%d %H:%M")
        return (datetime.now() - last_ts).total_seconds() < DEDUP_SECONDS
    except ValueError:
        return False


def append_to_history(rel: str, old_value: str, lang: str = ""):
    if not old_value or not old_value.strip():
        return

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    current = FILE_HISTORY.read_text(encoding="utf-8") if FILE_HISTORY.exists() else ""

    if was_recently_backed_up(rel, current):
        return

    fence = f"```{lang}" if lang else "```"
    entry = (
        f"\n### [{ts}] {rel}\n"
        f"**Change**: (fill in — what changed and why)\n"
        f"**Old value**:\n{fence}\n"
        f"{old_value.rstrip()}\n"
        f"```\n"
    )

    # Ensure the Log section exists
    if "## Log" not in current:
        current += "\n## Log\n"

    FILE_HISTORY.write_text(current + entry, encoding="utf-8")


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        data = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        return

    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name == "Edit":
        file_path_str = tool_input.get("file_path", "")
        old_string    = tool_input.get("old_string", "")
        if not file_path_str or not old_string:
            return

        path = Path(file_path_str)
        if not is_key_file(path):
            return

        ext  = path.suffix.lower().lstrip(".")
        lang = {"css": "css", "html": "html", "py": "python", "js": "javascript",
                "ts": "typescript", "java": "java", "c": "c", "cpp": "cpp"}.get(ext, "")

        append_to_history(rel_path(path), old_string, lang)

    elif tool_name == "Write":
        file_path_str = tool_input.get("file_path", "")
        if not file_path_str:
            return

        path = Path(file_path_str)
        if not path.exists() or not is_key_file(path):
            return

        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return

        if len(lines) > MAX_LINES:
            return

        ext  = path.suffix.lower().lstrip(".")
        lang = {"css": "css", "html": "html", "py": "python", "js": "javascript",
                "ts": "typescript", "java": "java", "c": "c", "cpp": "cpp"}.get(ext, "")

        append_to_history(rel_path(path), "\n".join(lines), lang)


if __name__ == "__main__":
    main()
