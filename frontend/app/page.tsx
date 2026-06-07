"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertOverview } from "@/components/AlertOverview";
import { ExecutiveSummary } from "@/components/ExecutiveSummary";
import { FiltersBar, type Filters } from "@/components/FiltersBar";
import { IncidentsTable } from "@/components/IncidentsTable";
import { OperationalSnapshot } from "@/components/OperationalSnapshot";
import { RawTelemetry } from "@/components/RawTelemetry";
import { RecommendationCard } from "@/components/RecommendationCard";
import { TrendChart } from "@/components/TrendChart";
import { Section } from "@/components/ui/primitives";
import { useAvailableAprs, useDailyKpis, useTelemetry, useTwinState } from "@/lib/api";
import {
  PRESSURE_MAX_BAR,
  PRESSURE_MIN_BAR,
  TANK_CRITICAL_PCT,
  TANK_LOW_PCT,
  TURBIDITY_ALERT_NTU,
  TURBIDITY_CRITICAL_NTU,
} from "@/lib/constants";
import {
  buildAlertSummaries,
  buildChartSeries,
  buildExecutiveSummary,
  buildIncidents,
} from "@/lib/telemetry";
import type { AvailableAPRRecord } from "@/lib/types";

// Límites de fechas (yyyy-mm-dd) cubiertos por un APR, a partir de su catálogo.
function dateBoundsFor(apr: AvailableAPRRecord | undefined): { min: string; max: string } | null {
  if (!apr) return null;
  const candidates = [
    apr.first_telemetry_timestamp,
    apr.last_telemetry_timestamp,
    apr.first_kpi_date,
    apr.last_kpi_date,
  ]
    .filter((v): v is string => Boolean(v))
    .map((v) => v.slice(0, 10));
  if (candidates.length === 0) return null;
  return { min: candidates.reduce((a, b) => (a < b ? a : b)), max: candidates.reduce((a, b) => (a > b ? a : b)) };
}

export default function Home() {
  const { data: aprs, error: aprsError, isLoading: aprsLoading } = useAvailableAprs();
  const [filters, setFilters] = useState<Filters>({ aprId: null, startDate: "", endDate: "" });

  // Inicializa los filtros con el primer APR y su cobertura de fechas.
  useEffect(() => {
    if (!aprs || aprs.length === 0 || filters.aprId) return;
    const first = aprs[0];
    const bounds = dateBoundsFor(first);
    setFilters({
      aprId: first.apr_id,
      startDate: bounds?.min ?? "",
      endDate: bounds?.max ?? "",
    });
  }, [aprs, filters.aprId]);

  const selectedApr = aprs?.find((a) => a.apr_id === filters.aprId);
  const bounds = dateBoundsFor(selectedApr);

  // Al cambiar de APR, reajusta el rango a la cobertura del nuevo APR.
  function handleFilterChange(next: Filters) {
    if (next.aprId !== filters.aprId) {
      const nextBounds = dateBoundsFor(aprs?.find((a) => a.apr_id === next.aprId));
      setFilters({
        aprId: next.aprId,
        startDate: nextBounds?.min ?? next.startDate,
        endDate: nextBounds?.max ?? next.endDate,
      });
      return;
    }
    setFilters(next);
  }

  const telemetryStart = filters.startDate ? `${filters.startDate}T00:00:00` : null;
  const telemetryEnd = filters.endDate ? `${filters.endDate}T23:59:59` : null;

  const { data: twin } = useTwinState(filters.aprId);
  const { data: telemetry, isLoading: telLoading } = useTelemetry(
    filters.aprId,
    telemetryStart,
    telemetryEnd,
  );
  const { data: kpis } = useDailyKpis(filters.aprId, filters.startDate || null, filters.endDate || null);

  const tel = useMemo(() => telemetry ?? [], [telemetry]);
  const gold = useMemo(() => kpis ?? [], [kpis]);

  const alertSummaries = useMemo(() => buildAlertSummaries(tel, gold, twin), [tel, gold, twin]);
  const execSummary = useMemo(() => buildExecutiveSummary(tel, gold, twin), [tel, gold, twin]);
  const incidents = useMemo(() => buildIncidents(tel), [tel]);
  const chartData = useMemo(() => buildChartSeries(tel), [tel]);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Sala de Control Operacional APR
          </h1>
          <p className="text-sm text-muted">
            Gemelo digital para sistemas de Agua Potable Rural · monitoreo y recomendación
          </p>
        </div>
      </header>

      {aprsError ? (
        <ErrorBox message="No se pudo conectar con la API del gemelo digital. Verifica que el servidor FastAPI esté corriendo en :8000." />
      ) : aprsLoading ? (
        <LoadingBox message="Cargando APRs disponibles…" />
      ) : !aprs || aprs.length === 0 ? (
        <ErrorBox message="No se encontraron datos de APR. Ejecuta primero scripts/run_mvp.py para generar telemetría." />
      ) : (
        <div className="space-y-8">
          <FiltersBar
            aprs={aprs}
            filters={filters}
            bounds={bounds}
            onChange={handleFilterChange}
          />

          {!twin ? (
            <LoadingBox message="Cargando estado del gemelo…" />
          ) : (
            <>
              <Section title="Panorama operacional">
                <OperationalSnapshot twin={twin} />
              </Section>

              <RecommendationCard twin={twin} />

              <Section title="Situación de alertas" subtitle="Resumen por dimensión en el rango seleccionado">
                <AlertOverview summaries={alertSummaries} />
              </Section>

              <Section title="Resumen ejecutivo">
                <ExecutiveSummary metrics={execSummary} />
              </Section>

              <Section
                title="Tendencias operacionales"
                subtitle={telLoading ? "Actualizando series…" : `${chartData.length} puntos graficados`}
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
      )}

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

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6 text-sm text-rose-200">
      {message}
    </div>
  );
}
