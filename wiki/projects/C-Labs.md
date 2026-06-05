# C University Labs

> C programming assignments — TUM coursework
> **Last synced**: 2026-06-05 21:42

**Path**: `Code/C/`
**Stack**: C, Python
**Context**: University lab submissions

---

## Subfolders

### `PC/` — Programming Concepts
Basic C exercises: arithmetic, logic, arrays, strings, file I/O
- Examples: `1_1_Addition.c`, `2_2_Math_Formula.c`, `7_4_Logical_Expression.c`
- Each lab has a `.c` source and compiled `.exe`
- Naming: `{lab}_{task}_{description}.c`

### `PC_Teams/` — Team-based PC Labs
Same PC syllabus but done in groups

### `SDA/` — Data Structures & Algorithms
- Individual works + Lab1–Lab7
- Topics: sorting, linked lists, trees, graphs, etc.

### `NA/` — Numerical Analysis
- Numerical methods implementations in C

---

## Patterns
- Every `.c` file has a corresponding `.exe` (compiled on Windows)
- Standard library: `stdio.h`, `string.h`, `math.h`
- All programs use `main()` as entry point
- Input via `scanf`/`fgets`, output via `printf`

---

## Compile
```bash
gcc filename.c -o filename.exe -lm
```

---

## Notes
- Files named with lab/task numbers for easy lookup
- `7_4_Logical_Expression.c` — example of string manipulation + logical checks
- SDA folder has individual works separate from lab submissions

---

## Backup Log
See [[../chat-history/C-Labs-chats|Chat History]] · [[../backups/C-Labs-backup|Backup History]]
