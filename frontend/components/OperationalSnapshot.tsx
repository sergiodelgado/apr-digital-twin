"use client";

import { formatDateTime, formatNumber } from "@/lib/format";
import { FRESHNESS_ES, SYSTEM_STATUS_ES } from "@/lib/i18n";
import type { TwinState } from "@/lib/types";
import { Badge, Card, freshnessTone, systemStatusTone } from "./ui/primitives";

export function OperationalSnapshot({ twin }: { twin: TwinState }) {
  const age = twin.data_age_minutes;
  const ageLabel =
    typeof age === "number" ? `${formatNumber(age, 1)} min de antigüedad` : "Antigüedad no disponible";

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <p className="text-xs uppercase tracking-wide text-muted">Estado operacional</p>
        <div className="mt-2">
          <Badge tone={systemStatusTone(twin.system_status)} className="text-sm">
            {SYSTEM_STATUS_ES[twin.system_status]}
          </Badge>
        </div>
      </Card>

      <Card>
        <p className="text-xs uppercase tracking-wide text-muted">Frescura de datos</p>
        <div className="mt-2">
          <Badge tone={freshnessTone(twin.freshness_status)} className="text-sm">
            {FRESHNESS_ES[twin.freshness_status]}
          </Badge>
        </div>
        <p className="mt-2 text-sm text-muted">{ageLabel}</p>
      </Card>

      <Card>
        <p className="text-xs uppercase tracking-wide text-muted">Última telemetría</p>
        <p className="mt-2 text-lg font-semibold text-foreground">
          {formatDateTime(twin.timestamp)}
        </p>
      </Card>

      <Card>
        <p className="text-xs uppercase tracking-wide text-muted">APR seleccionado</p>
        <p className="mt-2 text-2xl font-bold text-foreground">{twin.apr_id}</p>
      </Card>
    </div>
  );
}
