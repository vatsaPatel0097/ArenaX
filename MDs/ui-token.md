# ArenaX - Design Tokens (ui-token.md)

All UI components across the ArenaX platform MUST strictly utilize the design tokens defined in this document. Do NOT hardcode arbitrary colors, pixel sizes, or inline magic values.

---

## 1. Color Palette Tokens

ArenaX uses a dark, futuristic obsidian color scheme with vibrant neon accents for models, voting states, and rankings.

```css
:root {
  /* ==========================================================================
     Background Colors
     ========================================================================== */
  --bg-dark-obsidian: #080b11;
  --bg-primary: #0d111a;
  --bg-secondary: #131b2e;
  --bg-tertiary: #1a243b;
  --bg-card: rgba(19, 27, 46, 0.75);
  --bg-glass: rgba(15, 23, 42, 0.65);
  --bg-overlay: rgba(8, 11, 17, 0.85);

  /* ==========================================================================
     Border Colors
     ========================================================================== */
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-medium: rgba(255, 255, 255, 0.16);
  --border-highlight: rgba(99, 102, 241, 0.4);
  --border-glass: rgba(255, 255, 255, 0.12);

  /* ==========================================================================
     Text Colors
     ========================================================================== */
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --text-inverse: #0f172a;

  /* ==========================================================================
     Brand & Accent Colors
     ========================================================================== */
  --accent-primary: #6366f1;       /* Indigo */
  --accent-primary-hover: #4f46e5;
  --accent-primary-glow: rgba(99, 102, 241, 0.35);

  --accent-cyan: #06b6d4;          /* Model A Accent */
  --accent-cyan-glow: rgba(6, 182, 212, 0.3);

  --accent-purple: #a855f7;        /* Model B Accent */
  --accent-purple-glow: rgba(168, 85, 247, 0.3);

  --accent-gold: #f59e0b;          /* #1 Rank / Winner */
  --accent-gold-glow: rgba(245, 158, 11, 0.3);

  /* ==========================================================================
     Semantic & Vote State Colors
     ========================================================================== */
  --status-success: #10b981;      /* Tie / Success */
  --status-warning: #f59e0b;      /* Quota Warning */
  --status-danger: #ef4444;       /* Both Bad / Error */
  --status-info: #3b82f6;         /* Information */

  --vote-model-a: #06b6d4;
  --vote-model-b: #a855f7;
  --vote-tie: #10b981;
  --vote-both-bad: #f43f5e;
}
```

---

## 2. Typography Tokens

```css
:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-heading: 'Outfit', var(--font-sans);
  --font-mono: 'Fira Code', 'JetBrains Mono', monospace;

  /* Font Sizes */
  --font-xs: 0.75rem;    /* 12px */
  --font-sm: 0.875rem;   /* 14px */
  --font-base: 1rem;     /* 16px */
  --font-lg: 1.125rem;   /* 18px */
  --font-xl: 1.25rem;    /* 20px */
  --font-2xl: 1.5rem;    /* 24px */
  --font-3xl: 1.875rem;  /* 30px */
  --font-4xl: 2.25rem;   /* 36px */

  /* Font Weights */
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;

  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
}
```

---

## 3. Spacing & Radius Tokens

```css
:root {
  /* Spacing Scale (4px Base Grid) */
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-10: 2.5rem;  /* 40px */
  --space-12: 3rem;    /* 48px */

  /* Border Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;
}
```

---

## 4. Effects, Glassmorphism & Elevation Tokens

```css
:root {
  /* Backdrop Blur */
  --backdrop-blur: blur(12px);
  --backdrop-blur-heavy: blur(24px);

  /* Elevation Shadows */
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.6);
  --shadow-glass: 0 8px 32px 0 rgba(0, 0, 0, 0.37);

  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-bounce: 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

---

## 5. Usage Rules for Design Consistency

1. **No Hardcoded Hex Colors:** Always use `var(--accent-primary)`, `var(--bg-primary)`, etc.
2. **Glassmorphism Rule:** Glass containers must use `background: var(--bg-card); backdrop-filter: var(--backdrop-blur); border: 1px solid var(--border-glass);`.
3. **Model A vs Model B Identity Rule:**
   - Model A elements (badges, borders, glows) MUST use Cyan (`var(--vote-model-a)`).
   - Model B elements MUST use Purple (`var(--vote-model-b)`).
4. **Interactive Focus State Rule:** All interactive elements (inputs, buttons) must outline with `var(--border-highlight)` and a subtle glow on `:focus-visible`.
