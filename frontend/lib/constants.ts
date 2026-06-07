// Umbrales operacionales — ESPEJO de src/apr_twin/config.py.
// Mantener sincronizado con el backend; se usan para las líneas de umbral de los
// gráficos y para la clasificación de severidad en el cliente (paridad con app.py).

export const PRESSURE_MIN_BAR = 1.5;
export const PRESSURE_MAX_BAR = 4.5;
export const PRESSURE_CRITICAL_BAR = 1.0; // app.py marca CRITICAL bajo 1.0 bar

export const TURBIDITY_ALERT_NTU = 2.0;
export const TURBIDITY_CRITICAL_NTU = 5.0;

export const TANK_LOW_PCT = 30.0;
export const TANK_CRITICAL_PCT = 15.0;

export const FRESHNESS_FRESH_MAX_MINUTES = 15.0;
export const FRESHNESS_STALE_MAX_MINUTES = 60.0;

// Endpoint del proxy same-origin definido en next.config.ts.
export const API_BASE = "/api/apr";

// Máximo de puntos a graficar tras downsampling (rendimiento de Recharts).
export const MAX_CHART_POINTS = 600;

// Máximo de filas en la tabla de incidentes y la telemetría cruda.
export const MAX_INCIDENT_ROWS = 120;
export const MAX_RAW_ROWS = 120;
