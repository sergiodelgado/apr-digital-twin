'use client';

import type { ReactNode } from 'react';
import { formatDateTime } from '@/lib/format';
import { SEVERITY_ES } from '@/lib/i18n';
import { Badge, Card } from '@/components/ui/primitives';
import type { Incident } from '../types';

/** Column definition for the incidents table. */
interface Column {
  header: string;
  className: string;
  render: (inc: Incident) => ReactNode;
}

/** Column definitions driving both the header row and all data cells. */
const COLUMNS: Column[] = [
  { header: 'Marca temporal', className: 'text-muted',               render: (inc) => formatDateTime(inc.timestamp) },
  { header: 'Evento',         className: 'text-foreground',          render: (inc) => inc.event },
  { header: 'Severidad',      className: '',                         render: (inc) => <Badge tone={inc.severity}>{SEVERITY_ES[inc.severity]}</Badge> },
  { header: 'Valor observado', className: 'font-medium text-foreground', render: (inc) => inc.observedValue },
  { header: 'Umbral',         className: 'text-muted',               render: (inc) => inc.threshold },
];

/**
 * Scrollable table of threshold-crossing incidents, sorted by severity (CRITICAL first)
 * then by descending timestamp within each severity tier.
 *
 * Shows a green empty-state message when no incidents were detected in the selected window.
 * Row count is capped at MAX_INCIDENT_ROWS by the upstream `buildIncidents` transform.
 *
 * @param incidents - Incident array produced by `buildIncidents`.
 */
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
              {COLUMNS.map((col) => (
                <th key={col.header} className="px-4 py-3 font-medium">{col.header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {incidents.map((inc, i) => (
              <tr
                key={`${inc.timestamp}-${inc.event}-${i}`}
                className="border-t border-border/60 hover:bg-surface-2/50"
              >
                {COLUMNS.map((col) => (
                  <td key={col.header} className={`px-4 py-2.5 ${col.className}`}>
                    {col.render(inc)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
