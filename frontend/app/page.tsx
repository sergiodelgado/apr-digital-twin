'use client';

import { AprCard } from '@/features/aprs/components/AprCard';
import { useAvailableAprs } from '@/features/aprs/hooks/useAvailableAprs';
import { StatusPanel } from '@/components/ui/primitives';

/**
 * APR list page — entry point of the application.
 * Fetches all available APR records and renders a navigable grid of AprCard components.
 * Shows loading and error states while the catalog is resolving.
 */
export default function AprListPage() {
  const { data: aprs, error, isLoading, mutate } = useAvailableAprs();

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
        <StatusPanel
          title="Catálogo no disponible"
          message="No se pudo conectar a la API del gemelo digital. Verifica que FastAPI esté disponible en el puerto 8000."
          tone="ERROR"
          onRetry={() => void mutate()}
        />
      ) : isLoading ? (
        <LoadingBox message="Cargando APRs disponibles…"/>
      ) : !aprs || aprs.length === 0 ? (
        <StatusPanel
          title="Sin sistemas APR"
          message="No se encontraron datos. Ejecuta scripts/run_mvp.py para generar telemetría."
          tone="WARNING"
        />
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
