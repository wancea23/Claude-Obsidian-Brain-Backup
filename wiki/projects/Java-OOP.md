# Java — Phone Charging Simulation

> OOP simulation of a phone charging system
> **Last synced**: 2026-06-05 21:42

**Path**: `Code/Java/`
**Stack**: Java, Markdown
**Context**: University Java coursework

---

## What It Does

### User Experience
- Demonstrates a phone charging simulation
- `Outlet` → `Charger` → `Phone` — voltage flows through the chain
- Run the program, see charging state printed to console

### System Experience
Three classes interacting via OOP:
- `Outlet` — power source with a voltage value
- `Charger` — connects to outlet, steps voltage for phone
- `Phone` — has a battery; charges when connected to charger

Demonstrates: encapsulation, class interaction, method calls

---

## Key Files
| File | Role |
|------|------|
| `main.java` | Entry point + simulation |
| `Charger.class` | Compiled charger class |
| `Outlet.class` | Compiled outlet class |
| `Phone.class` | Compiled phone class |
| `images/` | Supporting images/diagrams |
| `TEST/` | Test cases |
| `README.md` | Project overview & class documentation |

---

## Run
```bash
javac main.java
java main
```

---

## Backup Log
See [[../backups/Java-backup|Backup History]]
