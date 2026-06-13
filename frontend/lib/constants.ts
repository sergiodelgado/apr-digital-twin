/**
 * **Operational Thresholds — Mirror of src/apr_twin/config.py.**
 *
 * Must be kept synchronized with the backend; used for rendering threshold lines
 * in charts and for severity classification on the client (parity with app.py).
 */

export const PRESSURE_MIN_BAR = 1.5;
export const PRESSURE_MAX_BAR = 4.5;

/** `app.py` marks CRITICAL below 1.0 bar */
export const PRESSURE_CRITICAL_BAR = 1.0;

export const TURBIDITY_ALERT_NTU = 2.0;
export const TURBIDITY_CRITICAL_NTU = 5.0;

export const TANK_LOW_PCT = 30.0;
export const TANK_CRITICAL_PCT = 15.0;

export const FRESHNESS_FRESH_MAX_MINUTES = 15.0;
export const FRESHNESS_STALE_MAX_MINUTES = 60.0;

/** Same-origin proxy endpoint defined in `next.config.ts`. */
export const API_BASE = '/api/apr';

/** Maximum chart points after downsampling (Recharts performance). */
export const MAX_CHART_POINTS = 600;

/** Maximum incident table and raw telemetry rows. */
export const MAX_INCIDENT_ROWS = 120;
export const MAX_RAW_ROWS = 120;
