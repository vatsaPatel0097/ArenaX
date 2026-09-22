# ArenaX - Engineering & Architectural Rules ([rules.md](http://rules.md))

This document dictates strict coding patterns and system constraints for the ArenaX codebase. All code added to FastAPI or Next.js MUST strictly follow these rules.

---

## 1. Backend Rules (FastAPI / Python)

### 1.1 Error Handling Rule (CRITICAL)

- **NO RAW** `HTTPException` **OR GENERIC** `Exception`**:** Never raise `HTTPException`, `ValueError`, or bare `Exception` inside endpoints, services, or adapters.

- **CUSTOM** `AppError` **HIERARCHY ONLY:** All errors raised in the backend MUST inherit from `AppError` in `app/core/errors.py`.

- **Standardized Error Structure:**

  ```python
  class AppError(Exception):
      def __init__(self, message: str, code: str, status_code: int = 400, details: dict = None):
          self.message = message
          self.code = code
          self.status_code = status_code
          self.details = details or {}
  ```

- **Predefined Exception Subclasses:**

  - `ProviderQuotaExceededError` (429 - `PROVIDER_QUOTA_EXHAUSTED`)
  - `ProviderUnavailableError` (503 - `PROVIDER_UNAVAILABLE`)
  - `ModelNotFoundError` (444 - `MODEL_NOT_FOUND`)
  - `BattleNotFoundError` (404 - `BATTLE_NOT_FOUND`)
  - `InvalidVoteError` (400 - `INVALID_VOTE`)
  - `AuthenticationError` (401 - `UNAUTHORIZED`)

- **Global Error Handler:** Global FastAPI exception handler converts all `AppError` instances into consistent JSON responses:

  ```json
  {
    "success": false,
    "error": {
      "code": "PROVIDER_QUOTA_EXHAUSTED",
      "message": "Daily free-tier limit reached for Groq.",
      "details": { "provider": "groq", "reset_in_seconds": 3600 },
      "timestamp": "2026-09-13T12:00:00Z"
    }
  }
  ```

### 1.2 Layered Architecture Rule

Strict separation of concerns across directory layers:

1. `app/api/v1/`: API endpoints, request validation schemas, response routers.
2. `app/services/`: Core business logic (Elo calculation, battle orchestration, voting logic).
3. `app/adapters/`: Provider implementations (`OpenRouterAdapter`, `GoogleAdapter`, `GroqAdapter`, `CerebrasAdapter`, `MistralAdapter`).
4. `app/db/`: Async SQLAlchemy models, Alembic migrations, database sessions.
5. `app/core/`: Security, config, Redis client, exception handlers.

### 1.3 Provider Adapter Rules

- All adapters must extend `BaseProviderAdapter` interface:
  - `async def generate_response(prompt: str, model_id: str) -> AsyncGenerator[str, None]`
  - `async def check_quota_available(model_id: str) -> bool`
- **Redis Quota Check First:** Every provider request MUST query Redis quota manager before attempting external HTTP/SDK calls.

### 1.4 Strict Typing & Pydantic v2

- All endpoint parameters, request bodies, and responses MUST be typed using Pydantic v2 schemas (`app/schemas/`).
- Never return untyped Python dictionaries (`dict`) from service methods or endpoint handlers.

### 1.5 Strict DRY (Don't Repeat Yourself) Principle
- Never duplicate code or logic in backend services, adapters, or endpoints.
- Even if 2 lines of code are repeated, extract them into a reusable helper function or utility module (`app/core/utils.py` or service helpers).

---

## 2. Frontend Rules (Next.js 15 / React 19 / TypeScript)

### 2.1 Uniform API Client & Error Handling

- All API interactions MUST pass through the shared `apiClient` (`lib/api-client.ts`).
- Catch `AppError` payloads from backend and surface them via standard toast notifications (`<Toast />`) or in-card quota warnings. Never let uncaught API errors crash component renders.

### 2.2 Design Token & Global Color Compliance (CRITICAL)

- **NO HARDCODED COLOR VALUES:** Never use inline hex colors (`#6366f1`), RGB/HSL values, or raw color names in `.tsx`, `.ts`, or component files.
- **ALWAYS USE GLOBAL CSS TOKENS:** All color styling MUST reference global CSS tokens (`var(--bg-primary)`, `var(--accent-cyan)`, `var(--text-primary)`, etc.) defined in `globals.css` / `ui-token.md`.

---

## 3. Version Control & Git Rule

- **NO AUTOMATIC COMMIT OR PUSH:** Never run `git commit` or `git push` commands under any circumstances. All git commits and pushes will be managed exclusively by the user.
- **COMMIT MESSAGE GENERATION:** Upon completing any sub-phase or task, ALWAYS output a clean, formatted Conventional Commit message (subject line + detailed bullet points) for the user to copy for their git commit.


### 2.3 State Management Rules

- Use local component state for transient inputs.
- Use React Context / Zustand for global active battle state, user key settings, and active provider selection.
- Do NOT directly mutate state objects or arrays. Always return fresh immutable updates.

---

## 3. Database & Migration Rules

- **Async SQLAlchemy Only:** All DB operations in FastAPI must use `AsyncSession`. No synchronous DB calls permitted on the main event loop.
- **Alembic Migrations Required:** Any change to `app/db/models/` MUST be accompanied by an Alembic migration script in `alembic/versions/`.
- **Database Schema Constraints:**
  - Foreign keys required on `votes.battle_id` -&gt; `battles.id`.
  - Enums for vote results (`model_a`, `model_b`, `tie`, `both_bad`).
  - Indexing required on `models.provider`, `battles.created_at`, `elo_ratings.rating`.