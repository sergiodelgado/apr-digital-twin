'use client';

import type { ReactNode } from 'react';
import { MAX_RAW_ROWS } from '@/lib/constants';
import { formatDateTime, formatNumber } from '@/lib/format';
import type { TelemetryRecord } from '@/lib/types';
import { Card } from '@/components/ui/primitives';

/** Column definition for the raw telemetry table. */
interface Column {
  header: string;
  className: string;
  render: (r: TelemetryRecord) => ReactNode;
}

/** Column definitions driving both the header row and all data cells. */
const COLUMNS: Column[] = [
  { header: 'Marca temporal', className: 'text-muted', render: (r) => formatDateTime(r.timestamp) },
  { header: 'Sensor', className: 'text-muted', render: (r) => r.sensor_id },
  { header: 'Caudal (L/s)', className: 'text-foreground', render: (r) => formatNumber(r.flow_lps, 2) },
  { header: 'Presión (bar)', className: 'text-foreground', render: (r) => formatNumber(r.pressure_bar, 2) },
  { header: 'Estanque (%)', className: 'text-foreground', render: (r) => formatNumber(r.tank_level_pct, 1) },
  { header: 'Turbidez (NTU)', className: 'text-foreground', render: (r) => formatNumber(r.turbidity_ntu, 2) },
  { header: 'Bomba', className: 'text-muted', render: (r) => r.pump_on ? 'ON' : 'OFF' },
];

/**
 * Collapsible table showing the most recent raw telemetry rows, sorted newest-first.
 *
 * Intended as a secondary diagnostic view — operators can expand it to inspect raw
 * sensor readings when the higher-level summaries need corroboration.
 * Row count is capped at MAX_RAW_ROWS for rendering performance.
 *
 * @param telemetry - Raw telemetry array from `useTelemetry`.
 */
export function RawTelemetry({ telemetry }: { telemetry: TelemetryRecord[] }) {
  const rows = [...telemetry]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, MAX_RAW_ROWS);

  return (
    <Card className="p-0">
      <details className="group">
        <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-foreground">
          <span className="inline-block transition-transform group-open:rotate-90">▸</span>{' '}
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
                {COLUMNS.map((col) => (
                  <th key={col.header} className="px-3 py-2 font-medium">{col.header}</th>
                ))}
              </tr>
              </thead>
              <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.timestamp}-${i}`} className="border-t border-border/40">
                  {COLUMNS.map((col) => (
                    <td key={col.header} className={`px-3 py-2 ${col.className}`}>
                      {col.render(r)}
                    </td>
                  ))}
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
