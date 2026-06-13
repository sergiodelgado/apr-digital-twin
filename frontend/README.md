# APR Digital Twin — Frontend

Next.js 16 frontend for the APR Digital Twin operational control room. Connects to the local FastAPI backend and displays telemetry, KPI summaries, trend charts, alerts, and explainable twin recommendations for rural drinking water (APR) systems.

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
| Framework | Next.js 16 (App Router) |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS v4 |
| Data fetching | SWR |
| Charts | Recharts |
| Date formatting | date-fns |
| Tests | Vitest + Testing Library |

## Project Structure

```
app/
  layout.tsx                    # Root layout and local Geist fonts
  page.tsx                      # APR catalog
  aprs/[apr_id]/page.tsx        # Per-APR control room route
components/ui/                  # Shared stateless UI primitives
features/
  aprs/                         # Catalog, cards, availability hooks
  control-room/                 # Dashboard composition and orchestration
  telemetry/                    # Charts, incidents, raw data and transforms
  twin-state/                   # Twin state, alerts, recommendations and i18n
lib/
  api/fetcher.ts                # Fetcher, query strings and SWR policy
  constants.ts                  # Operational thresholds
  format.ts                     # es-CL number and date formatting
  types.ts                      # Interfaces matching FastAPI schemas
tests/                          # Vitest unit and route-state tests
```

## API Integration

The browser calls the same-origin `/api/apr/*` proxy configured in `next.config.ts`. Next.js forwards requests to `http://127.0.0.1:8000` by default; override it with `APR_API_URL`.

| Endpoint | Used by |
|---|---|
| `GET /health` | Connectivity status chip |
| `GET /available_aprs` | APR catalog and historical date bounds |
| `GET /telemetry/recent?apr_id=` | Trend charts, raw telemetry table |
| `GET /kpis/daily?apr_id=` | Executive summary, KPI cards |
| `GET /twin/state?apr_id=` | Recommendation card, alert overview |

## Type Contract

`lib/types.ts` mirrors the Pydantic schemas in `src/apr_twin/schemas.py`. Keep them in sync when adding or changing API fields.

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for the prioritized feature and architecture plan.
