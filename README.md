# ArenaX ⚔️

> **Free Model Arena** — An open-source, crowd-sourced platform for side-by-side LLM evaluation powered by free-tier model APIs and Bring-Your-Own-Key (BYOK).

---

## 🚀 Overview

**ArenaX** is an open-source clone of LMSYS LMArena designed to evaluate and rank AI models side-by-side with **zero paid inference costs**. By leveraging free-tier APIs and OpenRouter free models, users can compare outputs, vote on response quality, and maintain a dynamic Elo-style leaderboard.

- 🥊 **Side-by-Side Battles:** Run identical prompts across two models simultaneously.
- 🎭 **Anonymized Voting:** Conceal model identity during battles to eliminate bias before casting votes (`Model A Wins`, `Model B Wins`, `Tie`, `Both Bad`).
- 📈 **Dynamic Elo Leaderboard:** Crowd-sourced model rankings updated in real time via Bradley-Terry / Elo algorithms.
- ⚡ **Zero-Cost BYOK Architecture:** Built-in provider adapters and Redis-backed rate-limit tracking for maximum quota efficiency.

---

## 🛠️ Technology Stack

| Layer | Technology |
| --- | --- |
| **Backend Framework** | FastAPI (Python 3.12+) |
| **Frontend Framework** | Next.js 15 (App Router, React 19, TypeScript) |
| **Authentication** | Clerk Auth |
| **Primary Database** | PostgreSQL (Async SQLAlchemy + Alembic) |
| **Quota & Rate-Limiting** | Redis |
| **Styling** | Vanilla CSS Design Tokens (Dark Obsidian Glassmorphism) |

---

## 🌐 Supported LLM Providers (v1)

1. **OpenRouter** (`:free` aggregator models)
2. **Google AI Studio** (Gemini Models)
3. **Groq** (Llama 3.3 70B ultra-fast LPU inference)
4. **Cerebras** (High-throughput inference with dynamic model registry)
5. **Mistral** (Free experiment tier models)

---

## 📦 Project Structure

```
ArenaX/
├── backend/            # FastAPI async backend application
├── frontend/           # Next.js 15 web interface
├── MDs/                # Project design documentation, PRD, and rules
├── .gitignore          # Repository ignore rules
└── README.md           # Project documentation
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
