# Skills Installed

> All Claude Code skills, tools, and extensions — current and planned.
> Update this whenever you install something new.

---

## Currently Installed

### Claude Code Skills — Global (`~/.claude/skills/`)

| Skill               | Install command                      | What it does                                                    |
| ------------------- | ------------------------------------ | --------------------------------------------------------------- |
| **graphify**        | `graphify install --platform claude` | Knowledge graph — maps codebase, query before reading raw files |
| **emil-design-eng** | *(marketplace)*                      | UI polish philosophy — Emil Kowalski's design principles        |
| **ui-ux-pro-max**   | *(marketplace)*                      | UI/UX design intelligence — 50+ styles, palettes, font pairings |
| **agent-browser**   | *(global)*                           | Browser automation CLI for AI agents — navigate, click, screenshot |
| **find-skills**     | *(global)*                           | Discover & install agent skills |
| **systematic-debugging** | *(global)*                      | Methodology for diagnosing bugs / test failures before proposing fixes |
| **web-design-guidelines** | *(global)*                     | Review UI for Web Interface Guidelines compliance |
| **spritecook-*** (3)| *(global)*                           | SpriteCook workflow / pixel-art / animation skills (gamedev) |
| **vault-update**    | *(global)*                           | Process pending wiki updates from the queue |

### Claude Code Skills — Project (`Code/.claude/skills/`)

Installed 2026-05-23. These were installed via `npx skills add` to `.agents/skills/` (which targets *other* agents like Cursor/Cline) — I copied them into `.claude/skills/` so Claude Code can also invoke them. They become visible after restarting Claude Code.

| Skill                | Source                                  | What it does                                                            |
| -------------------- | --------------------------------------- | ----------------------------------------------------------------------- |
| **seo-audit**        | coreyhaines31/marketingskills           | Audit / diagnose SEO issues — meta tags, page speed, core web vitals, crawl, indexing |
| **ai-seo**           | coreyhaines31/marketingskills           | Optimize content for AI search engines (AIO/AEO/GEO/LLMO) — ChatGPT/Perplexity/AI Overviews citations |
| **frontend-design**  | anthropics/skills                       | Build distinctive production-grade frontend interfaces — bold design direction, real working code |
| **impeccable**       | pbakaus/impeccable                      | Design / redesign / polish frontend UI — visual hierarchy, micro-interactions, typography, motion |

### Global Claude Settings (`~/.claude/settings.json`)
- `ui-ux-pro-max@ui-ux-pro-max-skill` — enabled plugin
- `effortLevel: max`

### Python Tools
| Tool | Install | What it does |
|------|---------|-------------|
| **graphifyy** | `pip install graphifyy` | Code graph builder (AST extraction, no LLM needed) |
| **playwright** | `pip install playwright` + `playwright install chromium` | Browser automation for 999 AutoPost & ASP Scrapper |

---

## Planned / Want to Install

| Skill/Tool | Source | Reason to install |
|------------|--------|------------------|
| *(add here)* | | |

---

## How to Add a New Skill

```bash
# From Claude Code marketplace
# Type /install in Claude Code

# From GitHub repo
pip install <package>
graphify install --platform claude   # if it's graphify-based

# Manual skill file
# Place SKILL.md in ~/.claude/skills/<skill-name>/
# Add entry to ~/.claude/CLAUDE.md
```

---

## Skill Trigger Reference — when Claude should invoke each one

> **For future-Claude**: this is your decision tree. The user installed these so I can use them proactively, not just on request. Pick the closest match by what they actually said, not by skill name.

### `/graphify` family
| Trigger | Skill |
|---|---|
| User asks about codebase structure, "where is X", "what does Y do" | `graphify query "..."` BEFORE reading raw files |
| User edited code files in the session | `graphify update .` at end of session |
| `/graphify` typed explicitly | `graphify` skill |

### Frontend / UI / design — pick ONE, don't chain

These four overlap heavily. Use this priority order:

1. **`frontend-design`** — *Building NEW frontend from scratch.* Component, page, app, "build me a landing page", "create a dashboard." Bias toward bold, distinctive aesthetic direction. The skill explicitly warns against generic AI slop.
2. **`impeccable`** — *Iterating on EXISTING UI.* "polish this", "make it more delightful", "review my UI", "redesign", "audit visual hierarchy", micro-interactions, motion, typography. Has sub-commands (`craft`, `shape`, `audit`) — load the right reference.
3. **`ui-ux-pro-max`** — *Needs specific design tokens.* When user asks for color palettes, font pairings, or specific styles (glassmorphism, brutalism, neumorphism, claymorphism, bento grid). Has 50+ styles, 161 palettes, 57 font pairings catalogued. Also good for shadcn/ui MCP component lookups.
4. **`web-design-guidelines`** — *Compliance check.* "review my UI", "check accessibility", "audit against best practices." Outputs a structured report, not redesigns.
5. **`emil-design-eng`** — *Philosophy/principles question.* When user asks WHY a design feels off, what makes good UI feel premium. Reference, not generator.

**Conflict rule**: if it's a 999 CarScrapper / Site / m99gadgets refresh → `impeccable` (it's existing UI). If it's a brand-new artifact → `frontend-design`. If user names a specific style → `ui-ux-pro-max`.

### SEO
| Trigger | Skill |
|---|---|
| "audit my SEO", "why am I not ranking", "Google update hit me", "page speed", "core web vitals", "crawl errors", "meta tags review", "SEO health check" | `seo-audit` |
| "AI SEO", "AEO", "GEO", "LLMO", "answer engine optimization", "optimize for ChatGPT/Perplexity/Claude", "AI Overviews", "AI citations", "zero-click search" | `ai-seo` |
| User says just "SEO" vaguely | start with `seo-audit`, then offer `ai-seo` after |

### Other
| Trigger | Skill |
|---|---|
| Bug, test failure, "this is broken", anything unexpected — BEFORE proposing a fix | `systematic-debugging` |
| User wants to interact with a real browser (login, click, screenshot, scrape, test webapp) | `agent-browser` |
| User asks "is there a skill for X" / "find a skill" | `find-skills` |
| Pending wiki updates in `pending-updates.md` | `vault-update` |
| Pixel art / sprite generation / sprite animation (gamedev work) | `spritecook-*` |

### Anti-patterns
- Don't chain frontend skills (`frontend-design` THEN `impeccable` THEN `ui-ux-pro-max`). Pick one.
- Don't invoke `seo-audit` for ai-seo questions or vice versa.
- Don't invoke a design skill for a backend/Python/SQL change.
- Don't invoke a skill without telling the user what you're doing — they're billed work.

---

## Notes
- Skills in `~/.claude/skills/` are global — available in every project
- Project-level hooks are in `Code/.claude/settings.json` (syncs via OneDrive)
- Global hooks are in `~/.claude/settings.json` (device-local, doesn't sync)

[[index|Back to Vault Index]]
