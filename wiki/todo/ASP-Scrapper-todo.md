# ASP Scrapper — Todo & Known Issues

---

## High Priority
- **Live-test auto-update flow** on `/APO/my-appointments`. Selectors are inferred from screenshots only; first real run will likely need a tweak. Watch for: visible-input order (IDNP/code/request), Cautare/Modifică/DA button matching, Ora dropdown name (`select[name*="Time"|"Hour"|"Ora"]` is a guess), confirm popup wording.
- **Rebuild `.exe`** — `dist/ASP Exam Checker.exe` is stale relative to the new auto-update code. Run `BUILD.bat`.

## Improvements
- Auto-fetch current appointment date once at startup (open my-appointments, parse table) instead of asking the user to type it in. Would also auto-update the stored date after a manual rebook done outside the app.
- Move the two DECA locations (`TARGET_LOCATIONS` in `app.py`) into config or detect them dynamically from the live form, so adding/removing offices doesn't need a code change.
- Add visual feedback in the GUI while auto-update is running (currently only shows in console + TG).

## Known Issues
- Stale `dist/ASP Exam Checker.exe` committed to repo — large binary, predates auto-update.
- `target_months` was widened to `["aprilie","mai","iunie"]` in `credentials.json` so something has a chance of beating the 25.06.2026 booking. `aprilie` is already past; revisit.

## Completed ✓
- 2026-05-28: Auto-update appointment feature (commit `6dfecd7`, local-only). See [[../chat-history/ASP-Scrapper-chats|chat history]] and [[../decisions/ASP-Scrapper-decisions|decisions]].

[[../projects/ASP-Scrapper|← Back to ASP Scrapper wiki]]
