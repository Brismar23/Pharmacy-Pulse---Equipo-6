# Declaración de trabajo (SOW) — versión 2.0

## Proyecto: plataforma de datos para priorizar zonas de apertura de la primera sucursal de Pharmacy Pulse

| Dato | Detalle |
|---|---|
| **Cliente** | Pharmacy Pulse |
| **Contacto del cliente** | Fundadora/Fundador de Pharmacy Pulse |
| **Equipo del proyecto** | Karen Pamela Rico Juárez, Brisa Mariana Gómez Luna, Ana Paula González Frías y Javier de Jesús Infante Martínez |
| **Versión** | 2.0 |
| **Fecha objetivo de entrega** | 29 de enero de 2027 |
| **Presupuesto máximo de referencia** | $120,000 MXN |

> Las decisiones que el RFP deja abiertas —unidad geográfica, categorías DENUE, tratamiento de unidades de salud, sustituto de ingreso y ponderaciones— se validan con Pharmacy Pulse en los Gates 1 y 2, antes de calcular el ranking definitivo.

## 0. Qué cambiamos respecto a la versión 1 y por qué

| Cambio | Por qué |
|---|---|
| El proyecto se replantea como **entrega de datos confiables, disponibles y documentados** (pipeline en AWS), con el índice como una de sus salidas. | La versión 1 era un estudio de analítica; el valor está en mover, limpiar, almacenar y gobernar los datos de forma reproducible. |
| Los roles pasan de analista/revisor a **cuatro roles de datos**: gestión y documentación, ingeniería de ingesta y plataforma, ingeniería de transformación, y calidad y gobierno. | Ninguna persona era dueña de los datos ni de la plataforma. |
| Se agrega **arquitectura en AWS**: S3 en tres zonas (`raw/clean/curated`), CloudFormation, rol IAM mínimo y alerta de presupuesto. | En la v1 AWS era solo una partida de costo y todo corría en carpetas locales. |
| Se agregan **reglas de calidad con umbral**, **linaje**, **versionado de `raw`** e **idempotencia** como criterios de aceptación. | La v1 tenía la intención de controlar la calidad, pero no cómo se garantiza. |
| La **etiqueta de confianza** se calcula a partir de las reglas, el % de faltantes y la antigüedad del dato. | Un semáforo manual es opinión; calculado es un dato. |
| El **mapa** pasa a ser una salida estática del pipeline; la **sensibilidad de pesos** pasa a ser opcional. | Evitar construir una aplicación web y un estudio analítico que no son trabajo de datos. |
| Se agrega la **verificación de ingreso por AGEB y de códigos DENUE en el hito 1**, con un **plan B medible**. | Es el principal riesgo técnico y debe resolverse antes de construir. |
| Se reasignan horas a los roles nuevos y la partida de AWS se sustituye por un tope con alerta. | El presupuesto debe reflejar el trabajo de ingesta, plataforma y calidad. |
| Se limpian el contacto del cliente y las referencias a un proceso de evaluación; la trazabilidad se conserva en la sección 3. | Un SOW lo lee un cliente que decide contratar, y el repositorio será público. |

## 1. Resumen ejecutivo

Pharmacy Pulse planea abrir su primera sucursal en la Ciudad de México durante 2027 y aún no cuenta con historial propio de ventas, clientes o desempeño por ubicación. La propuesta entrega un **pipeline de datos reproducible en AWS** que ingiere datos públicos del INEGI (Censo de Población y Vivienda, DENUE y Marco Geoestadístico), los limpia y valida con reglas de calidad automáticas, los almacena en zonas gobernadas y publica una tabla final de indicadores por zona dentro de Benito Juárez, Coyoacán, Tlalpan, Iztapalapa, Gustavo A. Madero y Álvaro Obregón.

Sobre esa tabla se calcula un **Índice de Potencial de Apertura (IPA)** simple y explicable, escala 0–100, que produce un ranking de al menos 10 zonas, un mapa estático y un resumen ejecutivo. La recomendación se presenta como **priorización relativa para orientar una siguiente fase de validación comercial**, no como garantía de ventas, rentabilidad ni selección de un local específico.

## 2. Objetivo general y objetivos específicos

### Objetivo general
Entregar a Pharmacy Pulse datos públicos confiables, versionados y documentados, y un modelo transparente que permita priorizar zonas para explorar la apertura de su primera sucursal.

### Objetivos específicos
1. Ingerir, limpiar y almacenar las fuentes del INEGI en un lago de datos en S3 con zonas `raw`, `clean` y `curated`.
2. Garantizar la calidad con 5 a 8 reglas con umbral que corren en cada carga y detienen o marcan el pipeline si fallan.
3. Documentar el linaje de cada variable, de la fuente a la tabla final.
4. Construir indicadores de demanda y de presión competitiva y consolidarlos en el IPA, con pesos en un archivo de configuración.
5. Generar un ranking de al menos 10 zonas con puntaje 0–100 y explicación de sus impulsores.
6. Mostrar farmacias y unidades de salud por separado para evitar interpretaciones ambiguas.
7. Generar un mapa estático comprensible para usuarios no técnicos.
8. Permitir que un tercero reproduzca el análisis siguiendo el README en menos de una hora, con resultados idénticos al usar la misma versión de `raw`.
9. Mantener el costo de AWS en $0 efectivo, con una alerta de presupuesto que lo respalde.

## 3. Alineación directa con necesidades N1–N5 del RFP

| Necesidad | Respuesta de la propuesta | Evidencia de cumplimiento |
|---|---|---|
| **N1. Identificar zonas con mayor potencial** | IPA 0–100 y ranking de al menos 10 zonas, calculados desde la tabla `curated` | `ranking.csv`, tabla de ranking y resumen ejecutivo |
| **N2. Medir demanda** | Indicadores de población, edades, sustituto de ingreso y acceso a salud, según compatibilidad geográfica | Diccionario de datos, tabla `curated` y metodología |
| **N3. Medir competencia** | Conteo DENUE de farmacias y unidades de salud, por separado | Tablas `clean`, categorías SCIAN documentadas y mapa |
| **N4. Mapa fácil de consultar** | Mapa estático (HTML con `folium` o PNG) generado por el pipeline | Prueba de uso con tiempo objetivo menor a 5 minutos |
| **N5. Repetir y revisar el análisis** | Repositorio con infraestructura como código, `make pipeline`, versionado de `raw` y README | Reproducción por una persona distinta del autor en menos de 1 hora |

## 4. Alcance del trabajo

### Incluye
- Ingesta de Censo de Población y Vivienda, DENUE y Marco Geoestadístico del INEGI para las seis alcaldías definidas.
- Almacenamiento en S3 con tres zonas, `clean` y `curated` en Parquet, y `raw` versionado por fecha de descarga.
- Infraestructura como código (CloudFormation): bucket, rol IAM mínimo y alerta de presupuesto.
- Reglas de calidad, etiqueta de confianza calculada, fichas de fuente y tabla de linaje.
- Cálculo del IPA con pesos configurables en `config/weights.yaml`.
- Ranking, mapa estático, resumen ejecutivo y presentación final.
- Consulta SQL de los resultados (DuckDB sobre Parquet, o Athena si se decide).
- Documentación: README con diagrama de arquitectura, diccionario de datos, `decision_log.md`, riesgos.

### Opcional (si el calendario lo permite)
- Análisis de sensibilidad de pesos: al ser el IPA una función de `weights.yaml`, se ejecuta cambiando el archivo y reportando el rango de posiciones por zona.

### Fuera de alcance
- Selección, inspección, renta o negociación de locales específicos.
- Licencias, permisos sanitarios o trámites regulatorios.
- Recomendaciones de surtido, inventario, precios, personal o estrategia comercial.
- Proyecciones financieras, pronósticos de ventas o rentabilidad.
- Compra de datos privados de movilidad, renta, tarjetas, geolocalización o afluencia.
- Aplicación web, servidor, login o despliegue web del mapa.
- Garantizar que la zona mejor calificada resulte rentable.

## 5. Arquitectura de datos

### 5.1 Zonas en S3

| Zona | Contenido | Reglas |
|---|---|---|
| `raw/` | Archivos tal como se descargaron de INEGI, en carpetas por fuente y fecha (`raw/denue/2026-11-23/`) | Nunca se modifica ni se sobrescribe; cada descarga conserva su versión |
| `clean/` | Datos limpios, tipados y homologados, en Parquet | Se regenera desde `raw`; pasa las reglas de calidad |
| `curated/` | Tabla final por zona con indicadores e IPA | Idempotente; es la única entrada del ranking y del mapa |

Los scripts leen y escriben en S3, no en carpetas locales. Flujo: `01_extract` (INEGI → `raw`) → `02_clean` (`raw` → `clean`) → `03_indicators` y `04_scoring` (`clean` → `curated`) → `05_map` (`curated` → salidas).

### 5.2 Infraestructura como código
`infra/template.yaml` (CloudFormation) define el bucket S3, un rol IAM de mínimo privilegio para el pipeline y una alerta de AWS Budget. Se usa CloudFormation, no Terraform, por alineación con el curso. Todo con servicios dentro del free tier.

### 5.3 Cómo corre el pipeline
Para una carga que se actualiza pocas veces al año, la ejecución es un comando documentado: `make pipeline`. Esta decisión se registra en `decision_log.md`. Si el cliente requiere ejecución programada, la siguiente opción es AWS Lambda con EventBridge Scheduler (fuera del alcance base).

### 5.4 Consulta de resultados
Opción base: **DuckDB** leyendo el Parquet de S3 (sin costo). Opción alternativa: **Amazon Athena**, que no tiene capa gratuita y cobra por dato escaneado; con volúmenes de decenas de MB el costo sería de centavos, siempre que el AWS Budget esté activo desde el día 0 y el workgroup limite el escaneo. No se usará Glue Crawler; las tablas se definen manualmente con DDL.

### 5.5 Costo
Objetivo: **$0 efectivo**. Se fija un presupuesto de AWS de unos pocos dólares (tope USD 5) con alerta al 80 %, escrito en la plantilla de CloudFormation. Antes del Gate 1 se revisará qué incluye el free tier de la cuenta utilizada, sin darlo por sentado.

## 6. Fuentes de datos, trazabilidad y calidad

### 6.1 Fuentes
| Fuente | Uso esperado | Validaciones mínimas |
|---|---|---|
| **Censo de Población y Vivienda (INEGI)** | Población y estructura por edades por AGEB | Año de referencia, cobertura, clave geográfica y valores faltantes |
| **DENUE (INEGI), CSV completo** | Farmacias y unidades de salud (puntos con coordenadas) | Fecha de actualización, códigos SCIAN, coordenadas válidas y duplicados |
| **Marco Geoestadístico (INEGI)** | Polígonos de AGEB y alcaldías | Versión, claves geográficas y correspondencia con el Censo |
| **Sustituto de ingreso** (por definir en el hito 1) | Aproximación de capacidad económica | Fuente, año, cobertura y compatibilidad con AGEB |

DENUE se descarga como CSV completo, no por API, por reproducibilidad. La unión es por clave de AGEB (`CVEGEO`) para el Censo y el Marco, y espacial punto en polígono para DENUE.

### 6.2 Ficha de control por fuente
Procedencia, URL/origen, fecha de descarga, fecha de referencia, unidad geográfica, variables utilizadas, cobertura, % de valores faltantes, transformaciones aplicadas, limitaciones y responsable de validación.

### 6.3 Reglas de calidad
Cada regla corre en cada carga. Las marcadas como **bloqueantes** detienen el pipeline; las demás marcan el resultado y reducen la confianza.

| # | Regla | Umbral | Acción si falla |
|---|---|---|---|
| R1 | `CVEGEO` es único en la tabla `curated` | 0 duplicados | Bloquea |
| R2 | Establecimientos DENUE con coordenadas válidas dentro de CDMX | 100 % de los retenidos; descartados se reportan | Bloquea si hay coordenadas inválidas en la tabla retenida |
| R3 | AGEB de las seis alcaldías con población | ≥ 95 % | Bloquea |
| R4 | Suma de población por AGEB vs. total de la alcaldía | ±1 % | Bloquea |
| R5 | Indicadores normalizados dentro de 0–100 | 100 % | Bloquea |
| R6 | Registros DENUE duplicados | 0 tras limpieza | Marca |
| R7 | Antigüedad de la fuente respecto al año de análisis | ≤ umbral documentado por fuente | Marca |
| R8 | Cobertura de variables por AGEB (empate con todas las variables) | ≥ 80 % (ver plan B) | Marca y activa plan B si no se cumple |

Las reglas viven en `tests/data_quality_checks.py` y sus resultados se guardan junto a cada carga.

### 6.4 Etiqueta de confianza calculada
La etiqueta (Alta / Media / Baja) se calcula por variable y por zona a partir de: % de valores faltantes, antigüedad del dato y resultado de las reglas. No modifica el IPA; transparenta la robustez de la evidencia.

### 6.5 Linaje
El diccionario de datos incluye una tabla fuente → `raw` → `clean` → tabla `curated` → qué la usa, de modo que la pregunta "¿de dónde salió este puntaje?" se responda en un minuto.

### 6.6 Versionado e idempotencia
- Cada descarga se guarda en `raw/<fuente>/<fecha>/` y nunca se reemplaza. El ranking final registra la versión de `raw` con la que se calculó.
- Si el pipeline corre dos veces sobre la misma versión de `raw`, el resultado es idéntico y no duplica filas. Es criterio de aceptación de la tabla `curated`.

## 7. Metodología analítica

### 7.1 Unidad geográfica
Se propone **AGEB urbana**, por permitir más de 10 zonas y por compartir clave entre Censo y Marco Geoestadístico. Si alguna variable solo existe a un nivel más agregado, no se imputará ni redistribuirá sin validación explícita.

**Plan B medible:** si menos de 80 % de los AGEB empatan con todas las variables, el análisis baja a nivel alcaldía/colonia. La decisión se registra en `decision_log.md`.

### 7.2 Definición de competencia
Se documentarán los códigos SCIAN vigentes incluidos. Punto de partida a verificar en el hito 1: rama 4641 para farmacias y ramas 621/622 para atención médica. Las unidades de salud se reportan por separado; su tratamiento en el IPA (generador de demanda, contexto o competencia) se valida con el cliente en el Gate 2 y no se asume.

### 7.3 Normalización
Min–max a escala 0–100 dentro del universo analizado:

`Indicador_norm = 100 × (x - min(x)) / (max(x) - min(x))`

Para variables donde un valor alto implique menor atractivo (presión competitiva): `Indicador_inverso = 100 - Indicador_norm`.

### 7.4 Índice de Potencial de Apertura (IPA)
Punto de partida sujeto a aprobación; los pesos se leen de `config/weights.yaml`:

`IPA = 0.30(Población) + 0.15(Composición por edades) + 0.15(Ingreso o sustituto) + 0.10(Acceso/contexto de salud) + 0.30(Presión competitiva inversa)`

Equivale a 70 % demanda/contexto y 30 % presión competitiva. Los pesos son hipótesis de decisión, no parámetros aprendidos de ventas.

### 7.5 Ingreso por AGEB
El Censo no reporta ingreso directamente a nivel AGEB. En el hito 1 se decide un sustituto (por ejemplo, escolaridad o derechohabiencia del Censo, o un índice de rezago/marginación publicado por otra institución) y se registra en `decision_log.md`. Si no hay sustituto aceptable, se recalculan los pesos aprobados sin esta variable, con aprobación del cliente.

### 7.6 Sensibilidad de pesos (opcional)
Se ejecutan escenarios alternativos cambiando `weights.yaml` y se reporta la posición base, el rango de posiciones y las zonas robustas y sensibles.

## 8. Entregables y criterios de aceptación

| Entregable | Criterio de aceptación | Evidencia |
|---|---|---|
| Definición metodológica | Cliente valida unidad geográfica, SCIAN, tratamiento de salud, sustituto de ingreso y ponderaciones | `decision_log.md` / acta breve |
| Infraestructura en AWS | `infra/template.yaml` despliega bucket, rol IAM mínimo y alerta de presupuesto desde cero | Pila de CloudFormation y alerta activa |
| Zonas `raw/clean/curated` | `raw` versionado por fecha y sin modificaciones; `clean` y `curated` en Parquet | Estructura en S3 |
| Reglas de calidad | 5 a 8 reglas con umbral que corren en cada carga y detienen o marcan el pipeline | Reporte de calidad por carga |
| Diccionario, fichas y linaje | Fuentes, variables, fechas, transformaciones y tabla de linaje documentadas | `data_dictionary.md` + fichas |
| Tabla `curated` | Idempotente: dos ejecuciones sobre la misma versión de `raw` dan el mismo resultado sin duplicar filas | Prueba de idempotencia |
| Ranking e indicadores | Al menos 10 zonas, IPA 0–100, explicación de factores y etiqueta de confianza | `ranking.csv` + resumen |
| Mapa estático | Usuario no técnico localiza e interpreta una zona en menos de 5 min | Prueba de uso |
| Repositorio GitHub | Código, datos públicos permitidos, dependencias, `Makefile` y README con diagrama de arquitectura | Prueba de reproducción en menos de 1 h por otra persona |
| Resumen ejecutivo | Máximo 2 páginas: recomendación, razones, limitaciones y próximos pasos | Documento final |
| Presentación | Sesión final con narrativa ejecutiva y preguntas | Presentación y minuta de cierre |
| Sensibilidad (opcional) | Cambios de posición bajo escenarios razonables | Tabla de estabilidad |

## 9. Estructura propuesta del repositorio

Nombre del repositorio: `cdmx-pharmacy-site-selection`.

```text
cdmx-pharmacy-site-selection/
├── README.md                     # problema, arquitectura (diagrama), cómo correrlo
├── Makefile                      # make pipeline
├── requirements.txt
├── .gitignore
├── config/
│   └── weights.yaml              # pesos del IPA
├── infra/
│   └── template.yaml             # CloudFormation: S3, IAM mínimo, AWS Budget
├── data/
│   └── data_dictionary.md        # incluye tabla de linaje
├── src/
│   ├── 01_extract.py             # INEGI -> raw/<fuente>/<fecha>/
│   ├── 02_clean.py               # raw -> clean (Parquet)
│   ├── 03_indicators.py
│   ├── 04_scoring.py             # clean -> curated (lee weights.yaml)
│   └── 05_map.py                 # mapa estático
├── sql/
│   └── ddl.sql                   # tablas para DuckDB/Athena
├── notebooks/                    # solo exploración; lógica final en src/
├── outputs/
│   ├── ranking.csv
│   ├── sensitivity.csv           # opcional
│   └── map/
├── docs/
│   ├── consultoria/
│   │   ├── rfp.md
│   │   └── sow.md
│   ├── methodology.md
│   ├── decision_log.md
│   ├── source_cards/             # fichas de control por fuente
│   ├── risks.md
│   └── executive_summary.md
└── tests/
    └── data_quality_checks.py    # reglas R1–R8
```

Convención: carpetas y archivos en minúsculas y sin espacios. El PDF se genera solo al entregar, fuera del repositorio.

## 10. Gobierno, roles y responsabilidades

| Integrante | Rol | Responsabilidades |
|---|---|---|
| **Brisa Mariana Gómez Luna** | **Project manager y documentación** | Calendario, comunicación con el cliente, control de cambios, `decision_log.md`, README y resumen ejecutivo |
| **Javier de Jesús Infante Martínez** | **Data Engineer de ingesta y plataforma** | S3, CloudFormation, IAM, descarga desde INEGI, versionado de `raw`, `make pipeline` |
| **Ana Paula González Frías** | **Data Engineer de transformación** | Limpieza, unión espacial, tablas `clean` y `curated`, indicadores e IPA |
| **Karen Pamela Rico Juárez** | **Calidad y gobierno de datos, y mapa** | Reglas de calidad, fichas de fuente, linaje, etiqueta de confianza, pruebas del pipeline y salida del mapa |

> La asignación de personas a roles es una propuesta a confirmar por el equipo en el kickoff.

### Gobierno mínimo
- Las decisiones que afecten alcance, scoring, fuentes, arquitectura o fecha se registran en `docs/decision_log.md`.
- La versión final del scoring requiere aprobación documentada antes de publicar el ranking.
- Los cambios de alcance posteriores a la validación inicial indican impacto en costo y calendario.
- El repositorio público no incluye información confidencial del cliente.

## 11. Calendario propuesto

| Fase | Fechas | Actividades y salida |
|---|---|---|
| Inicio y hito 1 | 10–20 nov 2026 | Kickoff; **verificar ingreso por AGEB y códigos SCIAN**; fijar plan B; desplegar CloudFormation y alerta de presupuesto; decidir unidad geográfica |
| Ingesta y calidad | 23 nov–4 dic 2026 | Descarga a `raw` versionado, `clean`, fichas de fuente, reglas de calidad y diccionario |
| Transformación y análisis | 7 dic 2026–8 ene 2027 | Tabla `curated`, linaje, IPA, ranking preliminar, mapa y (opcional) sensibilidad |
| Revisión con cliente | 11–15 ene 2027 | Revisar resultados, decisiones pendientes y correcciones dentro de alcance |
| Entrega y presentación | 18–29 ene 2027 | Repositorio final, prueba de reproducción, resumen y presentación |

### Gates de decisión
- **Gate 1:** unidad geográfica, fuentes, sustituto de ingreso y arquitectura.
- **Gate 2:** códigos SCIAN, tratamiento de unidades de salud y ponderaciones.
- **Gate 3:** validación de ranking preliminar y calidad de datos.
- **Gate 4:** aceptación final contra los criterios de la sección 8.

## 12. Presupuesto y costos de operación

| Rol / partida | Horas | Tarifa | Importe |
|---|---:|---:|---:|
| Project manager y documentación | 100 | $200 MXN/h | $20,000 MXN |
| Data Engineer de ingesta y plataforma | 110 | $250 MXN/h | $27,500 MXN |
| Data Engineer de transformación | 120 | $250 MXN/h | $30,000 MXN |
| Calidad y gobierno de datos, y mapa | 110 | $250 MXN/h | $27,500 MXN |
| **Subtotal equipo (440 h)** | | | **$105,000 MXN** |
| AWS: tope de presupuesto con alerta al 80 % (USD 5 aprox.) | | | $100 MXN |
| Reserva para variaciones (aprox. 12 %) | | | $14,900 MXN |
| **Total máximo de referencia** | | | **$120,000 MXN** |

Costo operativo mensual esperado tras la entrega: **$0** (el costo de almacenamiento de decenas de MB en S3 queda dentro del free tier o de centavos), muy por debajo del máximo de $2,000 MXN del RFP. Cualquier servicio de pago, dominio o cambio de arquitectura se aprueba antes de contratarse.

## 13. Riesgos, supuestos y mitigaciones

| Riesgo / supuesto | Impacto | Mitigación |
|---|---|---|
| Ingreso no disponible por AGEB | Pérdida de una variable (15 % del IPA) | Verificación en el hito 1; sustituto documentado; recalcular pesos con aprobación |
| Menos de 80 % de AGEB con todas las variables | Análisis poco comparable | Plan B: bajar a alcaldía/colonia |
| Fuentes con distinta antigüedad | Comparabilidad temporal | Regla R7, fechas visibles y etiqueta de confianza |
| DENUE se actualiza y cambia los resultados | Ranking no reproducible | `raw` versionado por fecha |
| Cambios en códigos SCIAN o cobertura de DENUE | Competencia mal medida | Verificar códigos vigentes; declarar clases, fecha y limitaciones |
| Costos inesperados en AWS | Exceder presupuesto | AWS Budget con alerta al 80 % desde el día 0; sin Glue Crawler; límite de escaneo si se usa Athena |
| Ausencia de ventas propias | No se puede calibrar con conversión real | Tratar el IPA como priorización relativa, no pronóstico |
| Tratamiento ambiguo de unidades de salud | Sesgo del IPA | Reportarlas por separado y validar su papel en el Gate 2 |
| Retrasos en aprobaciones | Afectación del cronograma | Gates, responsables y fecha límite de comentarios |
| Confusión entre score y rentabilidad | Decisión de negocio incorrecta | Disclaimer visible y siguiente fase de validación en campo |

## 14. KPIs de éxito y cierre

- **Calidad:** 100 % de las reglas bloqueantes aprobadas en la carga final.
- **Trazabilidad:** 100 % de variables finales con fuente, fecha, transformación y linaje documentados.
- **Reproducibilidad:** ejecución por tercero en menos de 1 hora, con resultados idénticos sobre la misma versión de `raw`.
- **Idempotencia:** dos ejecuciones consecutivas no cambian ni duplican la tabla `curated`.
- **Ranking:** mínimo 10 zonas con IPA 0–100 y explicación.
- **Usabilidad:** mapa interpretable por usuario no técnico en menos de 5 minutos.
- **Costo:** gasto en AWS dentro del tope definido, sin activar la alerta de presupuesto.
- **Transparencia:** limitaciones y supuestos visibles en el mapa, el README y el resumen ejecutivo.

## 15. Recomendación de uso del resultado

El ranking se utiliza para seleccionar un grupo reducido de zonas candidatas —por ejemplo, Top 3 o Top 5— que avancen a una segunda fase de **due diligence comercial**. Esa fase, fuera del alcance actual, podría incorporar rentas, flujo peatonal, accesibilidad, seguridad, visibilidad, estacionamiento, oferta inmobiliaria, competencia no registrada y visitas de campo.

El proyecto reduce el espacio de búsqueda con evidencia pública sin atribuir al modelo una precisión que no puede sostener con los datos disponibles.

## 16. Aprobación

La ejecución inicia tras la adjudicación y la confirmación escrita del alcance, calendario, presupuesto y decisiones pendientes. La aceptación final se realiza contra los criterios de la sección 8.

| Por Pharmacy Pulse | Por el equipo del proyecto |
|---|---|
| Nombre: __________________________ | Nombre: _________________________ |
| Cargo: ___________________________ | Cargo: ___________________________ |
| Fecha: ___________________________ | Fecha: ___________________________ |
| Firma: ___________________________ | Firma: ___________________________ |
