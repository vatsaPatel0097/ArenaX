# ArenaX - UI Component Registry (ui-registry.md)

This registry specifies all standard UI components, their variants, color rules, layout behaviors, and state styles. Every page or feature in ArenaX MUST consume components adhering to these exact patterns.

---

## 1. Table Component (`<LeaderboardTable />`)

The Leaderboard Table displays model Elo ratings, provider tags, battle stats, and win rates.

### 1.1 Structural Requirements
- **Container:** Full width, glass panel (`var(--bg-card)` + `var(--backdrop-blur)`), rounded (`var(--radius-lg)`), border (`var(--border-subtle)`).
- **Header:** Sticky header, dark surface (`var(--bg-secondary)`), uppercase caption text (`var(--font-xs)`, `var(--text-muted)`), 1px bottom border.
- **Row:** Height 56px, `transition: background var(--transition-fast)`. Hover state: `background: var(--bg-tertiary)`.
- **Rank Badges:**
  - Rank 1: Gold Pill (`background: rgba(245, 158, 11, 0.15)`, `color: var(--accent-gold)`, `border: 1px solid var(--accent-gold)`).
  - Rank 2: Silver Pill (`background: rgba(226, 232, 240, 0.15)`, `color: #e2e8f0`, `border: 1px solid #94a3b8`).
  - Rank 3: Bronze Pill (`background: rgba(205, 127, 50, 0.15)`, `color: #cd7f32`, `border: 1px solid #b45309`).
  - Rank 4+: Muted Number (`color: var(--text-muted)`).

### 1.2 Column Layout
| Column | Width | Alignment | Description |
| --- | --- | --- | --- |
| **Rank** | 80px | Center | Rank badge / number |
| **Model Name** | Auto | Left | Model display name + provider pill badge |
| **Elo Rating** | 120px | Right | Bold rating score (e.g. `1245` in `var(--accent-primary)`) |
| **Win Rate** | 100px | Right | Percentage + mini progress bar |
| **Total Battles** | 110px | Right | Integer count |
| **Provider** | 130px | Center | Provider tag |

---

## 2. Battle Container & Cards (`<BattleCard />`)

Used in side-by-side battle mode.

### 2.1 Dual Pane Grid
- **Layout:** Responsive 2-column grid (`grid-template-columns: 1fr 1fr` on desktop, 1-column stack on mobile).
- **Gap:** `var(--space-4)`.

### 2.2 Card Styling
- **Model A Card:**
  - Border: `1px solid var(--accent-cyan-glow)` (subtle cyan tint).
  - Header Tag: Cyan pill `Model A` (when anonymized) or `[Model Name]` (when revealed).
- **Model B Card:**
  - Border: `1px solid var(--accent-purple-glow)` (subtle purple tint).
  - Header Tag: Purple pill `Model B` (when anonymized) or `[Model Name]` (when revealed).
- **Card Content Area:**
  - Min height: 400px. Max height: 650px.
  - Overflow-y: auto with custom sleek dark scrollbar.
  - Text formatting: Full Markdown support (code blocks with copy button, lists, LaTeX math render).

---

## 3. Voting Bar (`<VotingBar />`)

Positioned directly below the dual battle cards.

### 3.1 Button Specifications
The voting bar contains 4 action buttons, arranged horizontally in a single glass container:

```
[ 👈 Model A Wins ]   [ 🤝 Tie ]   [ 👎 Both Bad ]   [ 👉 Model B Wins ]
```

1. **Model A Wins Button:**
   - Default: Glass button with cyan border on hover.
   - Active / Hover: `background: var(--vote-model-a)`, `color: #000`, `box-shadow: 0 0 16px var(--accent-cyan-glow)`.
2. **Model B Wins Button:**
   - Default: Glass button with purple border on hover.
   - Active / Hover: `background: var(--vote-model-b)`, `color: #fff`, `box-shadow: 0 0 16px var(--accent-purple-glow)`.
3. **Tie Button:**
   - Default: Glass button with emerald border on hover.
   - Active / Hover: `background: var(--vote-tie)`, `color: #000`.
4. **Both Bad Button:**
   - Default: Glass button with rose border on hover.
   - Active / Hover: `background: var(--vote-both-bad)`, `color: #fff`.

### 3.2 State Rules
- **Disabled State:** Disabled while models are actively streaming responses. Includes tooltips explaining: *"Wait for models to finish generating responses..."*.
- **Post-Vote State:** Replaced with revealed model names, Elo delta popups (+15 / -15), and a `[ Next Battle 🔄 ]` button.

---

## 4. Model Selector Dropdown (`<ModelSelector />`)

Selects models for comparison in non-random v1 battle mode.

- **Trigger:** Glass select button showing active model icon + display name + quota status indicator.
- **Status Pills:**
  - 🟢 `Available` (Quota ok)
  - 🟡 `Low Quota` (< 10% remaining)
  - 🔴 `Exhausted` (Disabled in dropdown with tooltip: *"Daily free tier limit reached"*)
- **Dropdown Items:** Grouped by Provider (OpenRouter, Google, Groq, Cerebras, Mistral).

---

## 5. Provider Pill Badges (`<ProviderBadge />`)

Used across Leaderboard, Battle Cards, and Model Selectors.

| Provider | Background Tint | Border / Text Color |
| --- | --- | --- |
| **OpenRouter** | `rgba(99, 102, 241, 0.15)` | `#818cf8` |
| **Google AI Studio** | `rgba(59, 130, 246, 0.15)` | `#60a5fa` |
| **Groq** | `rgba(249, 115, 22, 0.15)` | `#fb923c` |
| **Cerebras** | `rgba(168, 85, 247, 0.15)` | `#c084fc` |
| **Mistral** | `rgba(236, 72, 153, 0.15)` | `#f472b6` |

---

## 6. Prompt Input Bar (`<PromptInputBar />`)

- Fixed or pinned at bottom of Battle and Direct Chat views.
- Glass textarea with auto-resize (max 6 lines).
- Action button: Primary Indigo gradient button `[ Send Battle Prompt ⚡ ]`.
- Keyboard shortcut: `Cmd/Ctrl + Enter` to trigger.
