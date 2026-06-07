import { describe, it, expect } from "vitest";
import {
  buildAlertSummaries,
  buildExecutiveSummary,
  buildIncidents,
  buildChartSeries,
} from "../lib/telemetry";
import type { TelemetryRecord, DailyKPIRecord, TwinState } from "../lib/types";

// Mock constant values to align with lib/constants.ts thresholds
// PRESSURE_MIN_BAR = 1.5, TANK_LOW_PCT = 25.0, TURBIDITY_ALERT_NTU = 2.0

const mockTelemetry: TelemetryRecord[] = [
  {
    timestamp: "2026-06-07T08:00:00Z",
    flow_lps: 5.0,
    pressure_bar: 2.0,      // Normal
    tank_level_pct: 50.0,   // Normal
    turbidity_ntu: 1.0,     // Normal
  },
  {
    timestamp: "2026-06-07T08:05:00Z",
    flow_lps: 5.0,
    pressure_bar: 1.2,      // Low (< 1.5) -> Event Start
    tank_level_pct: 20.0,   // Low (< 25) -> Event Start
    turbidity_ntu: 3.5,     // High (> 2.0) -> Event Start
  },
  {
    timestamp: "2026-06-07T08:10:00Z",
    flow_lps: 5.0,
    pressure_bar: 1.3,      // Low (continuing)
    tank_level_pct: 18.0,   // Low (continuing)
    turbidity_ntu: 3.0,     // High (continuing)
  },
  {
    timestamp: "2026-06-07T08:15:00Z",
    flow_lps: 5.0,
    pressure_bar: 2.1,      // Recovered
    tank_level_pct: 55.0,   // Recovered
    turbidity_ntu: 0.8,     // Recovered
  },
];

const mockGold: DailyKPIRecord[] = [
  {
    date: "2026-06-07",
    apr_id: "APR-001",
    avg_flow_lps: 5.0,
    min_pressure_bar: 1.2,
    max_pressure_bar: 2.1,
    pressure_ok_ratio: 0.5,
    min_tank_level_pct: 18.0,
    max_turbidity_ntu: 3.5,
    completeness_pct: 100.0,
    imputed_pct: 0.0,
    low_pressure_duration_minutes: 10.0,
    high_turbidity_duration_minutes: 10.0,
  },
];

const mockTwin: TwinState = {
  apr_id: "APR-001",
  status: "WARNING",
  freshness_status: "FRESH",
  data_age_minutes: 5,
  evaluated_at: "2026-06-07T08:15:00Z",
  current_flow_lps: 5.0,
  current_pressure_bar: 2.1,
  current_tank_level_pct: 55.0,
  current_turbidity_ntu: 0.8,
  pressure_compliance_ratio: 0.96,
  hydraulic_risk: "LOW",
  water_quality_risk: "LOW",
  possible_root_cause: "Operation normal",
  recommendation: "Routine check",
  reason_codes: [],
};

describe("buildAlertSummaries", () => {
  it("computes active alerts, events count and severity correctly", () => {
    const alerts = buildAlertSummaries(mockTelemetry, mockGold, mockTwin);
    expect(alerts).toHaveLength(4);

    const pressureAlert = alerts.find((a) => a.key === "pressure");
    expect(pressureAlert).toBeDefined();
    // 1 start of low pressure event (going from 2.0 to 1.2)
    expect(pressureAlert?.events).toBe(1);
    expect(pressureAlert?.maxSeverity).toBe("WARNING"); // pressure 1.2 is WARNING, < 1.0 is CRITICAL
    expect(pressureAlert?.activeNow).toBe(false); // mockTwin says 2.1 now

    const tankAlert = alerts.find((a) => a.key === "tank");
    expect(tankAlert).toBeDefined();
    expect(tankAlert?.events).toBe(1);
    expect(tankAlert?.maxSeverity).toBe("WARNING"); // 18.0% is WARNING (<= 15% is CRITICAL)
    expect(tankAlert?.activeNow).toBe(false);

    const waterAlert = alerts.find((a) => a.key === "water");
    expect(waterAlert).toBeDefined();
    expect(waterAlert?.events).toBe(1);
    expect(waterAlert?.maxSeverity).toBe("WARNING"); // 3.5 NTU is WARNING (>= 5.0 NTU is CRITICAL)
    expect(waterAlert?.activeNow).toBe(false);
  });
});

describe("buildExecutiveSummary", () => {
  it("structures executive metrics with correct tones and labels", () => {
    const metrics = buildExecutiveSummary(mockTelemetry, mockGold, mockTwin);
    expect(metrics).toHaveLength(4);

    const pressureMetric = metrics.find((m) => m.label === "Cumplimiento de presión");
    expect(pressureMetric).toBeDefined();
    expect(pressureMetric?.value).toBe("96.0%"); // From mockTwin compliance ratio (0.96)
    expect(pressureMetric?.tone).toBe("OK"); // 96% >= 95% is OK

    const tankMetric = metrics.find((m) => m.label === "Riesgo de estanque");
    expect(tankMetric).toBeDefined();
    expect(tankMetric?.value).toBe("Medio"); // Min level is 18% -> TANK_LOW_PCT (25%) down to TANK_CRITICAL_PCT (15%) is WARNING/Medio
    expect(tankMetric?.tone).toBe("WARNING");

    const qualityMetric = metrics.find((m) => m.label === "Riesgo de calidad de agua");
    expect(qualityMetric).toBeDefined();
    expect(qualityMetric?.value).toBe("Medio"); // Max turbidity is 3.5 -> > 2.0 and < 5.0 is WARNING/Medio
    expect(qualityMetric?.tone).toBe("WARNING");

    const completenessMetric = metrics.find((m) => m.label === "Completitud de datos");
    expect(completenessMetric).toBeDefined();
    expect(completenessMetric?.value).toBe("100.0%");
    expect(completenessMetric?.tone).toBe("OK");
  });
});

describe("buildIncidents", () => {
  it("builds a list of incidents from threshold crossings", () => {
    const incidents = buildIncidents(mockTelemetry);
    // 2 timestamps (08:05, 08:10) have crossings. Each has pressure, tank, turbidity.
    // So we expect 6 incidents in total.
    expect(incidents.length).toBe(6);

    // Let's verify the fields of the first incident
    const first = incidents[0];
    expect(first).toHaveProperty("timestamp");
    expect(first).toHaveProperty("event");
    expect(first).toHaveProperty("severity");
    expect(first).toHaveProperty("observedValue");
    expect(first).toHaveProperty("threshold");

    // All should be WARNING severity since they don't cross CRITICAL thresholds in mock
    incidents.forEach((inc) => {
      expect(inc.severity).toBe("WARNING");
    });
  });
});

describe("buildChartSeries", () => {
  it("sorts and structures points correctly for small datasets", () => {
    const series = buildChartSeries(mockTelemetry);
    expect(series).toHaveLength(mockTelemetry.length);
    expect(series[0].pressure).toBe(2.0);
    expect(series[0].tank).toBe(50.0);
    expect(series[0].turbidity).toBe(1.0);
  });

  it("downsamples datasets that exceed the maximum allowed points", () => {
    // MAX_CHART_POINTS is 600, so we generate 800 items to trigger downsampling
    const largeTelemetry: TelemetryRecord[] = Array.from({ length: 800 }, (_, i) => ({
      timestamp: new Date(1770000000000 + i * 60000).toISOString(),
      flow_lps: 5.0,
      pressure_bar: i % 2 === 0 ? 2.0 : 1.0,
      tank_level_pct: 50.0,
      turbidity_ntu: 1.0,
    } as any));

    const series = buildChartSeries(largeTelemetry);
    expect(series.length).toBeLessThanOrEqual(600);
    expect(series.length).toBeGreaterThan(0);
  });
});
