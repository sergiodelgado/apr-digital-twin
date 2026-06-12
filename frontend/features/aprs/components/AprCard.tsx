"use client";

import Link from "next/link";
import { formatDateTime } from "@/lib/format";
import type { AvailableAPRRecord } from "@/lib/types";
import { Card } from "@/components/ui/primitives";

export function AprCard({ apr }: { apr: AvailableAPRRecord }) {
  return (
    <Link href={`/aprs/${apr.apr_id}`}>
      <Card className="cursor-pointer transition-colors hover:border-sky-500/50 hover:shadow-sky-500/10">
        <p className="text-xl font-bold text-foreground">{apr.apr_id}</p>
        <dl className="mt-3 space-y-1.5 text-sm">
          <div className="flex justify-between">
            <dt className="text-muted">Telemetry records</dt>
            <dd className="font-medium text-foreground">{apr.telemetry_records}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted">Last telemetry</dt>
            <dd className="font-medium text-foreground">
              {apr.last_telemetry_timestamp
                ? formatDateTime(apr.last_telemetry_timestamp)
                : "—"}
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted">KPI records</dt>
            <dd className="font-medium text-foreground">{apr.kpi_records}</dd>
          </div>
        </dl>
      </Card>
    </Link>
  );
}
