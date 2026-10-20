# Declaración de trabajo (SOW)

## Proyecto: análisis de zonas para la primera sucursal de Pharmacy Pulse

| Dato | Detalle |
|---|---|
| **Cliente** | Pharmacy Pulse |
| **Contacto del cliente** | Caleb Aguilar Camargo |
| **Project Owner** | **Karen Pamela Rico Juárez** |
| **Equipo propuesto** | Karen Pamela Rico Juárez, Brisa Mariana Gómez Luna, González Frías Ana Paula y Javier de Jesus Infante Martínez |
| **Fecha objetivo de entrega** | 29 de enero de 2027 |
| **Presupuesto máximo de referencia** | $120,000 MXN |

> Esta versión fortalece la SOW original con elementos de evaluación, trazabilidad, control de calidad y reproducibilidad. Las decisiones que el RFP deja abiertas —unidad geográfica, categorías DENUE, tratamiento de unidades de salud y ponderaciones— deberán validarse con Pharmacy Pulse antes de calcular el ranking definitivo.

## 1. Resumen ejecutivo

Pharmacy Pulse planea abrir su primera sucursal en la Ciudad de México durante 2027 y aún no cuenta con historial propio de ventas, clientes o desempeño por ubicación. La propuesta plantea un análisis reproducible basado en datos públicos del INEGI para priorizar zonas dentro de Benito Juárez, Coyoacán, Tlalpan, Iztapalapa, Gustavo A. Madero y Álvaro Obregón.

La solución combinará variables de demanda potencial, estructura demográfica, ingreso disponible cuando exista a un nivel geográfico compatible, acceso o proximidad a servicios de salud y presión competitiva observada en DENUE. Los indicadores serán normalizados en una escala 0–100 y consolidados en un **Índice de Potencial de Apertura (IPA)** interpretable. El resultado final será un ranking de al menos 10 zonas, acompañado de explicación de los factores que impulsan o reducen el puntaje, mapa de consulta, documentación y repositorio reproducible.

La recomendación se presentará como **priorización relativa para orientar una siguiente fase de validación comercial**, no como garantía de ventas, rentabilidad ni selección de un local específico.

## 2. Objetivo general y objetivos específicos

### Objetivo general
Identificar y priorizar las zonas con mayor potencial relativo para explorar la apertura de la primera sucursal de Pharmacy Pulse mediante un modelo transparente y reproducible sustentado principalmente en información pública del INEGI.

### Objetivos específicos
1. Comparar zonas con una metodología homogénea y trazable.
2. Construir un indicador de demanda potencial y un indicador de presión competitiva.
3. Generar un ranking de al menos 10 zonas con puntaje 0–100 y explicación de los principales impulsores.
4. Mostrar farmacias y unidades de salud de forma separada para evitar interpretaciones ambiguas.
5. Habilitar una consulta visual en mapa comprensible para usuarios no técnicos.
6. Permitir que un tercero reproduzca el análisis siguiendo el README en menos de una hora, sujeto a disponibilidad de las fuentes originales.
7. Documentar limitaciones, supuestos, decisiones metodológicas y sensibilidad del ranking.

## 3. Alineación directa con necesidades N1–N5 del RFP

| Necesidad | Respuesta de la propuesta | Evidencia de cumplimiento |
|---|---|---|
| **N1. Identificar zonas con mayor potencial** | IPA 0–100 y ranking de al menos 10 zonas | Archivo de resultados, tabla de ranking y resumen ejecutivo |
| **N2. Medir demanda** | Indicadores de población, edades, ingreso y acceso/proximidad a salud, según compatibilidad geográfica | Diccionario de variables, tabla de indicadores y metodología |
| **N3. Medir competencia** | Conteo DENUE de farmacias y unidades de salud, reportados por separado | Dataset procesado, categorías DENUE documentadas y mapa |
| **N4. Mapa fácil de consultar** | Visualización geográfica con zonas, puntaje y variables clave | Prueba de uso con tiempo objetivo menor a 5 minutos |
| **N5. Repetir y revisar el análisis** | Repositorio estructurado, dependencias, scripts/notebooks y README | Prueba de reproducibilidad por una persona distinta del autor |

## 4. Alcance del trabajo

### Incluye
- Delimitar y comparar zonas dentro de las seis alcaldías definidas por el cliente.
- Identificar, descargar y documentar fuentes públicas pertinentes del INEGI, incluyendo Censo de Población y Vivienda y DENUE.
- Evaluar la disponibilidad de indicadores de ingreso al nivel geográfico seleccionado; si no existe compatibilidad, documentar la limitación y solicitar aprobación antes de cualquier sustitución.
- Preparar, limpiar, homologar y validar datos con trazabilidad de transformaciones.
- Definir y documentar una metodología de puntuación interpretable.
- Generar ranking, indicadores, explicaciones, mapa y resumen ejecutivo.
- Documentar el repositorio de GitHub para facilitar auditoría y reproducción.
- Ejecutar controles de calidad de datos y análisis de sensibilidad de ponderaciones.

### Fuera de alcance
- Selección, inspección, renta o negociación de locales específicos.
- Licencias, permisos sanitarios o trámites regulatorios.
- Recomendaciones de surtido, inventario, precios, personal o estrategia comercial.
- Proyecciones financieras detalladas, pronósticos de ventas o rentabilidad.
- Compra de datos privados de movilidad, renta, tarjetas, geolocalización o afluencia.
- Garantizar que la zona mejor calificada resulte rentable.

## 5. Fuentes de datos, trazabilidad y calidad

### Fuentes prioritarias
| Fuente | Uso esperado | Validaciones mínimas |
|---|---|---|
| **Censo de Población y Vivienda (INEGI)** | Población y estructura por edades | Año de referencia, cobertura, unidad geográfica y valores faltantes |
| **DENUE (INEGI)** | Farmacias y unidades de salud | Fecha de actualización, categorías económicas, georreferencia y duplicados |
| **Indicadores públicos de ingreso compatibles** | Aproximación de capacidad económica | Fuente, año, cobertura y compatibilidad con la unidad de análisis |
| **Marco geoestadístico INEGI** | Límites y relación espacial | Versión, claves geográficas y correspondencia con indicadores |

### Matriz de calidad de datos
Cada fuente se registrará en una ficha de control con: procedencia, URL/origen, fecha de descarga, fecha de referencia, unidad geográfica, variables utilizadas, cobertura, porcentaje de valores faltantes, transformaciones aplicadas, limitaciones y responsable de validación.

Se recomienda reportar una **etiqueta de confianza del dato** (Alta / Media / Baja) basada en actualidad, completitud y compatibilidad geográfica. Esta etiqueta no modifica automáticamente el IPA; sirve para transparentar la robustez de la evidencia.

## 6. Metodología analítica

### 6.1 Unidad geográfica
El nivel de análisis definitivo se aprobará durante el arranque. Se propone utilizar **AGEB urbana** cuando exista compatibilidad suficiente entre fuentes porque permite comparar más de 10 zonas con mayor granularidad que la alcaldía. Si alguna variable solo existe a un nivel más agregado, no se imputará ni redistribuirá de forma artificial sin validación explícita.

### 6.2 Definición de competencia
Antes del cálculo final se documentarán los códigos/clases DENUE incluidos como:
- Farmacias u otros establecimientos de venta de medicamentos definidos como competencia directa.
- Unidades de salud, reportadas de manera separada.

Las unidades de salud pueden comportarse como generadores de demanda, contexto sanitario o presión competitiva dependiendo del tipo de establecimiento. Por ello, **su tratamiento en el IPA deberá validarse con el cliente** y no se asumirá automáticamente.

### 6.3 Normalización
Los indicadores comparables se convertirán a escala 0–100 utilizando una regla documentada, por ejemplo normalización min–max dentro del universo analizado:

`Indicador_norm = 100 × (x - min(x)) / (max(x) - min(x))`

Para variables donde un valor alto represente menor atractivo (por ejemplo, mayor presión competitiva), se utilizará la escala inversa:

`Indicador_inverso = 100 - Indicador_norm`

### 6.4 Índice de Potencial de Apertura (IPA)
Como punto de partida sujeto a aprobación:

`IPA = 0.30(Población) + 0.15(Composición por edades) + 0.15(Ingreso) + 0.10(Acceso/contexto de salud) + 0.30(Presión competitiva inversa)`

Equivale a una estructura general de **70 % demanda/contexto y 30 % presión competitiva**. Los pesos son hipótesis de decisión, no parámetros estadísticos aprendidos de ventas históricas, por lo que deberán aprobarse antes del ranking final.

### 6.5 Análisis de sensibilidad — complemento recomendado
Para fortalecer la evaluación, se probarán escenarios alternativos de ponderación alrededor del modelo base. El objetivo será observar si las zonas líderes permanecen en posiciones similares cuando cambian razonablemente los pesos.

Se reportará:
- Posición de cada zona en el escenario base.
- Rango de posiciones observado en escenarios alternativos.
- Zonas **robustas** (mantienen posición alta) y zonas **sensibles** (cambian significativamente).

Esto reduce el riesgo de presentar como concluyente un ranking que dependa excesivamente de una ponderación subjetiva.

## 7. Entregables y criterios de aceptación

| Entregable | Criterio de aceptación | Evidencia |
|---|---|---|
| Definición metodológica | Cliente valida unidad geográfica, categorías DENUE, tratamiento de salud y ponderaciones | Registro de decisión / acta breve |
| Datos preparados y diccionario | Fuentes, variables, fechas y transformaciones documentadas | Carpeta `data/` + diccionario |
| Ranking e indicadores | Al menos 10 zonas, IPA 0–100 y explicación de factores | CSV/tabla + resumen |
| Análisis de sensibilidad | Se muestran cambios de posición bajo escenarios razonables | Tabla de estabilidad |
| Mapa | Usuario no técnico localiza e interpreta una zona en <5 min | Prueba de uso |
| Repositorio GitHub | Código, datos públicos permitidos, dependencias y README | Prueba de reproducción <1 h |
| Resumen ejecutivo | Máximo 2 páginas, recomendación, razones, limitaciones y próximos pasos | Documento final |
| Presentación | Sesión final con narrativa ejecutiva y preguntas | Presentación y minuta de cierre |

## 8. Matriz de evaluación del RFP — complemento para maximizar puntuación

| Criterio del RFP | Peso | Cómo lo cubre esta propuesta | Evidencia que conviene mostrar |
|---|---:|---|---|
| **Respuesta a N1–N5** | 35 % | Matriz de trazabilidad, ranking, mapa y reproducibilidad | Sección 3 + demo final |
| **Uso adecuado y claro de INEGI** | 25 % | Fuentes, control de calidad, granularidad y limitaciones | Fichas de fuente + diccionario |
| **Costo total** | 20 % | Presupuesto dentro del máximo de $120,000 MXN | Tabla de costos y supuestos |
| **Calidad del plan y tiempos** | 10 % | Fases, hitos, gates de decisión y criterios de aceptación | Cronograma + calendario de revisiones |
| **Manejo de riesgos** | 10 % | Registro de riesgos, mitigaciones y sensibilidad | Matriz de riesgos + análisis de estabilidad |

### Evidencias adicionales recomendadas para la evaluación
1. **Matriz de trazabilidad requisito → entregable → evidencia.** Facilita al evaluador comprobar que ninguna necesidad quedó sin respuesta.
2. **Diccionario de datos y bitácora de transformaciones.** Eleva la auditabilidad del uso de INEGI.
3. **Prueba de reproducibilidad independiente.** Una persona distinta del autor ejecuta el flujo siguiendo únicamente el README.
4. **Análisis de sensibilidad.** Demuestra que el ranking fue cuestionado y no solo calculado.
5. **Registro de decisiones metodológicas.** Documenta por qué se eligieron AGEB, categorías DENUE, pesos y cualquier sustitución de variables.
6. **Semáforo de calidad/confianza de datos.** Ayuda a distinguir resultados sólidos de resultados que requieren validación en campo.
7. **Criterios de salida para la siguiente fase.** Define qué zonas deben pasar a due diligence comercial sin confundir el estudio con una selección de local.

## 9. Estructura propuesta del repositorio

```text
Pharmacy-Pulse---Equipo-6/
├── README.md
├── SOW.md
├── requirements.txt              # o environment.yml
├── .gitignore
├── .github/
│   └── CODEOWNERS
├── data/
│   ├── raw/                      # datos públicos permitidos / instrucciones de descarga
│   ├── processed/
│   └── data_dictionary.md
├── src/
│   ├── 01_extract.py
│   ├── 02_clean.py
│   ├── 03_indicators.py
│   ├── 04_scoring.py
│   └── 05_map.py
├── notebooks/                    # solo exploración; lógica final en src/
├── outputs/
│   ├── ranking.csv
│   ├── sensitivity.csv
│   └── map/
├── docs/
│   ├── methodology.md
│   ├── decision_log.md
│   ├── risks.md
│   └── executive_summary.pdf
└── tests/
    └── data_quality_checks.py
```

## 10. Gobierno, roles y responsabilidades

| Integrante | Rol formal | Responsabilidades |
|---|---|---|
| **Karen Pamela Rico Juárez** | **Project Owner / Gobierno y documentación** | Visión del entregable, trazabilidad documental, README, resumen ejecutivo, control de cambios y aceptación interna |
| **Brisa Mariana Gómez Luna** | **Project Lead / Gestión del proyecto** | Calendario, coordinación, reuniones, dependencias, entregables y comunicación con el cliente |
| **González Frías Ana Paula** | **Data Analyst / Analítica y preparación de datos** | Fuentes, limpieza, homologación, indicadores, normalización, scoring y sensibilidad |
| **Javier de Jesus Infante Martínez** | **Geospatial & Technical Reviewer / Mapa y revisión técnica** | Mapa, revisión técnica independiente, control de reproducibilidad y soporte de integración |

### Gobierno mínimo del proyecto
- Las decisiones que afecten alcance, scoring, fuentes o fecha se registrarán en `docs/decision_log.md`.
- La versión final del scoring requiere aprobación documentada antes de publicar el ranking definitivo.
- Los cambios de alcance posteriores a la validación inicial deberán indicar impacto en costo y calendario.
- El repositorio público no incluirá información confidencial del cliente.

## 11. Calendario propuesto

| Fase | Fechas propuestas | Actividades y salida |
|---|---|---|
| Inicio y definición | 10–20 nov 2026 | Kickoff; confirmar unidad geográfica, categorías DENUE, pesos, responsables y criterios de aceptación |
| Fuentes y preparación | 23 nov–4 dic 2026 | Recopilar fuentes, calidad, homologación, diccionario y reporte de vacíos |
| Análisis y prototipo | 7 dic 2026–8 ene 2027 | Indicadores, IPA, sensibilidad, ranking preliminar y mapa |
| Revisión con cliente | 11–15 ene 2027 | Revisar resultados, decisiones pendientes y correcciones dentro de alcance |
| Entrega y presentación | 18–29 ene 2027 | Repositorio final, resumen, pruebas de aceptación y presentación |

### Gates de decisión
- **Gate 1:** aprobación de unidad geográfica y fuentes.
- **Gate 2:** aprobación de categorías DENUE y ponderaciones.
- **Gate 3:** validación de ranking preliminar y sensibilidad.
- **Gate 4:** aceptación final contra criterios documentados.

## 12. Presupuesto y costos de operación

| Integrante / partida | Horas estimadas | Tarifa estimada | Importe estimado |
|---|---:|---:|---:|
| Brisa Mariana Gómez Luna — coordinación y gestión | 60 | $250 MXN/h | $15,000 MXN |
| González Frías Ana Paula — análisis y preparación de datos | 140 | $250 MXN/h | $35,000 MXN |
| Karen Pamela Rico Juárez — gobierno, documentación y entregables | 100 | $200 MXN/h | $20,000 MXN |
| Javier de Jesus Infante Martínez — mapa y revisión técnica | 140 | $250 MXN/h | $35,000 MXN |
| **Subtotal equipo (440 h)** |  |  | **$105,000 MXN** |
| AWS durante implementación (estimado) |  |  | $1,000 MXN |
| Reserva para variaciones |  |  | $14,000 MXN |
| **Total máximo de referencia** |  |  | **$120,000 MXN** |

El costo operativo mensual deberá mantenerse por debajo del máximo indicado en el RFP. Cualquier servicio de pago, dominio o cambio de arquitectura deberá aprobarse antes de contratarse.

## 13. Riesgos, supuestos y mitigaciones

| Riesgo / supuesto | Impacto | Mitigación |
|---|---|---|
| Fuentes con distinta antigüedad | Comparabilidad temporal | Mostrar fechas y advertencias; no mezclar periodos sin documentarlo |
| Ausencia de ventas propias | No se puede calibrar contra conversión real | Tratar el IPA como priorización relativa, no pronóstico |
| Ingreso no disponible a granularidad compatible | Pérdida de una variable del modelo | Escalar decisión al cliente antes de sustituir; recalcular pesos aprobados |
| Cobertura incompleta de DENUE | Subestimación de competencia/contexto | Declarar clases incluidas, fecha y limitaciones |
| Tratamiento ambiguo de unidades de salud | Sesgo del IPA | Reportarlas por separado y validar su papel antes de incorporarlas |
| Ranking sensible a pesos | Recomendación inestable | Análisis de sensibilidad y etiqueta de estabilidad |
| Retrasos en aprobaciones | Afectación del cronograma | Gates, responsables y fecha límite de comentarios |
| Confusión entre score y rentabilidad | Decisión de negocio incorrecta | Disclaimer visible y siguiente fase de validación en campo |

## 14. KPIs de éxito y cierre

- **Cobertura:** 100 % de zonas seleccionadas procesadas con la misma metodología.
- **Trazabilidad:** 100 % de variables finales con fuente, fecha y transformación documentada.
- **Ranking:** mínimo 10 zonas con IPA 0–100 y explicación.
- **Usabilidad:** mapa interpretable por usuario no técnico en menos de 5 minutos.
- **Reproducibilidad:** ejecución por tercero en menos de 1 hora siguiendo el README.
- **Estabilidad:** resultados de sensibilidad reportados para las zonas finalistas.
- **Transparencia:** limitaciones y supuestos visibles en mapa, README y resumen ejecutivo.

## 15. Recomendación de uso del resultado

El ranking deberá utilizarse para seleccionar un grupo reducido de zonas candidatas —por ejemplo, Top 3 o Top 5— que avancen a una segunda fase de **due diligence comercial**. Esa fase, fuera del alcance actual, podría incorporar rentas, flujo peatonal, accesibilidad, seguridad, visibilidad, estacionamiento, oferta inmobiliaria, competencia no registrada y visitas de campo.

De esta forma, el proyecto reduce el espacio de búsqueda con evidencia pública sin atribuir al modelo una precisión que no puede sostener con los datos disponibles.

## 16. Aprobación

La ejecución inicia tras la adjudicación y la confirmación escrita del alcance, calendario, presupuesto y decisiones pendientes. La aceptación final se realizará contra los criterios de la sección 7.

| Por Pharmacy Pulse | Por el equipo del proyecto |
|---|---|
| Nombre: __________________________ | **Karen Pamela Rico Juárez** |
| Cargo: ___________________________ | Project Owner |
| Fecha: ___________________________ | Fecha: ___________________________ |
| Firma: ___________________________ | Firma: ___________________________ |
