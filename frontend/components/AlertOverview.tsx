"use client";

import type { AlertSummary, Severity } from "@/lib/telemetry";
import { Badge, Card } from "./ui/primitives";

const SEVERITY_ES: Record<Severity, string> = {
  OK: "OK",
  WARNING: "Advertencia",
  CRITICAL: "Crítica",
};

function AlertCard({ summary }: { summary: AlertSummary }) {
  return (
    <Card className="h-full">
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-semibold text-foreground">{summary.title}</h4>
        <Badge tone={summary.activeNow ? "CRITICAL" : "OK"}>
          {summary.activeNow ? "ACTIVA" : "DESPEJADA"}
        </Badge>
      </div>
      <dl className="mt-3 space-y-1.5 text-sm">
        <div className="flex justify-between">
          <dt className="text-muted">Eventos en el rango</dt>
          <dd className="font-medium text-foreground">{summary.events}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted">Severidad máxima</dt>
          <dd>
            <Badge tone={summary.maxSeverity}>{SEVERITY_ES[summary.maxSeverity]}</Badge>
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted">Duración</dt>
          <dd className="font-medium text-foreground">{summary.durationLabel}</dd>
        </div>
      </dl>
    </Card>
  );
}

export function AlertOverview({ summaries }: { summaries: AlertSummary[] }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {summaries.map((s) => (
        <AlertCard key={s.key} summary={s} />
      ))}
    </div>
  );
}
