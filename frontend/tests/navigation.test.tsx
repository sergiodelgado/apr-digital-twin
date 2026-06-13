import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import AprListPage from '@/app/page';
import AprDetailPage from '@/app/aprs/[apr_id]/page';
import { ControlRoomView } from '@/features/control-room/components/ControlRoomView';
import type { TwinState } from '@/lib/types';

const mocks = vi.hoisted(() => ({
  useAvailableAprs: vi.fn(),
  useControlRoom: vi.fn(),
}));

vi.mock('@/features/aprs/hooks/useAvailableAprs', () => ({
  useAvailableAprs: mocks.useAvailableAprs,
}));

vi.mock('@/features/control-room/hooks/useControlRoom', () => ({
  useControlRoom: mocks.useControlRoom,
}));

vi.mock('@/features/twin-state/components/OperationalSnapshot', () => ({
  OperationalSnapshot: ({ twin }: { twin: TwinState }) => <div>Estado {twin.apr_id}</div>,
}));
vi.mock('@/features/twin-state/components/RecommendationCard', () => ({
  RecommendationCard: () => <div>Recomendación actual</div>,
}));
vi.mock('@/features/twin-state/components/AlertOverview', () => ({
  AlertOverview: () => <div>Alertas</div>,
}));
vi.mock('@/features/twin-state/components/ExecutiveSummary', () => ({
  ExecutiveSummary: () => <div>Resumen</div>,
}));
vi.mock('@/features/telemetry/components/TrendChart', () => ({
  TrendChart: ({ title }: { title: string }) => <div>{title}</div>,
}));
vi.mock('@/features/telemetry/components/IncidentsTable', () => ({
  IncidentsTable: () => <div>Incidentes</div>,
}));
vi.mock('@/features/telemetry/components/RawTelemetry', () => ({
  RawTelemetry: () => <div>Telemetría</div>,
}));

const retryCatalog = vi.fn();
const retryTwin = vi.fn();
const retryHistory = vi.fn();

function controlRoomState(overrides: Record<string, unknown> = {}) {
  return {
    filters: { aprId: 'APR-001', startDate: '', endDate: '' },
    bounds: null,
    catalogError: undefined,
    catalogLoading: false,
    twin: undefined,
    twinError: undefined,
    twinLoading: false,
    tel: [],
    telLoading: false,
    telemetryError: undefined,
    kpisError: undefined,
    chartData: [],
    alertSummaries: [],
    execSummary: [],
    incidents: [],
    handleFilterChange: vi.fn(),
    retryCatalog,
    retryTwin,
    retryHistory,
    ...overrides,
  };
}

const twin = {
  apr_id: 'APR-001',
  system_status: 'OK',
} as TwinState;

describe('APR routes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders catalog entries as links to the dynamic APR route', () => {
    mocks.useAvailableAprs.mockReturnValue({
      data: [{
        apr_id: 'APR-001',
        telemetry_records: 120,
        kpi_records: 3,
        first_telemetry_timestamp: '2026-06-01T00:00:00Z',
        last_telemetry_timestamp: '2026-06-03T00:00:00Z',
        first_kpi_date: '2026-06-01',
        last_kpi_date: '2026-06-03',
      }],
      isLoading: false,
      error: undefined,
      mutate: vi.fn(),
    });

    render(<AprListPage />);

    expect(screen.getByRole('link', { name: /APR-001/i })).toHaveAttribute(
      'href',
      '/aprs/APR-001',
    );
  });

  it('offers a catalog retry after an API failure', () => {
    const mutate = vi.fn();
    mocks.useAvailableAprs.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('offline'),
      mutate,
    });

    render(<AprListPage />);
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Catálogo no disponible');
    expect(mutate).toHaveBeenCalledOnce();
  });

  it('forwards the dynamic route parameter to the control room', async () => {
    const element = await AprDetailPage({ params: Promise.resolve({ apr_id: 'APR-009' }) });

    expect(element.props.aprId).toBe('APR-009');
  });
});

describe('ControlRoomView failure states', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows a recoverable error instead of an infinite Twin loading state', () => {
    mocks.useControlRoom.mockReturnValue(controlRoomState({
      twinError: new Error('twin unavailable'),
    }));

    render(<ControlRoomView aprId="APR-001" />);
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));

    expect(screen.getByRole('alert')).toHaveTextContent('Estado del gemelo no disponible');
    expect(retryTwin).toHaveBeenCalledOnce();
  });

  it('keeps the current Twin visible when the catalog is unavailable', () => {
    mocks.useControlRoom.mockReturnValue(controlRoomState({
      catalogError: new Error('catalog unavailable'),
      twin,
    }));

    render(<ControlRoomView aprId="APR-001" />);

    expect(screen.getByText('Estado APR-001')).toBeInTheDocument();
    expect(screen.getByText('Cobertura histórica no disponible')).toBeInTheDocument();
  });
});
