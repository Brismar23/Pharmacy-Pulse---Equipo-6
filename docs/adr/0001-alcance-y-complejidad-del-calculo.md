# ADR 0001: Qué tanto calculamos (alcance y complejidad del cálculo)

* **Estado:** Propuesto (se confirma con Pharmacy Pulse en los Gates 1 y 2)
* **Fecha:** 2026-11-18
* **Proyecto:** Plataforma de datos para priorizar zonas de apertura de Pharmacy Pulse
* **Relacionado:** [ADR 0002](0002-lambda-vs-glue.md), [ADR 0003](0003-cloudformation-dos-plantillas.md), [SOW](../consultoria/sow.md) secciones 5 a 7

## Contexto

La decisión del cliente es una sola y es binaria en la práctica: **en qué zonas buscar local para la primera sucursal**. No hay ventas propias para entrenar un modelo (RFP, sección 5), el usuario final no es técnico (RFP, sección 6) y el presupuesto de operación debe tender a $0. Cada cálculo extra agrega costo, tiempo de construcción y, sobre todo, cosas que hay que explicarle a un fundador que tiene que confiar en el ranking.

La pregunta de este ADR es: **¿cuánto cálculo necesita esa decisión, y dónde paramos?**

## Decisión

Calculamos **lo mínimo que hace defendible un ranking**, y nada que no podamos explicar en una frase.

| Tema | Lo que SÍ hacemos | Lo que NO hacemos (y por qué) |
|---|---|---|
| Unidad de análisis | **AGEB urbana** del Censo 2020 en las 6 alcaldías (unas 1,000 zonas). | Manzana (demasiado ruido) ni alcaldía (solo 6 zonas; no cumple N1 de 10 zonas). |
| Demanda | 4 indicadores del Censo: **población**, **% de 60 años o más**, **nivel socioeconómico** (sustituto de ingreso, SOW 7.5: escolaridad y % de viviendas con auto, internet y computadora) y **consultorios/hospitales cercanos** (generan recetas). | Ingreso real por AGEB (no existe en el Censo), flujo peatonal, rentas (datos privados, fuera de alcance). |
| Competencia | **Farmacias del DENUE (SCIAN 464111 y 464112) a menos de 500 m** del punto representativo de la zona. | Modelos de gravedad o de Huff, tiempos de traslado reales, cuota de mercado por cadena. |
| Geografía | **Sin unión espacial con polígonos.** El DENUE ya trae la clave de AGEB de cada establecimiento, así que Censo y DENUE se unen por clave. El punto representativo de la zona es el promedio de coordenadas de sus establecimientos DENUE. | Descargar el Marco Geoestadístico (shapefiles) y hacer punto-en-polígono: pide GeoPandas/Shapely/GDAL, que no caben cómodos en una Lambda sin capas pesadas. |
| Índice | **IPA = suma ponderada** de 5 componentes normalizados 0-100 (min-max recortado a percentiles 5-95). Pesos del SOW 7.4 en un parámetro (`PESOS_IPA`), no en el código. | Machine learning **dentro del IPA**: sin ventas no hay con qué entrenar ni validar un pronóstico. El análisis exploratorio con ML va aparte (ADR 0004) y no cambia el IPA. |
| Explicación | Cada zona del ranking trae su **"por qué"** en lenguaje simple (dos fortalezas y un punto débil) y una **etiqueta de confianza** calculada. | Tableros interactivos o una aplicación web (SOW 4, fuera de alcance). |
| Formato | **CSV UTF-8** en silver y gold (biblioteca estándar de Python). | Parquet: obliga a una capa de Lambda (pyarrow o AWS SDK for pandas) para tablas de pocos MB. DuckDB y Athena leen CSV igual. |
| Calidad | Reglas **R1-R8** del SOW 6.3 en cada carga, más N1 (al menos 10 zonas). Las bloqueantes detienen la publicación. | Frameworks de calidad (Great Expectations, Glue Data Quality): sobredimensionados para 8 reglas. |
| Sensibilidad | Opcional: se cambia `PESOS_IPA` y se vuelve a correr la Lambda de indicadores. | Un estudio de sensibilidad automático con cientos de escenarios. |

### Cómo se calcula, en una página

1. **Población** (`n_poblacion`): habitantes de la AGEB. Solo entran al ranking zonas con 500 o más habitantes (`MIN_POBLACION`), para no premiar parques o zonas industriales.
2. **Edades** (`n_edades`): % de personas de 60 años o más (mayor consumo de medicamentos).
3. **Ingreso, por sustituto** (`n_ingreso`): promedio de cuatro variables normalizadas del Censo: escolaridad (`GRAPROES`) y % de viviendas con auto (`VPH_AUTOM`), internet (`VPH_INTER`) y computadora (`VPH_PC`).
4. **Salud** (`n_salud`): consultorios y hospitales (SCIAN 621 y 622) a menos de 500 m.
5. **Competencia inversa** (`n_competencia`): 100 menos el valor normalizado de farmacias a menos de 500 m.

`IPA = 0.30·población + 0.15·edades + 0.15·ingreso + 0.10·salud + 0.30·competencia`

Si a una zona le falta un dato (asterisco o N/D del INEGI), el IPA se calcula con los componentes disponibles reponderados, y la zona baja su etiqueta de confianza.

## Por qué así

* **El cliente tiene que poder auditarlo.** "Tiene 6 mil habitantes, 20 % son adultos mayores y no hay farmacia a 500 m" se entiende y se puede verificar caminando. Un puntaje de un modelo de caja negra no.
* **Los datos no dan para más precisión.** El Censo es de 2020 y no trae ingreso por AGEB; inventar precisión sería engañar al cliente (SOW 15).
* **Cabe en una Lambda sin capas.** Solo biblioteca estándar: zips de 20 KB, sin problemas de versiones de pyarrow o GDAL, despliegue en segundos.
* **Medido:** con 524 mil registros del DENUE (tamaño de la CDMX), la limpieza tarda unos 5 s y usa unos 106 MB de memoria; el cálculo del IPA, menos de 1 s.

## Por qué 500 m y no la AGEB para la competencia

Contar farmacias solo dentro de la AGEB premia zonas con 0 farmacias aunque haya una en la acera de enfrente que cae en la AGEB vecina. Contarlas en un radio usa las coordenadas que el DENUE ya trae, cuesta unas líneas de código y se explica fácil ("farmacias a unos 6 minutos caminando"). El radio es un parámetro (`RadioMetros`).

## Consecuencias

**Positivas**
* Ranking explicable, reproducible e idempotente (mismas entradas, mismos bytes).
* Operación casi gratis y sin dependencias que mantener.
* Cambiar pesos, radio o población mínima no requiere tocar código.

**Negativas / riesgos**
* El punto representativo (promedio de establecimientos) puede caer en una orilla de la AGEB si los comercios se concentran en una avenida. Aceptable para priorizar; las zonas finalistas se visitan en campo.
* La escolaridad es un sustituto imperfecto del ingreso. Si el cliente lo prefiere, se puede cambiar por el Grado de Rezago Social por AGEB de CONEVAL (ver decision log).
* Sin polígonos, el mapa muestra círculos por zona en lugar de áreas coloreadas.
* Cambios respecto al SOW v2.0: CSV en lugar de Parquet (5.1) y Lambdas en lugar de `make pipeline` local (5.3, ver ADR 0002).

## Cuándo subiríamos la complejidad

* Si el cliente consigue datos de ventas de una sucursal piloto: calibrar los pesos con esas ventas.
* Si se compran datos de flujo peatonal o rentas: agregarlos como componentes del IPA.
* Si se pide un mapa con áreas: agregar el Marco Geoestadístico con una capa de Lambda geoespacial o un paso fuera de Lambda.
