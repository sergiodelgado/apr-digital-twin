"use client";

import type { AvailableAPRRecord } from "@/lib/types";

export interface Filters {
  aprId: string | null;
  startDate: string; // yyyy-mm-dd
  endDate: string; // yyyy-mm-dd
}

export function FiltersBar({
  aprs,
  filters,
  bounds,
  onChange,
}: {
  aprs: AvailableAPRRecord[];
  filters: Filters;
  bounds: { min: string; max: string } | null;
  onChange: (next: Filters) => void;
}) {
  return (
    <div className="flex flex-wrap items-end gap-4 rounded-xl border border-border bg-surface/80 p-4 backdrop-blur">
      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-muted">APR en operación</span>
        <select
          value={filters.aprId ?? ""}
          onChange={(e) => onChange({ ...filters, aprId: e.target.value })}
          className="min-w-44 rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-foreground outline-none focus:border-sky-500"
        >
          {aprs.map((apr) => (
            <option key={apr.apr_id} value={apr.apr_id}>
              {apr.apr_id}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-muted">Desde</span>
        <input
          type="date"
          value={filters.startDate}
          min={bounds?.min}
          max={filters.endDate || bounds?.max}
          onChange={(e) => onChange({ ...filters, startDate: e.target.value })}
          className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-foreground outline-none focus:border-sky-500 [color-scheme:dark]"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-xs uppercase tracking-wide text-muted">Hasta</span>
        <input
          type="date"
          value={filters.endDate}
          min={filters.startDate || bounds?.min}
          max={bounds?.max}
          onChange={(e) => onChange({ ...filters, endDate: e.target.value })}
          className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-foreground outline-none focus:border-sky-500 [color-scheme:dark]"
        />
      </label>

      {bounds ? (
        <p className="ml-auto text-xs text-muted">
          Cobertura de datos: {bounds.min} → {bounds.max}
        </p>
      ) : null}
    </div>
  );
}
