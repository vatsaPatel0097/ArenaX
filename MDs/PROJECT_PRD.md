# PRD: Free Model Arena (LMArena Clone)

## 1. Overview

An open-source, LMArena-style platform for comparing AI model outputs side-by-side, using only BYOK and free-tier model APIs. Users select two models, run the same prompt against both, and vote for a winner — building an Elo-style leaderboard over time.

## 2. Goals

- Let users directly compare responses from different LLMs on the same prompt.
- Track relative model quality via crowd-sourced voting and Elo ratings.
- Run entirely on free-tier / BYOK model access — no paid inference cost to operate.
- Ship as a portfolio-quality, open-source project (FastAPI + Next.js + Clerk).

## 3. Non-Goals (v1)

- No support for paid/metered model usage beyond what's needed to unlock free tiers (e.g. OpenRouter's $10 topup threshold).
- No fully-random or auto-matchmaking battle mode — deferred to a later version.
- No fine-grained analytics dashboard beyond the leaderboard.

## 4. Core Features

### 4.1 Battle Mode

- User selects **both** models to compare (from the enabled provider/model list) — no random pairing in v1.
- User submits one prompt; it's sent to both selected models in parallel.
- Responses are shown side-by-side, anonymized by default (model identity hidden until vote is cast, matching LMArena convention) — *flag this as a decision to confirm, see Open Questions.*
- User votes: Model A wins / Model B wins / Tie / Both bad.
- Vote updates Elo ratings for both models and is logged to history.

### 4.2 Side-by-Side Chat

- Free-form chat mode against a single selected model, outside of battle/voting flow (for casual testing).

### 4.3 Leaderboard

- Elo-style ranking of all models, updated after each vote.
- Filterable by provider, and by date range if feasible in v1.

### 4.4 Model Providers (v1)

All 5 are in scope for v1; provider integration should be built behind a common adapter interface so ones can be toggled on/off without code changes elsewhere.

| Provider | Free Tier (subject to change — verify live) | Notes |
| --- | --- | --- |
| OpenRouter | \~1,000 req/day on `:free` models (unlocked after $10 topup, already done) | Aggregator — many models behind one key |
| Google AI Studio (Gemini) | \~1,000–1,500 req/day (Google no longer publishes exact numbers post-Dec-2025 cuts) | Strongest frontier-quality free model |
| Groq | 30 RPM / 1,000 RPD / 100K TPD (Llama 3.3 70B) | Fastest inference, custom LPU hardware |
| Cerebras | 1M tokens/day | High volume; free model catalog has been volatile — fetch live model list, don't hardcode |
| Mistral | 1B tokens/month at 2 RPM | Requires opting into data training on free "Experiment" tier |

## 5. Technical Design

### 5.1 Stack

- **Backend:** FastAPI
- **Frontend:** Next.js
- **Auth:** Clerk
- **Primary DB:** Postgres — battles, votes, Elo ratings, model/provider metadata (durable, queryable for future stats)
- **Cache/rate-limit layer:** Redis — per-provider RPM/RPD quota tracking (fast counters with TTL), consistent with existing Celery/Redis experience

### 5.2 Provider Adapter Layer

- Common interface (e.g. `Provider.chat(prompt, model) -> response`) implemented per provider.
- Each adapter responsible for: auth/key handling (BYOK), request formatting, response normalization, error/timeout handling.
- A model registry synced periodically (not hardcoded) — especially important for Cerebras given recent free-model-list volatility.
- Redis-backed quota tracker checks remaining daily/per-minute budget before routing a request to a given provider; falls back or surfaces "provider unavailable" if exhausted.

### 5.3 Data Model (initial sketch)

- `models` — provider, model_id, display_name, active flag
- `battles` — id, prompt, model_a_id, model_b_id, response_a, response_b, created_at
- `votes` — battle_id, result (a_wins / b_wins / tie / both_bad), voted_at
- `elo_ratings` — model_id, rating, updated_at

## 6. Open Questions

- **Anonymity in battle mode:** Should model identity be hidden until after voting (standard LMArena behavior), or shown upfront? Affects UI and whether votes should be discarded/flagged when identity bias is suspected.
- **Rate-limit exhaustion UX:** If a provider's daily quota is hit mid-session, do we auto-swap to another provider's equivalent model, or block that provider until reset?
- **Data policy disclosure:** Some free tiers (Google, Mistral) may use prompts for training. Should the UI warn users before they submit a prompt, given this is a public/portfolio project?

## 7. Milestones (suggested)

1. Provider adapter layer + Redis quota tracking for all 5 providers
2. Postgres schema + battle mode (user-selected models, no voting yet)
3. Voting + Elo calculation
4. Leaderboard UI
5. Side-by-side free chat mode
   1. Polish, deploy, open-source release
