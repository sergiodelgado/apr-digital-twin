"use client";

import { formatDateTime } from "@/lib/format";
import type { Incident, Severity } from "@/lib/telemetry";
import { Badge, Card } from "./ui/primitives";

const SEVERITY_ES: Record<Severity, string> = {
  OK: "OK",
  WARNING: "Advertencia",
  CRITICAL: "Crítica",
};

export function IncidentsTable({ incidents }: { incidents: Incident[] }) {
  if (incidents.length === 0) {
    return (
      <Card>
        <p className="py-4 text-sm text-emerald-300">
          No se detectaron incidentes en la ventana de tiempo seleccionada.
        </p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="max-h-96 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-surface-2 text-left text-xs uppercase tracking-wide text-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Marca temporal</th>
              <th className="px-4 py-3 font-medium">Evento</th>
              <th className="px-4 py-3 font-medium">Severidad</th>
              <th className="px-4 py-3 font-medium">Valor observado</th>
              <th className="px-4 py-3 font-medium">Umbral</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((inc, i) => (
              <tr
                key={`${inc.timestamp}-${inc.event}-${i}`}
                className="border-t border-border/60 hover:bg-surface-2/50"
              >
                <td className="px-4 py-2.5 text-muted">{formatDateTime(inc.timestamp)}</td>
                <td className="px-4 py-2.5 text-foreground">{inc.event}</td>
                <td className="px-4 py-2.5">
                  <Badge tone={inc.severity}>{SEVERITY_ES[inc.severity]}</Badge>
                </td>
                <td className="px-4 py-2.5 font-medium text-foreground">{inc.observedValue}</td>
                <td className="px-4 py-2.5 text-muted">{inc.threshold}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
