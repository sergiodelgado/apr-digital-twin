'use client';

import { AprCard } from '@/features/aprs/components/AprCard';
import { useAvailableAprs } from '@/features/aprs/hooks/useAvailableAprs';

/**
 * APR list page — entry point of the application.
 * Fetches all available APR records and renders a navigable grid of AprCard components.
 * Shows loading and error states while the catalog is resolving.
 */
export default function AprListPage() {
  const { data: aprs, error, isLoading } = useAvailableAprs();

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 border-b border-border pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          Sala de Control Operacional APR
        </h1>
        <p className="text-sm text-muted">
          Gemelo digital para Sistemas de Agua Potable Rural · selecciona un APR para continuar
        </p>
      </header>

      {error ? (
        <ErrorBox
          message="No se pudo conectar a la API del gemelo digital. Verifica que el servidor FastAPI esté ejecutándose en :8000."/>
      ) : isLoading ? (
        <LoadingBox message="Cargando APRs disponibles…"/>
      ) : !aprs || aprs.length === 0 ? (
        <ErrorBox
          message="No se encontraron datos APR. Ejecuta scripts/run_mvp.py para generar telemetría."/>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          { aprs.map((apr) => (
            <AprCard key={apr.apr_id} apr={apr}/>
          )) }
        </div>
      )}

      <footer className="mt-10 border-t border-border pt-4 text-center text-xs text-muted">
        Gemelo Digital APR · MVP Local · datos servidos vía FastAPI
      </footer>
    </div>
  );
}

/** Loading placeholder displayed while the APR catalog is being fetched from the API. */
function LoadingBox({ message }: { message: string }) {
  return (
    <div
      className="flex items-center justify-center rounded-xl border border-border bg-surface/60 p-12 text-sm text-muted">
      { message }
    </div>
  );
}

/** Error or empty-state message box. */
function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6 text-sm text-rose-200">
      { message }
    </div>
  );
}
