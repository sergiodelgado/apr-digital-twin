'use client';

import Link from 'next/link';
import { AlertOverview } from '@/features/twin-state/components/AlertOverview';
import { ExecutiveSummary } from '@/features/twin-state/components/ExecutiveSummary';
import { OperationalSnapshot } from '@/features/twin-state/components/OperationalSnapshot';
import { RecommendationCard } from '@/features/twin-state/components/RecommendationCard';
import { IncidentsTable } from '@/features/telemetry/components/IncidentsTable';
import { RawTelemetry } from '@/features/telemetry/components/RawTelemetry';
import { TrendChart } from '@/features/telemetry/components/TrendChart';
import { Section, StatusPanel } from '@/components/ui/primitives';
import {
  PRESSURE_MAX_BAR,
  PRESSURE_MIN_BAR,
  TANK_CRITICAL_PCT,
  TANK_LOW_PCT,
  TURBIDITY_ALERT_NTU,
  TURBIDITY_CRITICAL_NTU,
} from '@/lib/constants';
import { useControlRoom } from '../hooks/useControlRoom';
import { FiltersBar } from './FiltersBar';

/**
 * Client component that renders the full APR operational control room.
 *
 * Delegates all data fetching, filter state management, and memoized transforms
 * to the `useControlRoom` hook. Renders a loading placeholder until the twin state
 * is available, then shows the full dashboard layout.
 *
 * @param aprId - APR identifier forwarded from the Server Component route params.
 */
export function ControlRoomView({ aprId }: { aprId: string }) {
  const {
    filters,
    bounds,
    catalogError,
    catalogLoading,
    twin,
    twinError,
    twinLoading,
    tel,
    telLoading,
    telemetryError,
    kpisError,
    chartData,
    alertSummaries,
    execSummary,
    incidents,
    handleFilterChange,
    retryCatalog,
    retryTwin,
    retryHistory,
  } = useControlRoom(aprId);

  const historyError = telemetryError || kpisError;
  const hasDateRange = Boolean(filters.startDate && filters.endDate);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-5">
        <div>
          <Link
            href="/"
            className="mb-2 inline-flex text-sm font-medium text-sky-300 transition-colors hover:text-sky-200"
          >
            Volver al catálogo
          </Link>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {aprId}
          </h1>
          <p className="text-sm text-muted">
            Gemelo digital · monitoreo y recomendación operacional
          </p>
        </div>
      </header>

      <div className="space-y-8">
        {catalogError ? (
          <StatusPanel
            title="Cobertura histórica no disponible"
            message="El estado actual del gemelo sigue accesible. Selecciona un rango manual para consultar históricos o reintenta el catálogo."
            tone="WARNING"
            onRetry={retryCatalog}
          />
        ) : null}

        <FiltersBar filters={filters} bounds={bounds} onChange={handleFilterChange} />

        {!catalogLoading && !bounds && !hasDateRange ? (
          <StatusPanel
            title="Selecciona un rango de fechas"
            message="No hay cobertura automática disponible para este APR. Define las fechas para cargar telemetría y KPI."
          />
        ) : null}

        {twinError ? (
          <StatusPanel
            title="Estado del gemelo no disponible"
            message="La API no pudo entregar el estado operacional de este APR."
            tone="ERROR"
            onRetry={retryTwin}
          />
        ) : twinLoading ? (
          <LoadingBox message="Cargando estado del gemelo…" />
        ) : twin ? (
          <>
            <Section title="Panorama operacional">
              <OperationalSnapshot twin={twin} />
            </Section>

            <RecommendationCard twin={twin} />

            {historyError ? (
              <StatusPanel
                title="Históricos parcialmente disponibles"
                message="Falló la carga de telemetría o KPI para el rango seleccionado. El estado actual permanece visible."
                tone="WARNING"
                onRetry={retryHistory}
              />
            ) : null}

            <Section
              title="Situación de alertas"
              subtitle="Resumen por dimensión en el rango seleccionado"
            >
              <AlertOverview summaries={alertSummaries} />
            </Section>

            <Section title="Resumen ejecutivo">
              <ExecutiveSummary metrics={execSummary} />
            </Section>

            <Section
              title="Tendencias operacionales"
              subtitle={
                telLoading ? 'Actualizando series…' : `${chartData.length} puntos graficados`
              }
            >
              <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
                <TrendChart
                  title="Presión"
                  data={chartData}
                  dataKey="pressure"
                  color="#38bdf8"
                  unit="bar"
                  thresholds={[
                    { value: PRESSURE_MIN_BAR, label: 'mín', color: '#f43f5e' },
                    { value: PRESSURE_MAX_BAR, label: 'máx', color: '#64748b' },
                  ]}
                />
                <TrendChart
                  title="Nivel de estanque"
                  data={chartData}
                  dataKey="tank"
                  color="#34d399"
                  unit="%"
                  thresholds={[
                    { value: TANK_LOW_PCT, label: 'bajo', color: '#f59e0b' },
                    { value: TANK_CRITICAL_PCT, label: 'crítico', color: '#f43f5e' },
                  ]}
                />
                <TrendChart
                  title="Turbidez"
                  data={chartData}
                  dataKey="turbidity"
                  color="#a78bfa"
                  unit="NTU"
                  thresholds={[
                    { value: TURBIDITY_ALERT_NTU, label: 'alerta', color: '#f59e0b' },
                    { value: TURBIDITY_CRITICAL_NTU, label: 'crítico', color: '#f43f5e' },
                  ]}
                />
              </div>
            </Section>

            <Section title="Incidentes y eventos">
              <IncidentsTable incidents={incidents} />
            </Section>

            <Section title="Detalle técnico">
              <RawTelemetry telemetry={tel} />
            </Section>
          </>
        ) : null}
      </div>

      <footer className="mt-10 border-t border-border pt-4 text-center text-xs text-muted">
        Gemelo Digital APR · MVP local · datos vía API FastAPI
      </footer>
    </div>
  );
}

/**
 * Full-width loading placeholder displayed while the twin state is initializing.
 * @param message - Spanish loading message shown to the operator.
 */
function LoadingBox({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center rounded-xl border border-border bg-surface/60 p-12 text-sm text-muted">
      {message}
    </div>
  );
}
