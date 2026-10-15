# Declaración de trabajo (SOW)

## Proyecto: análisis de zonas para la primera sucursal de Pharmacy Pulse

| Dato | Detalle |
|---|---|
| **Cliente** | Pharmacy Pulse |
| **Contacto del cliente** | Caleb Aguilar Camargo |
| **Equipo propuesto** | Brisa (liderazgo del proyecto), Ana Pau (análisis de datos), Pam (redacción y documentación) y Javier (mapa y revisión técnica) |
| **Fecha objetivo de entrega** | 29 de enero de 2027 |

> Este documento concreta el alcance solicitado en el RFP. Las decisiones que el RFP deja abiertas —como el nivel geográfico, las categorías de competencia y las ponderaciones del puntaje— deberán confirmarse con Pharmacy Pulse antes del análisis. El precio desglosado es una distribución presupuestal de referencia, no una cotización aprobada.

## 1. Propósito y objetivos

Pharmacy Pulse aún no tiene sucursales ni datos propios de ventas. El proyecto analizará datos públicos para comparar zonas de seis alcaldías de la Ciudad de México e identificar dónde convendría explorar la apertura de la primera sucursal en 2027. El resultado será una recomendación relativa entre las zonas estudiadas, no una garantía de ventas ni una selección de un local comercial específico.

Al cierre, el proyecto deberá:

1. Entregar un ranking de al menos 10 zonas, cada una con un puntaje de potencial de 0 a 100 y una explicación comprensible.
2. Mostrar un indicador de demanda y conteos de farmacias y unidades de salud para las zonas del ranking.
3. Permitir que el equipo consulte y entienda los resultados en un mapa en menos de 5 minutos, sin ayuda técnica.
4. Permitir que una persona siga las instrucciones del repositorio y repita el análisis en menos de 1 hora.

## 2. Alcance del trabajo

### Incluye

- Delimitar y comparar zonas dentro de Benito Juárez, Coyoacán, Tlalpan, Iztapalapa, Gustavo A. Madero y Álvaro Obregón.
- Identificar, descargar y documentar datos públicos pertinentes del INEGI:
  - Censo de Población y Vivienda para población y estructura por edades.
  - DENUE para ubicar y contar farmacias y unidades de salud.
  - Datos públicos disponibles de ingresos por zona, indicando su fuente, fecha y nivel geográfico.
- Revisar cobertura, fechas, definiciones y limitaciones de las fuentes; preparar los datos para el análisis y conservar la trazabilidad de las transformaciones.
- Proponer y documentar una metodología de puntaje interpretable que combine demanda y presión competitiva, sin presentarla como pronóstico de ventas.
- Generar el ranking, sus indicadores y sus explicaciones.
- Crear un mapa sencillo para consultar y comparar las zonas.
- Preparar un repositorio de GitHub con datos públicos utilizados, código y un README en español que explique cómo repetir el análisis.
- Entregar un resumen ejecutivo de máximo 2 páginas y presentar los resultados al equipo de Pharmacy Pulse.

### Fuera de alcance

- Buscar, inspeccionar, seleccionar, arrendar o negociar locales específicos.
- Tramitar licencias, permisos o autorizaciones sanitarias.
- Recomendar surtido, inventario, precios, personal o estrategia comercial.
- Elaborar proyecciones financieras detalladas, estimaciones de ventas o rentabilidad.
- Obtener datos privados de clientes, ventas, afluencia peatonal, rentas o establecimientos no registrados.
- Garantizar que la zona mejor calificada sea rentable o que los datos públicos reflejen la situación actual en campo.

## 3. Fuentes de datos y metodología

Se priorizarán las fuentes públicas del INEGI indicadas en el RFP. Para cada conjunto se anotarán la fuente, fecha de publicación o referencia temporal, variables usadas, cobertura geográfica y limitaciones. Si los datos de ingresos no están disponibles con el detalle geográfico acordado, se informará al cliente y se propondrá una alternativa antes de sustituirlos.

### Unidad geográfica y competencia

El nivel de análisis (alcaldía, colonia o AGEB) se definirá durante la validación inicial. Para alcanzar al menos 10 zonas dentro de las seis alcaldías y permitir la comparación, se propone evaluar AGEB urbanas cuando las fuentes tengan cobertura compatible. La elección definitiva y cualquier agrupación de unidades deberán aprobarse antes de calcular el ranking.

El equipo y el cliente acordarán qué categorías y actividades del DENUE se tratarán como competencia, así como la forma de asociar establecimientos con cada zona. El resultado reportará por separado los conteos de farmacias y unidades de salud y dejará explícitas las categorías incluidas. No se asumirá que el DENUE contiene todos los consultorios, tiendas con venta de medicamentos, hospitales o clínicas privadas.

### Puntaje propuesto

Como punto de partida sujeto a aprobación del cliente, se propone un puntaje compuesto por:

- **Demanda estimada (70 %):** población (30 %), composición por edades (15 %), ingresos (15 %) y acceso a servicios de salud (10 %).
- **Presión competitiva (30 %):** conteos de farmacias y unidades de salud, con mayor presión competitiva reduciendo el puntaje.

Cada indicador se expresará en una escala relativa de 0 a 100 respecto de las zonas comparadas. El puntaje final también irá de 0 a 100. El informe explicará los pesos, las reglas de cálculo y qué significan; el cliente deberá aprobarlos antes de la clasificación final. Este resultado sirve para priorizar investigación, no equivale a una probabilidad de éxito. Si una variable no es comparable o no está disponible, su tratamiento se acordará y documentará, sin inventar datos.

## 4. Entregables y criterios de aceptación

| Entregable | Criterio de aceptación |
|---|---|
| Definición de zonas, fuentes y metodología | Cliente valida por escrito el nivel geográfico, las categorías DENUE y las reglas de puntuación antes del análisis definitivo. |
| Ranking e indicadores | Al menos 10 zonas; puntaje de 0 a 100, indicador de demanda, conteos separados de farmacias y unidades de salud, y explicación de los factores que influyen en cada resultado. |
| Mapa | Se abre con instrucciones sencillas y permite a un integrante del equipo localizar una zona e interpretar sus resultados en menos de 5 minutos, sin asistencia técnica. |
| Repositorio de GitHub | Incluye el código, los datos públicos usados y un README en español; una persona distinta del autor puede reproducir el análisis siguiendo el README en menos de 1 hora. |
| Resumen ejecutivo | Máximo 2 páginas; presenta la recomendación, sus razones, limitaciones y próximos pasos sugeridos. |
| Presentación de resultados | Sesión de presentación al equipo de Pharmacy Pulse, con oportunidad para preguntas. |

Los criterios se verificarán en una revisión final con el cliente. Los cambios que amplíen las zonas, las fuentes o los entregables requerirán acuerdo de ambas partes sobre su efecto en costo y fecha.

## 5. Calendario propuesto

Las fechas del proceso de selección son las del RFP. Las fases de ejecución siguientes son propuestas y dependen de la adjudicación del 9 de noviembre de 2026 y de la disponibilidad del cliente.

| Fase | Fechas propuestas | Actividades y salida |
|---|---|---|
| Inicio y definición | 10–20 de noviembre de 2026 | Reunión de arranque; confirmar zonas, nivel geográfico, categorías DENUE, metodología, responsables y accesos. |
| Fuentes y preparación | 23 de noviembre–4 de diciembre de 2026 | Recopilar fuentes, revisar cobertura y antigüedad, preparar datos y reportar vacíos. |
| Análisis y mapa | 7 de diciembre de 2026–8 de enero de 2027 | Calcular indicadores, aplicar puntaje aprobado, preparar ranking y construir el mapa. |
| Revisión con cliente | 11–15 de enero de 2027 | Revisar resultados preliminares, registrar observaciones y acordar correcciones dentro del alcance. |
| Entrega y presentación | 18–29 de enero de 2027 | Publicar los entregables, validar criterios de aceptación y presentar resultados. |

Las fechas intermedias se ajustarán de común acuerdo si la disponibilidad de datos, los periodos vacacionales o las revisiones del cliente afectan el calendario. La fecha objetivo final del RFP es el 29 de enero de 2027.

## 6. Responsabilidades y comunicación

### Equipo del proyecto

- **Brisa, líder del proyecto:** coordinar calendario, decisiones, entregas y comunicación.
- **Ana Pau, análisis de datos:** revisar y preparar las fuentes y calcular los indicadores y el ranking.
- **Pam, redacción y documentación:** documentar metodología, limitaciones, README y resumen ejecutivo.
- **Javier, mapa y revisión técnica:** preparar el mapa y revisar la reproducibilidad técnica.

### Pharmacy Pulse

- Nombrar una persona responsable de aprobar decisiones y entregables.
- Facilitar oportunamente la definición de zonas prioritarias y resolver las preguntas sobre el uso previsto del análisis.
- Revisar y aprobar el nivel geográfico, las categorías de competencia y las ponderaciones antes del cálculo definitivo.
- Consolidar comentarios y devolverlos en las fechas acordadas.
- Compartir cualquier plan de negocio o información interna solo bajo un acuerdo de confidencialidad; dicha información no se incluirá en el repositorio público.

Se propone una reunión de arranque, una revisión de avance por fase y una presentación final. Las aprobaciones y cambios de alcance deberán quedar documentados por escrito.

## 7. Presupuesto y costos de operación

El presupuesto máximo indicado por el cliente es de **$120,000 MXN**. La estimación considera aproximadamente un mes de trabajo del equipo, con dedicación parcial distribuida entre sus cuatro integrantes. Las horas y tarifas son supuestos de planeación que deberán validarse en la propuesta económica definitiva; no representan una cotización aceptada.

| Integrante / partida | Horas estimadas | Tarifa estimada | Importe estimado |
|---|---:|---:|---:|
| Brisa — coordinación y gestión | 60 | $250 MXN/h | $15,000 MXN |
| Ana Pau — análisis y preparación de datos | 140 | $250 MXN/h | $35,000 MXN |
| Pam — redacción y documentación | 100 | $200 MXN/h | $20,000 MXN |
| Javier — mapa y revisión técnica | 140 | $250 MXN/h | $35,000 MXN |
| **Subtotal del equipo (440 horas)** |  |  | **$105,000 MXN** |
| AWS durante implementación (configuración y primer mes, estimado) |  |  | $1,000 MXN |
| Reserva para variaciones de costos |  |  | $14,000 MXN |
| **Total máximo de referencia** |  |  | **$120,000 MXN** |

Para la operación posterior se estima un costo recurrente de AWS de **$300–$1,000 MXN al mes**, sujeto al tráfico, almacenamiento, región, tipo de cambio e impuestos. El supuesto es publicar el mapa y sus archivos como contenido estático en servicios administrados como Amazon S3 y CloudFront, sin mantener un servidor encendido; el dominio, si se requiere, se cotizará por separado y deberá aprobarse antes de contratarse. El gasto mensual deberá mantenerse por debajo del máximo de **$2,000 MXN** indicado en el RFP. La estimación no es una cotización de AWS ni presupone que aplique una capa gratuita. La propuesta económica definitiva deberá confirmar impuestos y costos aplicables, y cualquier servicio de pago o gasto que rebase la reserva deberá aprobarse previamente.

## 8. Supuestos, riesgos y mitigación

| Supuesto o riesgo | Tratamiento |
|---|---|
| Algunas fuentes pueden tener varios años de antigüedad. | Mostrar la fecha de referencia y advertir que la situación actual puede diferir. |
| No existen datos propios de ventas ni clientes. | Usar indicadores públicos como aproximaciones comparativas, no como pronósticos. |
| Ingresos, población y establecimientos pueden estar publicados a distintos niveles geográficos o periodos. | Verificar compatibilidad antes de puntuar; documentar y acordar cualquier alternativa. |
| El DENUE puede no registrar todos los competidores o servicios privados. | Describir las categorías y exclusiones; reportar los conteos como cobertura del directorio, no como censo perfecto. |
| El flujo peatonal, las rentas y algunos establecimientos no registrados no están disponibles. | Excluirlos del cálculo y mencionarlos como factores que el cliente deberá investigar en una fase posterior. |
| El cliente tarda en resolver decisiones o revisar resultados. | Acordar responsables y fechas de revisión al inicio; ajustar hitos intermedios de común acuerdo. |
| Un puntaje relativo puede interpretarse como garantía de éxito. | Explicar los pesos, limitaciones y carácter comparativo en el mapa y los informes. |

El repositorio público contendrá únicamente datos públicos, código y resultados autorizados. No se incorporarán datos confidenciales del negocio.

## 9. Aprobación

La ejecución comienza tras la adjudicación y la confirmación por escrito del alcance, calendario, presupuesto y decisiones pendientes descritas en este documento. La aceptación final se realizará contra los criterios de la sección 4.

| Por Pharmacy Pulse | Por el equipo del proyecto |
|---|---|
| Nombre: ____________________ | Nombre: ____________________ |
| Cargo: _____________________ | Cargo: _____________________ |
| Fecha: _____________________ | Fecha: _____________________ |
| Firma: _____________________ | Firma: _____________________ |
