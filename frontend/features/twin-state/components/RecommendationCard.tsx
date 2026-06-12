"use client";

import { formatPercent } from "@/lib/format";
import { Badge, Card } from "@/components/ui/primitives";
import type { TwinState } from "@/lib/types";
import {
  ALERT_ES,
  CONFIDENCE_ES,
  REASON_CODE_ES,
  RECOMMENDATION_ES,
  ROOT_CAUSE_ES,
  t,
} from "../lib/i18n";

export function RecommendationCard({ twin }: { twin: TwinState }) {
  const recommendation = t(RECOMMENDATION_ES, twin.operational_recommendation);
  const rootCause = t(ROOT_CAUSE_ES, twin.possible_root_cause);
  const alerts = twin.active_alerts ?? [];

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="text-base font-semibold text-foreground">Recomendación operacional</h3>
        <Badge tone="INFO">
          Confianza: {CONFIDENCE_ES[twin.confidence]} · {formatPercent(twin.confidence_score)}
        </Badge>
      </div>

      <p className="mt-3 text-foreground">{recommendation || "Sin recomendación disponible."}</p>

      {rootCause ? (
        <p className="mt-2 text-sm text-muted">
          <span className="font-medium text-foreground/80">Causa probable:</span> {rootCause}
        </p>
      ) : null}

      {twin.reason_codes.length > 0 ? (
        <div className="mt-4">
          <p className="mb-2 text-xs uppercase tracking-wide text-muted">Códigos de razón</p>
          <div className="flex flex-wrap gap-2">
            {twin.reason_codes.map((code) => (
              <Badge key={code} tone="NEUTRAL">
                {REASON_CODE_ES[code] ?? code}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-4">
        <p className="mb-2 text-xs uppercase tracking-wide text-muted">Alertas activas</p>
        {alerts.length > 0 ? (
          <ul className="flex flex-wrap gap-2">
            {alerts.map((alert, i) => (
              <li key={`${alert}-${i}`}>
                <Badge tone="WARNING">{t(ALERT_ES, alert)}</Badge>
              </li>
            ))}
          </ul>
        ) : (
          <Badge tone="OK">Sin alertas activas</Badge>
        )}
      </div>
    </Card>
  );
}
