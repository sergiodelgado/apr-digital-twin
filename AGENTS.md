# Guía de Agentes de IA para APR Digital Twin (AGENTS.md)

Este archivo proporciona contexto, restricciones arquitectónicas y directrices operacionales críticas para cualquier agente de IA que trabaje en este repositorio.

---

## 1. Contexto del Dominio y del Proyecto

- **Dominio**: Sistemas de Agua Potable Rural (APR) en Chile. Estos sistemas suministran agua a comunidades rurales y están gestionados por comités o cooperativas locales.
- **Problema de Negocio**: Convertir señales de telemetría (presión, caudal, nivel de estanques, turbidez) en información explicable para la toma de decisiones operativas locales.
- **Estado Actual**: MVP local y autocontenido. Utiliza datos sintéticos y almacenamiento en archivos locales de formato Parquet. No se conecta a hardware físico o infraestructura de nube compleja.

---

## 2. Mapa Arquitectónico Clave

- `src/apr_twin/`: Directorio principal del código fuente en Python.
  - [engine.py](file:///Users/maka/WebstormProjects/apr-digital-twin/src/apr_twin/twin/engine.py): Motor del gemelo digital que computa las reglas operacionales, estados (`OK`, `WARNING`, `CRITICAL`), niveles de confianza, causas raíz y recomendaciones.
  - [api/main.py](file:///Users/maka/WebstormProjects/apr-digital-twin/src/apr_twin/api/main.py): API FastAPI que expone datos e información del gemelo digital.
  - [pipelines/](file:///Users/maka/WebstormProjects/apr-digital-twin/src/apr_twin/pipelines/): Procesamiento por lotes local.
    - Bronze: Telemetría cruda en Parquet.
    - Silver ([bronze_to_silver.py](file:///Users/maka/WebstormProjects/apr-digital-twin/src/apr_twin/pipelines/bronze_to_silver.py)): Limpieza, imputación y validaciones de calidad de datos.
    - Gold ([silver_to_gold.py](file:///Users/maka/WebstormProjects/apr-digital-twin/src/apr_twin/pipelines/silver_to_gold.py)): Agregación de KPIs diarios.
  - [dashboard/app.py](file:///Users/maka/WebstormProjects/apr-digital-twin/src/apr_twin/dashboard/app.py): Dashboard heredado en Streamlit (útil para pruebas rápidas de backend).
- `frontend/`: Aplicación moderna en Next.js.
  - Servidor de desarrollo Next.js 16 con React 19 y Tailwind CSS v4.
  - Consume los endpoints de FastAPI y visualiza la telemetría, estados del Twin y recomendaciones.
- `scripts/`: Entrypoints para automatizaciones y demos.
  - [demo_workflow.py](file:///Users/maka/WebstormProjects/apr-digital-twin/scripts/demo_workflow.py): Script de control principal para preparar escenarios de datos sintéticos y lanzar la API/dashboard.

---

## 3. Directrices y Restricciones del Sistema

> [!IMPORTANT]
> **Preservación del Diseño Local-First**: No agregues bases de datos relacionales tradicionales externas (PostgreSQL, MySQL), colas de mensajería (RabbitMQ) o servicios en la nube (AWS/GCP/Azure) a menos que el usuario lo solicite expresamente. La simplicidad de archivos Parquet locales es esencial para el demo portátil.

### Lógica de Reglas y Explicabilidad
- Al refactorizar o añadir reglas al Twin Engine (`engine.py`), asegúrate de que todos los estados retornen explicaciones claras y legibles para humanos:
  - `system_status`: Estado general del sistema (`OK`, `WARNING`, `CRITICAL`).
  - `freshness_status`: Estado de frescura de datos (`FRESH`, `STALE`, `OUTDATED`).
  - `confidence_score` & `confidence`: Nivel de confianza numérico (0.0 a 1.0) y cualitativo.
  - `reason_codes`: Códigos específicos de alertas (ej. `HYDRAULIC_LOW_PRESSURE_WITH_NORMAL_STORAGE`).
  - `possible_root_cause` & `operational_recommendation`: Mensajes de apoyo para el operador rural.

### Desarrollo del Frontend (Next.js & Tailwind CSS v4)
- **Next.js 16**: Esta versión tiene convenciones estrictas y cambios importantes. Consulta la documentación local si encuentras incompatibilidades en APIs o estructuras de archivos heredadas de Next.js 13/14/15.
- **Estilo Visual**: Debe ser premium, limpio e interactivo. Usa las clases de Tailwind v4, animaciones suaves al pasar el ratón (hover), y mantén un diseño responsivo.
- **Tipado estricto**: En TypeScript, evita el uso de `any`. Define contratos claros de interfaz para mapear los payloads que expone la API de FastAPI.

---

## 4. Flujo de Trabajo para Agentes

1. **Investigar**: Antes de modificar código, localiza las pruebas relevantes en `tests/` o `frontend/tests/`.
2. **Desarrollar**: Sigue las guías de `CLAUDE.md`.
3. **Verificar**: Ejecuta `pytest` y `npm --prefix frontend run test:run` para comprobar que las pruebas existentes siguen pasando antes de entregar el trabajo.
4. **Registrar**: Si añades una nueva regla de negocio o escenario, asegúrate de añadir pruebas parametrizadas en `tests/test_scenarios.py` y actualizar el playbook de escenarios si aplica.
