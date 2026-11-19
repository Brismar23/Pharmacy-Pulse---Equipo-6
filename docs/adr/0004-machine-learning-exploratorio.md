# ADR 0004: Machine learning solo como análisis exploratorio, fuera del pipeline

* **Estado:** Propuesto
* **Fecha:** 2026-11-18
* **Relacionado:** [ADR 0001](0001-alcance-y-complejidad-del-calculo.md), [ADR 0002](0002-lambda-vs-glue.md), [fuentes y extracción](../datos/fuentes_y_extraccion.md)

## Contexto

El ADR 0001 dejó fuera el machine learning del IPA porque no hay ventas con las que entrenar ni validar un pronóstico. Aun así quedaban dos preguntas que el ranking no responde bien:

1. **¿Qué tipos de zona hay?** El fundador no piensa en 2,300 AGEB sino en "zonas residenciales", "zonas populares saturadas", etc.
2. **¿Dónde hay zonas parecidas a las que ya tienen muchas farmacias, pero sin farmacias?** Es decir, demanda probada (por zonas gemelas) y casi sin competencia.

Las dos se pueden contestar **sin ventas**: la primera agrupa zonas por sus datos, la segunda usa como objetivo algo que sí observamos (cuántas farmacias hay a 500 m).

## Decisión

Agregamos un análisis exploratorio en `scripts/analisis/` que **no corre en AWS ni cambia el IPA**. Se ejecuta en una computadora con `make analisis` y produce gráficas, una tabla y la demo web.

| Pregunta | Método | Detalle | Cómo se valida |
|---|---|---|---|
| Tipos de zona | **k-means**, k = 5 | 11 variables estandarizadas (población en log, % 60+, % 0-2, escolaridad, % auto, % internet, % computadora, % seguro privado, % afiliada, farmacias y consultorios a 500 m). `n_init = 50`, semilla 0. **PCA** a 2 dimensiones solo para dibujar. | Silueta 0.19 (grupos que se traslapan, esperable en una ciudad continua); los nombres salen de reglas sobre el perfil promedio, no a mano. |
| Hueco de farmacias | **Random forest** de regresión | Predice farmacias a 500 m con 11 variables de gente y comercio. **Sin coordenadas ni consultorios** (los consultorios a 500 m hacían el modelo circular). 500 árboles, `min_samples_leaf = 5`. | Validación cruzada de 5 particiones: R² = 0.385. Las predicciones son de la partición que el modelo no vio. |
| Zonas gemelas | **Vecinos más cercanos** (k = 10) | Las 10 zonas más parecidas en gente y comercio. | Se reporta la mediana de farmacias de las gemelas. |
| Oportunidad | Regla | hueco ≥ 3 farmacias **y** farmacias ≤ mitad de la mediana de sus gemelas **y** ≥ 1,500 habitantes | 310 zonas. Se revisan a mano en Google Maps: 8 de 20 sin farmacia a 500 m. |

## Por qué así

* **Conserva el ADR 0001**: el IPA sigue siendo una suma ponderada explicable; el ML solo agrega contexto (tipo de zona) y una segunda lista (huecos).
* **El objetivo del modelo es observable**: no predecimos ventas, predecimos competencia "normal" para una zona así. La diferencia con la real es una señal, no un pronóstico.
* **R² de 0.385 es suficiente para señalar, no para decidir**: por eso cada hueco se confirma en Google Maps y después en campo.
* **No va en Lambda**: scikit-learn, pandas, SciPy y matplotlib juntos rebasan el límite de 250 MB de un paquete de Lambda; meterlos rompería la decisión de Lambdas sin capas (ADR 0002). El análisis se corre pocas veces y en segundos (≈ 30 s) en una laptop.
* **Reproducible**: semillas fijas, entrada versionada en `data/extraido/` con SHA-256, salida determinista.

## Consecuencias

* Hay dos entregables que conviven: el **ranking IPA** (pipeline AWS, oficial) y el **análisis exploratorio** (gráficas, tabla y demo).
* Si un día hay ventas reales de la primera sucursal, el siguiente paso es un modelo supervisado de ventas; este ADR se reemplaza.
* Riesgo: que se lea el hueco como "aquí se venderá". Se mitiga con el texto de las gráficas y la verificación obligatoria.

## Alternativas descartadas

* **DBSCAN / clustering jerárquico**: más difícil de explicar y de fijar el número de grupos.
* **Regresión lineal / Poisson** para el hueco: más simple de explicar, pero no capta interacciones (por ejemplo, comercio × auto) sin construirlas a mano.
* **Modelo de Huff o de gravedad**: necesita tiempos de traslado y atractivo por tienda que no tenemos (ADR 0001).
