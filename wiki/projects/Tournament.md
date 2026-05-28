# Tournament — Bot Competition

> Programming competition bot (team_07)
> **Last synced**: 2026-05-29 00:27

**Path**: `Code/Tournament/`
**Stack**: Python, HTML

---

## What It Does

### User Experience
- A bot that competes in a programming tournament
- `team_07.py` — the actual competition bot submission
- `test_bot.py` — local test harness to validate bot behavior before submission

### System Experience
- `team_07.py` — bot logic: reads game state, outputs moves/decisions
- `test_bot.py` — runs the bot against test scenarios
- `__pycache__` present — actively run locally

---

## Key Files
| File | Role |
|------|------|
| `team_07.py` | Competition bot (team 07's submission) |
| `test_bot.py` | Local testing |
| `Battleground/Main.py` | Battleground mode entry point |
| `Battleground/Mahoraga.py` | Bot strategy — Mahoraga agent |
| `Battleground/Player.py` | Player model / state representation |
| `Battleground/Strategies.py` | Strategy definitions for Battleground mode |
| `Battleground/battle.html` | Battleground visualizer / replay viewer |

---

## Run
```bash
# Test the bot locally
python test_bot.py

# Run the bot directly
python team_07.py
```

---

## Notes
- Competition context — bot likely follows a specific API/protocol defined by the tournament
- Team number: 07
- **Battleground/** subfolder added (2026-04-29): new competitive mode with dedicated strategy agents (Mahoraga), player model, and an HTML battle visualizer. Separate from the base `team_07.py` submission.

---

## Backup Log
See [[../chat-history/Tournament-chats|Chat History]] · [[../backups/Tournament-backup|Backup History]]
