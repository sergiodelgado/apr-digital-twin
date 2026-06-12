"use client";

import { MAX_RAW_ROWS } from "@/lib/constants";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { TelemetryRecord } from "@/lib/types";
import { Card } from "@/components/ui/primitives";

export function RawTelemetry({ telemetry }: { telemetry: TelemetryRecord[] }) {
  const rows = [...telemetry]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, MAX_RAW_ROWS);

  return (
    <Card className="p-0">
      <details className="group">
        <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-foreground">
          <span className="inline-block transition-transform group-open:rotate-90">▸</span>{" "}
          Telemetría cruda (vista secundaria) · {rows.length} filas
        </summary>
        {rows.length === 0 ? (
          <p className="px-4 pb-4 text-sm text-muted">
            No hay telemetría disponible para los filtros seleccionados.
          </p>
        ) : (
          <div className="max-h-96 overflow-auto border-t border-border">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-surface-2 text-left uppercase tracking-wide text-muted">
                <tr>
                  <th className="px-3 py-2 font-medium">Marca temporal</th>
                  <th className="px-3 py-2 font-medium">Sensor</th>
                  <th className="px-3 py-2 font-medium">Caudal (L/s)</th>
                  <th className="px-3 py-2 font-medium">Presión (bar)</th>
                  <th className="px-3 py-2 font-medium">Estanque (%)</th>
                  <th className="px-3 py-2 font-medium">Turbidez (NTU)</th>
                  <th className="px-3 py-2 font-medium">Bomba</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={`${r.timestamp}-${i}`} className="border-t border-border/40">
                    <td className="px-3 py-2 text-muted">{formatDateTime(r.timestamp)}</td>
                    <td className="px-3 py-2 text-muted">{r.sensor_id}</td>
                    <td className="px-3 py-2 text-foreground">{formatNumber(r.flow_lps, 2)}</td>
                    <td className="px-3 py-2 text-foreground">{formatNumber(r.pressure_bar, 2)}</td>
                    <td className="px-3 py-2 text-foreground">{formatNumber(r.tank_level_pct, 1)}</td>
                    <td className="px-3 py-2 text-foreground">{formatNumber(r.turbidity_ntu, 2)}</td>
                    <td className="px-3 py-2 text-muted">{r.pump_on ? "ON" : "OFF"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </details>
    </Card>
  );
}
