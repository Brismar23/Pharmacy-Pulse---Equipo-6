# Bitácora de decisiones

Decisiones que afectan alcance, fuentes, cálculo o arquitectura (SOW 10, gobierno mínimo). Las marcadas **Propuesta** se validan con Pharmacy Pulse en el Gate indicado.

| # | Fecha | Decisión | Estado | Gate | Dónde se configura |
|---|---|---|---|---|---|
| D1 | 2026-11-18 | Unidad geográfica: **AGEB urbana** del Censo 2020. Plan B si R8 < 80 %: bajar a colonia/alcaldía. | Propuesta | 1 | Código (`limpieza`) |
| D2 | 2026-11-18 | Sustituto de ingreso: **nivel socioeconómico** = promedio normalizado de escolaridad (`GRAPROES`) y % de viviendas con auto, internet y computadora. Alternativa: Grado de Rezago Social por AGEB 2020 de CONEVAL. | Propuesta | 1 | Código (`indicadores`) |
| D3 | 2026-11-18 | Competencia: farmacias **SCIAN 464111 y 464112**. No se cuentan naturistas (464113) ni ópticas. | Propuesta | 2 | `SCIAN_FARMACIAS` en `limpieza` |
| D4 | 2026-11-18 | Unidades de salud (SCIAN 621 y 622) se tratan como **generador de demanda** (recetas), peso 0.10. Se muestran aparte en el mapa. Para quitarlas: peso `salud` = 0. | Propuesta | 2 | `PesosIpa` |
| D5 | 2026-11-18 | Pesos del IPA del SOW 7.4: población 0.30, edades 0.15, ingreso 0.15, salud 0.10, competencia 0.30. | Propuesta | 2 | `PesosIpa` |
| D6 | 2026-11-18 | Competencia y salud se cuentan en un **radio de 500 m** del punto representativo de cada AGEB, no solo dentro de la AGEB. | Propuesta | 2 | `RadioMetros` |
| D7 | 2026-11-18 | Solo entran al ranking AGEB con **500 o más habitantes**. | Propuesta | 2 | `MinPoblacion` |
| D8 | 2026-11-18 | Ejecución en **AWS Lambda** en lugar de `make pipeline` local (ver ADR 0002). | Aprobada por el equipo | 1 | `infra/Lambdas.yaml` |
| D9 | 2026-11-18 | **CSV** en silver y gold en lugar de Parquet (ver ADR 0001). | Aprobada por el equipo | 1 | Código |
| D10 | 2026-11-18 | Sin unión espacial con el Marco Geoestadístico: el DENUE trae la clave de AGEB (ver ADR 0001). | Aprobada por el equipo | 1 | Código |
| D11 | 2026-11-18 | Dos plantillas de CloudFormation: `Buckets.yaml` y `Lambdas.yaml` (ver ADR 0003). | Aprobada por el equipo | 1 | `infra/` |
| D12 | 2026-11-18 | Carga **a demanda**; el calendario trimestral existe pero está apagado. | Propuesta | 1 | `ScheduleState` |
| D13 | Pendiente | Región de AWS (por defecto `us-east-1`; alternativa `mx-central-1`). | Pendiente | 1 | `AWS_REGION` en `deploy.sh` |
| D14 | 2026-11-18 | Alcance geográfico configurable: parámetro `Alcaldias` (`todas` o lista de claves). Default: las 6 del RFP. El análisis exploratorio cubre las 16. | Aprobada por el equipo | 1 | `Alcaldias` en `infra/Lambdas.yaml` |
| D15 | 2026-11-18 | Las farmacias y unidades de salud del radio de 500 m se toman de **toda la CDMX**, aunque el ranking sea de 6 alcaldías, para no subcontar competencia en los bordes. | Aprobada por el equipo | 2 | Código (`limpieza`) |
| D16 | 2026-11-18 | Leaflet va **incluido dentro del HTML** del mapa (sin CDN) para que abra sin internet y en visores que bloquean scripts externos. | Aprobada por el equipo | 2 | `src/mapa/vendor/` |
| D17 | 2026-11-18 | Machine learning solo como **análisis exploratorio** (tipos de zona y hueco de farmacias), fuera del pipeline (ver ADR 0004). | Aprobada por el equipo | 2 | `scripts/analisis/` |
| D18 | 2026-11-18 | Las zonas con hueco se confirman a mano en Google Maps antes de recomendarlas; el resultado queda en `data/extraido/verificacion_google_maps.csv`. | Aprobada por el equipo | 2 | Datos |
