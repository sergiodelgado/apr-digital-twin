# Guía de Desarrollo de APR Digital Twin (CLAUDE.md)

Este archivo define las convenciones de código, comandos comunes de construcción, pruebas y ejecución tanto para el backend (Python) como para el frontend (Next.js) en este proyecto.

## Comandos Comunes de Desarrollo

### Backend (Python)

- **Instalación en modo editable**:
  ```bash
  python -m pip install -e .
  ```
- **Preparar escenario de datos sintéticos**:
  ```bash
  python scripts/demo_workflow.py prepare --scenario <scenario_name> --apr-id <apr_id>
  # Ejemplo:
  python scripts/demo_workflow.py prepare --scenario normal --apr-id APR-001
  ```
- **Ejecutar API FastAPI**:
  ```bash
  python scripts/demo_workflow.py api --port 8000
  # O ejecución directa con uvicorn:
  uvicorn apr_twin.api.main:app --reload --port 8000
  ```
- **Ejecutar Streamlit Dashboard**:
  ```bash
  python scripts/demo_workflow.py dashboard --port 8501
  # O ejecución directa con streamlit:
  python -m streamlit run src/apr_twin/dashboard/app.py
  ```
- **Ejecutar pruebas unitarias**:
  ```bash
  pytest
  # O en modo silencioso:
  python -m pytest -q
  ```

### Frontend (Next.js & TypeScript)

- **Instalar dependencias**:
  ```bash
  npm --prefix frontend install
  ```
- **Ejecutar servidor de desarrollo**:
  ```bash
  npm --prefix frontend run dev
  ```
- **Construir para producción**:
  ```bash
  npm --prefix frontend run build
  ```
- **Ejecutar linters**:
  ```bash
  npm --prefix frontend run lint
  ```
- **Ejecutar pruebas (Vitest)**:
  ```bash
  # Modo interactivo:
  npm --prefix frontend run test
  # Ejecución simple de una sola vez:
  npm --prefix frontend run test:run
  ```

---

## Convenciones de Código y Buenas Prácticas

### Backend (Python)

- **Tipado estático**: Se debe usar type hinting estricto en todos los archivos. Usar `from __future__ import annotations` al inicio de cada archivo Python.
- **Nombres y Estilos**:
  - `snake_case` para variables, funciones, métodos y nombres de módulos.
  - `CamelCase` para clases y esquemas de Pydantic.
  - `UPPER_CASE` para constantes.
- **Arquitectura de Datos**:
  - Respetar estrictamente los límites de las capas:
    - **Synthetic**: Solo para generación de datos sintéticos de prueba/escenarios.
    - **Bronze**: Almacenamiento local directo de telemetría cruda en archivos Parquet.
    - **Silver**: Limpieza, deduplicación, validación e imputación de brechas temporales cortas.
    - **Gold**: Consolidación y agregación de KPIs diarios por APR.
    - **Twin Engine**: Lógica de reglas de negocio para evaluar estado de presión, nivel, turbidez, frescura, confianza y recomendaciones operacionales operativas explicables.
  - Toda la persistencia local debe usar formatos Parquet mediante `pandas` y `pyarrow`.
- **Pruebas**:
  - Escribir siempre pruebas en `tests/` para nuevas reglas de negocio o endpoints.
  - Usar `monkeypatch` para anular la variable de entorno `APR_DATA_DIR` a un directorio temporal (`tmp_path`) en las pruebas para no ensuciar los datos de desarrollo.

### Frontend (Next.js / TypeScript / Tailwind v4)

- **Tipado de TypeScript**:
  - Prohibido el uso de `any` sin justificación explícita. Crear interfaces o tipos detallados para los payloads que provienen de la API del Twin.
  - Mantener sincronizados los tipos del frontend con los esquemas de Pydantic definidos en `src/apr_twin/schemas.py`.
- **Componentes de React**:
  - Usar componentes funcionales modernos de React.
  - Diferenciar claramente entre Client Components (`"use client"`) para interactividad y Server Components por defecto.
  - Organizar componentes comunes y de UI reutilizables en `frontend/components/` y subcarpetas lógicas.
- **Estilos (Tailwind CSS v4)**:
  - Usar clases de utilidad de Tailwind CSS v4.
  - Seguir el diseño de estética premium: bordes curvos (`rounded-xl` / `rounded-2xl`), efectos de desenfoque y fondo tipo cristal (glassmorphism/backdrop-filter), degradados sutiles y micro-animaciones en estados hover/active.
  - No usar Tailwind de forma inline desordenada, agrupar de forma limpia y reutilizar variables CSS modernas cuando sea necesario.
- **Manejo de Estado y Peticiones**:
  - Usar la librería `swr` para consultas del lado del cliente hacia la API de FastAPI.
  - Implementar estados correctos de carga (`loading`) y error para todas las llamadas a la API.
