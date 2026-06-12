"use client";

import { AlertOverview } from "@/features/twin-state/components/AlertOverview";
import { ExecutiveSummary } from "@/features/twin-state/components/ExecutiveSummary";
import { OperationalSnapshot } from "@/features/twin-state/components/OperationalSnapshot";
import { RecommendationCard } from "@/features/twin-state/components/RecommendationCard";
import { IncidentsTable } from "@/features/telemetry/components/IncidentsTable";
import { RawTelemetry } from "@/features/telemetry/components/RawTelemetry";
import { TrendChart } from "@/features/telemetry/components/TrendChart";
import { Section } from "@/components/ui/primitives";
import {
  PRESSURE_MAX_BAR,
  PRESSURE_MIN_BAR,
  TANK_CRITICAL_PCT,
  TANK_LOW_PCT,
  TURBIDITY_ALERT_NTU,
  TURBIDITY_CRITICAL_NTU,
} from "@/lib/constants";
import { useControlRoom } from "../hooks/useControlRoom";
import { FiltersBar } from "./FiltersBar";

export function ControlRoomView({ aprId }: { aprId: string }) {
  const {
    filters,
    bounds,
    twin,
    tel,
    telLoading,
    chartData,
    alertSummaries,
    execSummary,
    incidents,
    handleFilterChange,
  } = useControlRoom(aprId);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {aprId}
          </h1>
          <p className="text-sm text-muted">
            Gemelo digital · monitoreo y recomendación operacional
          </p>
        </div>
      </header>

      <div className="space-y-8">
        <FiltersBar filters={filters} bounds={bounds} onChange={handleFilterChange} />

        {!twin ? (
          <LoadingBox message="Cargando estado del gemelo…" />
        ) : (
          <>
            <Section title="Panorama operacional">
              <OperationalSnapshot twin={twin} />
            </Section>

            <RecommendationCard twin={twin} />

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
                telLoading ? "Actualizando series…" : `${chartData.length} puntos graficados`
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
                    { value: PRESSURE_MIN_BAR, label: "mín", color: "#f43f5e" },
                    { value: PRESSURE_MAX_BAR, label: "máx", color: "#64748b" },
                  ]}
                />
                <TrendChart
                  title="Nivel de estanque"
                  data={chartData}
                  dataKey="tank"
                  color="#34d399"
                  unit="%"
                  thresholds={[
                    { value: TANK_LOW_PCT, label: "bajo", color: "#f59e0b" },
                    { value: TANK_CRITICAL_PCT, label: "crítico", color: "#f43f5e" },
                  ]}
                />
                <TrendChart
                  title="Turbidez"
                  data={chartData}
                  dataKey="turbidity"
                  color="#a78bfa"
                  unit="NTU"
                  thresholds={[
                    { value: TURBIDITY_ALERT_NTU, label: "alerta", color: "#f59e0b" },
                    { value: TURBIDITY_CRITICAL_NTU, label: "crítico", color: "#f43f5e" },
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
        )}
      </div>

      <footer className="mt-10 border-t border-border pt-4 text-center text-xs text-muted">
        Gemelo Digital APR · MVP local · datos vía API FastAPI
      </footer>
    </div>
  );
}

function LoadingBox({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center rounded-xl border border-border bg-surface/60 p-12 text-sm text-muted">
      {message}
    </div>
  );
}
