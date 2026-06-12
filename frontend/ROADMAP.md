# Frontend Roadmap — APR Digital Twin

This roadmap is scoped to the Next.js frontend and aligns with the [project MVP roadmap](../docs/roadmap/roadmap.md). Items are ordered by priority — Near-Term work should be done before the component tree grows further.

---

## Near-Term

### 1. Component test coverage

Only `format.ts` and `telemetry.ts` are currently tested. Extend coverage to:

- React components: `AlertOverview`, `RecommendationCard`, `ExecutiveSummary`
- SWR hooks in `lib/api.ts`: mock responses, assert loading / error / data states
- Edge cases: `null` twin state fields, stale data, empty telemetry arrays

Tests should be co-located with their feature once the feature-based structure (item 5) is in place.

### 2. Demo presentation polish

- Replace text-only loading states with animated skeleton placeholders across all components.
- `RecommendationCard`: render `reason_codes` as styled chips; color-code confidence level (LOW = amber, MEDIUM = blue, HIGH = green).
- `OperationalSnapshot`: visualize `data_age_minutes` with a freshness indicator (green / yellow / red) instead of plain text.
- `TrendChart`: add threshold reference lines for pressure and turbidity limits (constants already defined in `lib/constants.ts`).

### 3. Type contract validation

`constants.ts` mirrors `config.py` and `lib/types.ts` mirrors `schemas.py` — both can drift silently. Add a smoke test that fetches from the live API in CI and asserts critical response fields match the TypeScript interfaces.

### 4. Auto-refresh

SWR has `revalidateOnFocus: false` everywhere and no polling interval. Add a configurable refresh toggle (e.g. every 30 s) surfaced as a UI control — important for live demo sessions where the backend receives new telemetry.

### 5. Feature-based architecture + App Router pages

The current flat `components/` structure and monolithic `page.tsx` will become a maintenance problem as the app grows. Refactor before adding more surface area.

**Target structure:**

```
app/
  layout.tsx
  page.tsx                      # APR list — operational overview per system
  aprs/
    [apr_id]/
      page.tsx                  # APR detail — full control room view
features/
  aprs/                         # APR catalog, selection, availability
    components/                 # AprCard, AprSelector
    hooks/                      # useAvailableAprs
    types.ts
  control-room/                 # Operational dashboard composition
    components/                 # FiltersBar, OperationalSnapshot, ExecutiveSummary
    hooks/                      # useControlRoomData (orchestrates SWR calls)
  telemetry/                    # Charts, incidents, raw data
    components/                 # TrendChart, IncidentsTable, RawTelemetry
    hooks/                      # useTelemetry, useDailyKpis
  twin-state/                   # Explainable twin outputs
    components/                 # RecommendationCard, AlertOverview
    hooks/                      # useTwinState
components/
  ui/                           # Truly shared, stateless primitives only
lib/
  api/                          # Base fetcher and URL helpers — no domain logic
  constants.ts
  format.ts
  types.ts                      # Cross-feature shared types only
```

**Architectural principles applied:**

- **Single Responsibility** — each feature owns its components, hooks, and types; nothing bleeds across feature boundaries.
- **Dependency Inversion** — components receive data via hook interfaces, not coupled directly to SWR or `fetch`.
- **Interface Segregation** — component props carry only what they need; avoid passing full `TwinState` where only `confidence` and `reason_codes` are used.
- **Open/Closed** — UI primitives in `components/ui/` are extended via props composition, never modified for individual feature needs.

### 6. Mobile-responsive layout

Rework the grid layout with Tailwind responsive breakpoints before the component tree grows. The control room should be usable on tablets, which are common in field demos.

Layout contract per feature:
- Mobile: single-column stacked
- Tablet: two-column grid
- Desktop: full dashboard layout

---

## Mid-Term

### 7. Operational report export

"Download report" button that generates a CSV of KPIs + telemetry for the selected APR and date range, using data already in client state — no additional API calls needed.

### 8. Explainability panel

Dedicated section for `reason_codes`, `possible_root_cause`, `hydraulic_risk`, `tank_balance_consistency`, and `projected_tank_level_2h_pct`. Render as a structured diagnostic view with a mini timeline of how alerts evolved over the selected period. Builds on the `twin-state` feature module introduced in item 5.

---

## Long-Term

### 9. Historical comparison mode

Overlay two date ranges on `TrendChart` to contrast normal operation against an anomalous scenario. Directly supports demo storytelling around the scenario library defined in the backend.

### 10. Runtime type safety (Zod)

The `fetcher` in `lib/api/` currently casts responses as `T` with no runtime validation. Introduce Zod schemas that mirror `lib/types.ts` to catch API/frontend schema drift at the network boundary rather than silently consuming malformed data.
