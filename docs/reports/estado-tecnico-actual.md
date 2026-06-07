# Informe tecnico del estado actual del proyecto APR Digital Twin

Fecha de revision: 2026-06-06  
Audiencia: stakeholders tecnicos  
Alcance: estado tecnico actual del MVP local, basado en evidencia del repositorio

## Resumen ejecutivo

El proyecto APR Digital Twin implementa un MVP local para demostrar un flujo de gemelo digital operacional aplicado a sistemas APR. El sistema genera telemetria sintetica, la procesa en capas Bronze/Silver/Gold, calcula KPIs diarios, evalua el estado operacional mediante reglas explicables y expone resultados a traves de una API FastAPI y un dashboard Streamlit.

Este informe interpreta "estado del arte" como el estado tecnico actual del proyecto, no como una revision academica externa. La evidencia se obtiene desde codigo, documentacion, scripts de demo y pruebas automatizadas. No se asume que `main.py` represente el pipeline real; el flujo se reconstruye desde los modulos y scripts implementados.

## 1. Inventario

### Hechos observados

- El MVP es local-first y file-based: usa procesos Python locales y almacenamiento Parquet bajo `data/`.
- La arquitectura documentada declara el flujo Bronze -> Silver -> Gold -> Twin Engine -> API/Dashboard.
- Los componentes principales estan en `src/apr_twin/`, con modulos separados para generacion sintetica, pipelines, almacenamiento, motor twin, API y dashboard.
- La operacion demo se centraliza en `scripts/demo_workflow.py`, mientras que `scripts/run_mvp.py` cubre la ejecucion batch local.
- La suite de pruebas cubre pipeline, API y escenarios de comportamiento del gemelo.
- El proyecto incluye documentacion en `docs/architecture/`, `docs/demos/`, `docs/operations/` y `docs/roadmap/`.

### Evidencia consultada

- Documentacion base: `README.md`, `CHANGELOG.md`, `docs/architecture/mvp-architecture.md`, `docs/architecture/data-flow.md`.
- Documentacion operacional: `docs/demos/demo-workflow.md`, `docs/demos/scenario-playbook.md`, `docs/operations/runbook.md`.
- Roadmap: `docs/roadmap/roadmap.md`.
- Codigo: `src/apr_twin/config.py`, `src/apr_twin/synthetic/generator.py`, `src/apr_twin/pipelines/bronze_to_silver.py`, `src/apr_twin/pipelines/silver_to_gold.py`, `src/apr_twin/twin/engine.py`, `src/apr_twin/twin/taxonomy.py`, `src/apr_twin/api/main.py`, `src/apr_twin/dashboard/app.py`.
- Pruebas: `tests/test_pipeline.py`, `tests/test_api.py`, `tests/test_scenarios.py`.

### Interpretacion tecnica

El repositorio ya tiene separacion razonable entre datos, transformaciones, logica del gemelo, interfaz API y visualizacion. Para un MVP, el valor tecnico principal esta en la trazabilidad local y en la explicabilidad: los estados y recomendaciones se derivan de reglas, umbrales, frescura de datos, calidad de datos, reason codes y taxonomia operacional.

## 2. Reconstruccion del pipeline

### Hechos observados

El flujo implementado se reconstruye de la siguiente manera:

1. `src/apr_twin/synthetic/generator.py` genera telemetria sintetica en Bronze.
2. `src/apr_twin/pipelines/bronze_to_silver.py` valida, limpia, deduplica, imputa y crea salidas Silver.
3. `src/apr_twin/pipelines/silver_to_gold.py` calcula KPIs diarios y clasifica riesgo operacional.
4. `src/apr_twin/twin/engine.py` calcula estado actual, frescura, confianza, riesgo hidraulico, causa probable y recomendacion.
5. `src/apr_twin/api/main.py` expone endpoints para salud, APRs disponibles, telemetria, KPIs y estado twin.
6. `src/apr_twin/dashboard/app.py` visualiza estado operacional y tendencias, consumiendo datos locales o API.

### Capa Bronze

La generacion sintetica produce registros con timestamp, APR, sensor, caudal, presion, nivel de estanque, turbidez, estado de bomba e indicador sintetico. Tambien soporta escenarios demo, entre ellos:

- `normal`
- `stale_data`
- `low_pressure`
- `high_turbidity`
- `projected_low_tank_level`
- `pump_on_no_recovery`
- `abnormal_tank_drop`
- `low_pressure_with_normal_storage`
- `demand_spike_with_storage_depletion`
- `noisy_or_erratic_tank_sensor`

### Capa Silver

La transformacion Bronze -> Silver valida columnas esperadas, normaliza identificadores, convierte tipos, elimina duplicados por `apr_id`, `sensor_id` y `timestamp`, reemplaza valores fuera de rango por nulos y aplica imputacion lineal acotada por brechas maximas. Las salidas observadas son:

- `data/silver/telemetry_silver.parquet`
- `data/silver/rejected_records.parquet`
- `data/silver/silver_quality_report.json`

El reporte de calidad incluye metricas como filas de entrada, filas Silver, rechazos, duplicados removidos, imputaciones, tasa de rechazo, valores fuera de rango y archivos fuente.

### Capa Gold

La transformacion Silver -> Gold calcula KPIs diarios por APR. Entre las metricas observadas estan:

- volumen diario
- presion promedio
- razon de cumplimiento de presion
- minimos y maximos de nivel de estanque
- horas de operacion de bomba
- turbidez promedio
- conteo y duracion de eventos de turbidez
- completitud
- porcentaje imputado
- duracion de baja presion
- nivel de riesgo `LOW`, `MEDIUM` o `HIGH`

La salida principal es `data/gold/daily_kpis.parquet`.

### Motor twin

El motor twin calcula un estado operacional con:

- `system_status`: `OK`, `WARNING`, `CRITICAL` o `NO_DATA`.
- `freshness_status`: `FRESH`, `STALE`, `OUTDATED` o `NO_DATA`.
- `confidence` y `confidence_score`.
- presion, turbidez, nivel de estanque y volumen diario.
- proyeccion de nivel de estanque a 2 horas.
- tendencia observada del estanque.
- consistencia del balance hidraulico.
- riesgo hidraulico.
- reason codes.
- causa probable.
- recomendacion operacional.

La configuracion de umbrales esta en `src/apr_twin/config.py`. Entre los parametros principales se observan presion minima y maxima, turbidez de alerta y critica, umbrales de estanque bajo/critico, reglas de frescura y umbrales hidraulicos.

### API y dashboard

La API FastAPI expone:

- `GET /health`
- `GET /available_aprs`
- `GET /aprs/available`
- `GET /telemetry/recent`
- `GET /kpis/daily`
- `GET /twin/state`

El dashboard Streamlit permite operar con datos locales Parquet o via API. Incluye seleccion de APR, rango temporal, indicadores de estado, tendencias y resumen de alertas.

## 3. Racionalizacion tecnica

### Capacidades verificadas

- Pipeline local completo desde telemetria sintetica hasta KPIs y estado twin.
- Control de calidad en Silver con rechazos, imputacion limitada y reporte JSON.
- Trazabilidad basica con `batch_id`, `source_file` y `processed_at`.
- Clasificacion de frescura de datos.
- Reason codes y recomendaciones operacionales explicables.
- Escenarios demo para presion, turbidez, datos obsoletos, recuperacion hidraulica, caidas anormales y sensor erratico.
- API local con modelos Pydantic.
- Dashboard con modo local y modo API.
- Pruebas automatizadas verdes: `python -m pytest -q` reporto `13 passed`.

### Limitaciones actuales

- La telemetria es sintetica; no hay integracion implementada con sensores reales.
- La arquitectura no incluye servicios cloud, streaming administrado ni colas/eventos.
- No hay autenticacion, autorizacion ni soporte multi-tenant.
- No existe benchmark formal de volumen, latencia o escalamiento.
- La persistencia esta basada en archivos locales Parquet, adecuada para MVP y demo, pero limitada para operacion productiva multiusuario.
- El dashboard esta orientado a validacion y storytelling tecnico, no a una sala de control productiva.

### Riesgos tecnicos

- Las reglas y umbrales son transparentes, pero requieren calibracion con datos reales de APR antes de uso operacional.
- La calidad de inferencia depende de la continuidad de telemetria; el propio motor reduce confianza frente a frescura baja o datos incompletos.
- La imputacion esta acotada y documentada, pero debe mantenerse auditable si se incorporan datos reales.
- La operacion local facilita reproducibilidad, aunque limita observabilidad, concurrencia y gobierno de datos.

### Propuestas de mejora

- Formalizar ejemplos de contrato API con payloads esperados para todos los endpoints principales.
- Agregar benchmarks de runtime y volumen para Bronze -> Silver -> Gold.
- Expandir escenarios y pruebas de brechas de telemetria, seleccion de APR y casos limite.
- Enriquecer visualizaciones de explicabilidad en el dashboard usando reason codes, causa probable y confianza.
- Preparar una estrategia futura para ingestion real, manteniendo primero compatibilidad con el MVP local.

## 4. Documentacion y reproducibilidad

### Comandos reproducibles

Preparar entorno:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Ejecutar pipeline batch local:

```powershell
python scripts/run_mvp.py --days 7 --freq-minutes 5 --apr-id APR-001
```

Preparar demo con escenario normal:

```powershell
python scripts/demo_workflow.py prepare --scenario normal --apr-id APR-001 --days 7 --freq-minutes 5
```

Preparar demo con escenario hidraulico:

```powershell
python scripts/demo_workflow.py prepare --scenario pump_on_no_recovery --apr-id APR-001
```

Levantar API:

```powershell
python scripts/demo_workflow.py api --port 8000
```

Levantar dashboard:

```powershell
python scripts/demo_workflow.py dashboard --port 8501
```

Health checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod "http://127.0.0.1:8000/twin/state?apr_id=APR-001"
```

Ejecutar pruebas:

```powershell
python -m pytest -q
```

### Roadmap recomendado

El roadmap tecnico debe mantenerse alineado con `docs/roadmap/roadmap.md`:

- Corto plazo: endurecer metricas de calidad, ampliar escenarios, cubrir edge cases y mejorar presentacion del dashboard.
- Mediano plazo: documentar contratos API, agregar benchmarks y estandarizar runbooks de demo.
- Largo plazo compatible con MVP local: modularizar escenarios y profundizar vistas de explicabilidad.

### Conclusiones

El proyecto presenta un MVP tecnicamente consistente para demostracion local de un gemelo digital APR. Su madurez actual esta en la integracion end-to-end, la explicabilidad de reglas, la trazabilidad basica de datos y la reproducibilidad de demos. Las principales brechas no son de coherencia interna, sino de paso a condiciones reales: ingestion de sensores, calibracion con datos de campo, escalamiento, seguridad, observabilidad y gobierno de operacion.

La recomendacion es conservar la arquitectura local como base demostrable mientras se fortalece la evidencia tecnica: contratos API, benchmarks, pruebas de escenarios extremos y documentacion de razonamiento operacional. Ese camino mantiene el MVP estable y permite evolucionarlo sin perder trazabilidad.

