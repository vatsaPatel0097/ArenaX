# ArenaX - Project Overview

## 1. Executive Summary

**ArenaX** is an open-source, crowd-sourced AI model evaluation platform inspired by LMSYS LMArena. It allows users to run side-by-side prompt comparisons across multiple free-tier LLMs (via BYOK / free provider tiers) and vote on model outputs to maintain a dynamic, crowd-ranked Elo leaderboard.

The system is designed to run with **zero paid inference overhead** by leveraging free API quotas from top providers and OpenRouter free models.

---

## 2. In-Scope vs Out-of-Scope (v1)

### 2.1 In-Scope (v1)

- **Side-by-Side Model Battle Mode:**
  - Users select two specific models to battle against each other.
  - Prompts are executed in parallel across both selected model endpoints.
  - Model responses are streamed side-by-side.
  - Option for anonymized display (model identity hidden until vote cast).
- **Voting & Elo Leaderboard:**
  - Voting options: `Model A wins`, `Model B wins`, `Tie`, `Both Bad`.
  - Dynamic Elo score calculation following standard Bradley-Terry / Elo ranking models.
  - Public leaderboard filterable by model provider and date ranges.
- **Provider Adapter Architecture:**
  - Extensible adapter layer supporting 5 initial providers:
    1. **OpenRouter** (`:free` models)
    2. **Google AI Studio** (Gemini models)
    3. **Groq** (Llama 3.3 70B, high speed)
    4. **Cerebras** (Ultra-fast inference, dynamic model registry sync)
    5. **Mistral** (Free experiment tier models)
- **Redis Quota & Rate-Limit Tracking:**
  - Per-minute (RPM) and per-day (RPD) quota guardrails stored in Redis to prevent hitting provider hard limits.
- **Direct Side-by-Side Chat Mode:**
  - Free-form chat testing against single or dual models without recorded votes.
- **Authentication & User Management:**
  - Clerk Auth integration for user sessions and vote integrity.

### 2.2 Out-of-Scope (v1)

- Paid/metered model inference beyond free tier limits.
- Automated random matchmaking battle queue (planned for v2).
- Multi-modal comparisons (Image, Audio, Video - v1 is strictly text-based).
- Granular per-prompt telemetry & deep analytics dashboard beyond leaderboard Elo.

---

## 3. Technology Stack & Architecture

### 3.1 Languages & Frameworks

| Layer | Technology | Purpose |
| --- | --- | --- |
| **Backend Language** | Python 3.12+ | Core server runtime |
| **Backend Framework** | FastAPI | High-performance async REST API & SSE streaming |
| **Database ORM** | Async SQLAlchemy + Alembic | DB models, migrations, & persistence |
| **Frontend Language** | TypeScript | Type-safe web interface |
| **Frontend Framework** | Next.js 15 (App Router) + React 19 | Frontend application framework |
| **Styling & Tokens** | Custom Vanilla CSS Tokens | Sleek dark glassmorphism aesthetic |
| **Auth Provider** | Clerk | User authentication & session management |
| **Primary Database** | PostgreSQL | Battles, votes, Elo ratings, model catalog |
| **Cache & Quota Layer** | Redis | Provider RPM/RPD rate-limit state |

---

## 4. Key Architectural Goals

1. **Adapter Pattern Isolation:** Adding a new LLM provider requires zero changes to core battle logic—only a new subclass of `BaseProviderAdapter`.
2. **Quota Resilience:** Graceful degradation and user-facing notifications when a provider's daily quota is depleted.
3. **Consistent UI Design:** Strict adherence to design tokens and component specs for a unified, modern dark aesthetic.
4. **Strict Error Contract:** Custom `AppError` hierarchy enforced across backend and frontend to eliminate raw standard crashes or unhandled 500 responses.
