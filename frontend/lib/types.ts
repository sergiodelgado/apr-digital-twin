/**
 * Mirror types of `src/apr_twin/schemas.py (FastAPI Pydantic models).
 * Keep in sync when backend schemas change.
 */

/**
 * UI-level severity shared across features.
 */
export type Severity = 'OK' | 'WARNING' | 'CRITICAL';

export type SystemStatus = 'OK' | 'WARNING' | 'CRITICAL' | 'NO_DATA';
export type FreshnessStatus = 'FRESH' | 'STALE' | 'OUTDATED' | 'NO_DATA';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type Confidence = 'LOW' | 'MEDIUM' | 'HIGH';
export type HydraulicRisk = 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
export type TankConsistency = 'CONSISTENT' | 'WATCH' | 'INCONSISTENT' | 'UNKNOWN';

export interface HealthResponse {
  status: 'ok' | 'warning';
  bronze_files: number;
  silver_rows: number;
  gold_rows: number;
  last_telemetry_timestamp: string | null;
}

export interface TelemetryRecord {
  timestamp: string;
  apr_id: string;
  sensor_id: string;
  batch_id: string;
  source_file: string;
  processed_at: string;
  flow_lps: number;
  pressure_bar: number;
  tank_level_pct: number;
  turbidity_ntu: number;
  pump_on: boolean;
  pressure_ok: boolean;
  turbidity_alert: boolean;
  is_synthetic: boolean;
}

export interface DailyKPIRecord {
  date: string;
  apr_id: string;
  batch_id: string;
  source_file: string;
  processed_at: string;
  records: number;
  avg_flow_lps: number;
  daily_volume_m3: number;
  avg_pressure_bar: number;
  pressure_ok_ratio: number;
  min_tank_level_pct: number;
  max_tank_level_pct: number;
  pump_runtime_h: number;
  avg_turbidity_ntu: number;
  turbidity_alert_count: number;
  completeness_pct: number;
  imputed_pct: number;
  low_pressure_duration_minutes: number;
  high_turbidity_duration_minutes: number;
  risk_level: RiskLevel;
}

export interface AvailableAPRRecord {
  apr_id: string;
  telemetry_records: number;
  kpi_records: number;
  first_telemetry_timestamp: string | null;
  last_telemetry_timestamp: string | null;
  first_kpi_date: string | null;
  last_kpi_date: string | null;
}

export interface TwinState {
  timestamp: string;
  apr_id: string;
  system_status: SystemStatus;
  current_tank_level_pct: number | null;
  current_pressure_bar: number | null;
  current_turbidity_ntu: number | null;
  pressure_compliance_ratio: number | null;
  daily_volume_m3: number | null;
  data_age_minutes: number | null;
  freshness_status: FreshnessStatus;
  confidence: Confidence;
  confidence_score: number;
  projected_tank_level_2h_pct: number | null;
  observed_tank_trend_pct_per_hour: number | null;
  tank_balance_consistency: TankConsistency;
  hydraulic_risk: HydraulicRisk;
  possible_root_cause: string | null;
  reason_codes: string[];
  operational_recommendation: string | null;
  turbidity_alert_active: boolean;
  active_alerts: string[];
  recommendation_code: string | null;
}
