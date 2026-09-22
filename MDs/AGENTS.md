# ArenaX - AI Agent Master Context Index (AGENTS.md)

Welcome AI Coding Assistant. This single document links and synthesizes all architectural guidelines, design system tokens, component specs, project scope, engineering rules, and task progress trackers for the **ArenaX** project.

Reading this file gives you complete context over the entire project.

---

## 📚 Master Index of Documentation Files

| Document | Purpose & Key Details | File Link |
| --- | --- | --- |
| **PRD** | Original Product Requirements Document (Goals, Providers, Data Model, Milestones) | [PROJECT_PRD.md](file:///d:/ArenaX/MDs/PROJECT_PRD.md) |
| **Project Overview** | Executive summary, tech stack (FastAPI + Next.js 15), in-scope vs out-of-scope features | [project_overview.md](file:///d:/ArenaX/MDs/project_overview.md) |
| **UI Design Tokens** | CSS variables for obsidian dark theme, glassmorphism, cyan/purple model accents, typography | [ui-token.md](file:///d:/ArenaX/MDs/ui-token.md) |
| **UI Component Registry** | Complete specifications for Leaderboard Table, Battle Cards, Voting Bar, Model Selectors, Badges | [ui-registry.md](file:///d:/ArenaX/MDs/ui-registry.md) |
| **Engineering Rules** | Strict `AppError` exception hierarchy (No raw `HTTPException`), Async SQLAlchemy, Adapter rules | [rules.md](file:///d:/ArenaX/MDs/rules.md) |
| **Progress Tracker** | Detailed breakdown of Phase 1 to Phase 6. **Rule:** Execute strictly 1 sub-phase at a time (e.g. 1.1 first) | [progress-tracker.md](file:///d:/ArenaX/MDs/progress-tracker.md) |

---

## ⚡ Core Directives for AI Assistant

1. **Strict Error Rule:** Never introduce raw `HTTPException`, `ValueError`, or standard unhandled exceptions in backend code. Always use `AppError` subclasses from `backend/app/core/errors.py`.
2. **Sub-phase Incremental Rule:** Work MUST be completed **one sub-phase at a time** as outlined in [progress-tracker.md](file:///d:/ArenaX/MDs/progress-tracker.md). (Current active sub-phase is `1.2`).
3. **UI Consistency & Global Color Rule:** NEVER hardcode color values (hex, rgb, hsl, or literal colors) in frontend `.tsx`, `.ts`, or component files. All colors MUST use global CSS tokens defined in `globals.css` / `ui-token.md` (e.g., `var(--bg-primary)`, `var(--accent-cyan)`).
4. **Backend Strict DRY Rule:** Strictly follow the DRY (Don't Repeat Yourself) principle. Even if 2 lines of logic or code patterns are repeated, extract them into a reusable function/helper to prevent duplicate code.
5. **No Automatic Git Commit / Push Rule:** NEVER run `git commit` or `git push` commands. The user will manually handle all version control commits and pushes.
6. **Provider Adapter Rule:** New LLM provider integrations must inherit from `BaseProviderAdapter` and query Redis quota manager prior to external requests.
7. **Commit Message Generation Rule:** Upon completion of every sub-phase or task, ALWAYS provide a clean, standardized Conventional Commit message (subject line + brief summary of key changes) for the user to copy and use for their git commit.


