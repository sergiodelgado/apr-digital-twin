<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Frontend Agent Guidelines (AGENTS.md)

This document outlines instructions and architectural rules for AI agents modifying the Next.js frontend.

---

## 1. Project Stack & Environment

- **Framework**: Next.js 16.x (App Router-based, React 19)
- **Styling**: Tailwind CSS v4.0.0 (PostCSS integration)
- **Data Fetching**: SWR (`swr`) for client-side API requests, standard browser fetch
- **Charts**: Recharts (`recharts`) for time-series telemetry metrics and trends
- **Testing**: Vitest + JSDOM + `@testing-library/react`

---

## 2. Directory Layout

- `app/`: Next.js App Router root layout, APR catalog, and dynamic APR routes.
  - `app/layout.tsx`: Root HTML shell and page container.
  - `app/page.tsx`: APR catalog.
  - `app/aprs/[apr_id]/page.tsx`: Per-APR control room route.
  - `app/globals.css`: Tailwind v4 import directives.
- `features/`: Domain-owned components, hooks, types, and transforms.
  - `features/aprs/`: APR catalog and coverage.
  - `features/control-room/`: Dashboard composition and orchestration.
  - `features/telemetry/`: Historical views and transforms.
  - `features/twin-state/`: Explainable Twin state and translations.
- `components/ui/`: Reusable stateless primitives.
- `lib/`: Helper libraries and utilities.
  - `lib/format.ts`: Data localization and display helpers (Spanish/es-CL locale for Chile).
- `tests/`: Automated test suite using Vitest.

---

## 3. Core Architectural Rules

### 1. React 19 & Next.js 16 Compatibility
- Next.js 16 uses React 19. Ensure you follow new React hooks conventions and do not use deprecated React or Next.js APIs.
- Components that require client-side hooks like `useState`, `useEffect`, `useMemo`, or SWR **must** start with the `"use client"` directive.

### 2. Premium Design Principles (Tailwind CSS v4)
- Maintain a highly aesthetic dashboard interface.
- Avoid generic colors. Use HSL-mapped variables or specific Tailwind v4 palettes.
- Apply glassmorphism components (`backdrop-blur-md bg-white/70` or dark-mode equivalents).
- Standardize on cards with `rounded-xl` / `rounded-2xl` and subtle shadows.
- Include transition effects for interactive actions (`transition-all duration-200 ease-in-out hover:scale-[1.01]`).

### 3. Localization & Domain Semantics
- The interface language is **Spanish** (since the user/domain is Chilean APR).
- All numbers, dates, and units must be formatted using `lib/format.ts` which uses the Chilean locale (`es-CL`) for numbers (`1.234,5` instead of `1,234.5`) and dates.
- Use correct hydraulic units: pressure in `bar` or `m.c.a.`, flow in `L/s` (litros por segundo), tank levels in `%`.

---

## 4. Verification Flow

- Always run linting:
  ```bash
  npm run lint
  ```
- Always execute tests to prevent regressions:
  ```bash
  npm run test:run
  ```
- If creating new visual elements, verify rendering in JSDOM tests if applicable, or write unit tests under `tests/`.
