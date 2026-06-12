# APR Digital Twin — Frontend

Next.js 15 frontend for the APR Digital Twin operational control room. Connects to the local FastAPI backend and displays real-time telemetry, KPI summaries, trend charts, alerts, and explainable twin recommendations for rural drinking water (APR) systems.

## Quick Start

Install dependencies (run from the repo root):

```bash
npm --prefix frontend install
```

Start the development server:

```bash
npm --prefix frontend run dev
```

Open [http://localhost:3000](http://localhost:3000).

The FastAPI backend must be running on port 8000. See the [root README](../README.md) for backend setup.

## Commands

| Command | Description |
|---|---|
| `npm run dev` | Start development server (Turbopack) |
| `npm run build` | Production build |
| `npm run lint` | Run ESLint |
| `npm run test` | Run Vitest in watch mode |
| `npm run test:run` | Run Vitest once |

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS v4 |
| Data fetching | SWR |
| Charts | Recharts |
| Date formatting | date-fns |
| Tests | Vitest + Testing Library |

## Project Structure

```
app/
  layout.tsx          # Root layout — Geist font, global CSS
  page.tsx            # Main dashboard page (Client Component)
components/
  AlertOverview.tsx   # KPI alert cards (pressure, level, quality, telemetry)
  ExecutiveSummary.tsx  # Compliance metric summary cards
  FiltersBar.tsx      # APR selector and date range controls
  IncidentsTable.tsx  # Event and incident log table
  OperationalSnapshot.tsx  # Status chips (connectivity, freshness, etc.)
  RawTelemetry.tsx    # Raw telemetry detail table
  RecommendationCard.tsx   # Twin recommendation with confidence score
  TrendChart.tsx      # Recharts time-series chart wrapper
  ui/
    primitives.tsx    # Shared low-level UI primitives
lib/
  api.ts              # SWR fetchers and API URL helpers
  constants.ts        # Threshold constants and config values
  format.ts           # Number and date formatting utilities
  i18n.ts             # Spanish UI string constants
  telemetry.ts        # Telemetry data transformation helpers
  types.ts            # TypeScript interfaces matching FastAPI schemas
tests/                # Vitest test files
```

## API Integration

The frontend calls the FastAPI backend at `http://localhost:8000` (configured in `lib/api.ts`). Key endpoints consumed:

| Endpoint | Used by |
|---|---|
| `GET /health` | Connectivity status chip |
| `GET /aprs/available` | APR selector dropdown |
| `GET /telemetry/recent?apr_id=` | Trend charts, raw telemetry table |
| `GET /kpis/daily?apr_id=` | Executive summary, KPI cards |
| `GET /twin/state?apr_id=` | Recommendation card, alert overview |

## Type Contract

`lib/types.ts` mirrors the Pydantic schemas in `src/apr_twin/schemas.py`. Keep them in sync when adding or changing API fields.

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for the prioritized feature and architecture plan.
