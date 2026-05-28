# Global Design Decisions

> Cross-project patterns and rules discovered through work. Prevents re-researching the same problems.
> Add entries here when a decision applies to multiple projects or is a general rule.

---

## CSS / Frontend

### position:fixed inside backdrop-filter — NEVER
**Rule**: Never place `position:fixed` elements inside a parent that has `backdrop-filter`, `filter`, `transform`, or `will-change:transform`.
**Why**: Safari iOS (and some mobile Chromium builds) repositions fixed children relative to that ancestor instead of the viewport — making them invisible or misplaced.
**Fix**: Move fixed elements to be direct `<body>` children.
**Affected projects**: m99gadgets (cart button)

### position:fixed with both top AND bottom set — NEVER
**Rule**: Never set both `top` and `bottom` on the same `position:fixed` element.
**Why**: The browser stretches the element to fill the gap between them. Causes elements to span the full viewport height.
**Fix**: When overriding in a media query, always unset the other axis with `top:auto` or `bottom:auto`.
**Affected projects**: m99gadgets (cart button stretched to full height on mobile)

### dvh fallback for older iOS Safari
**Rule**: Always include `height:100vh` before `height:100dvh` when using dvh units.
**Why**: Older iOS Safari (pre-15.4) doesn't support dvh. Without the fallback, sections collapse.
```css
.hero { height: 100vh; height: 100dvh; }
```

### overflow-x:hidden — html AND body
**Rule**: Apply `overflow-x:hidden` to both `html` and `body`, not just `body`.
**Why**: On some browsers, setting only `body` still allows `html` to scroll horizontally.

---

## Python / Desktop Apps

### PyInstaller frozen asset paths
**Rule**: Use `sys._MEIPASS` for asset paths in frozen builds, `__file__` otherwise.
```python
if getattr(sys, 'frozen', False):
    BASE = sys._MEIPASS
else:
    BASE = os.path.dirname(__file__)
```
**Affected projects**: 999 AutoPost, ASP Scrapper

### Playwright in PyInstaller
**Rule**: Import `aiohttp` and `playwright` in `app.py` even if unused — required so PyInstaller bundles them for modules that need them at runtime.
**Affected projects**: 999 AutoPost, ASP Scrapper

### CTk async threading
**Rule**: Never run async/Playwright directly in the main CTk thread. Always use `threading.Thread` + `asyncio.run()`. Send results back via `queue.Queue` drained by `after()`.
**Affected projects**: 999 AutoPost, ASP Scrapper

---

## File Organization

### Never save to root folder
**Rule**: Use `/src`, `/tests`, `/docs`, `/scripts`, `/config` — never the project root.
**Why**: Root gets cluttered; hard to find generated vs. source files.

### Vault files are read-only from hooks
**Rule**: PostToolUse hooks that edit vault files (vault_sync.py, vault_pre_edit.py) can conflict with my own edits to vault files. vault_sync.py runs after every Edit/Write — if I'm editing a vault file, the hook will update it again immediately. Always re-read vault files before editing if the hook may have changed them.

---

## Vault / Knowledge Management

### Session start order
1. pending-updates.md → process FILL CHAT HISTORY first
2. mistakes.md → check pitfalls
3. Project wiki + decisions + todo
4. Only then work

### Session end order
1. Fill chat history template
2. Add new mistakes
3. Add new decisions
4. Update todo
5. /exit

[[index|← Vault Index]]
