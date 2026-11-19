# ADR 0002: AWS Lambda frente a AWS Glue para bronze → silver → gold

* **Estado:** Propuesto
* **Fecha:** 2026-11-18
* **Relacionado:** [ADR 0001](0001-alcance-y-complejidad-del-calculo.md), [ADR 0003](0003-cloudformation-dos-plantillas.md)

## Contexto

El SOW v2.0 (5.3) proponía correr el pipeline en la laptop con `make pipeline`. Para que el cliente pueda repetir la carga sin depender de la computadora de nadie, el procesamiento se mueve a AWS. Las dos opciones naturales son **AWS Lambda** y **AWS Glue** (Spark o Python shell).

Tamaño real del problema:

| Fuente | Registros que nos importan | Tamaño |
|---|---|---|
| Censo 2020 por AGEB y manzana, CDMX | unas 70 mil filas; usamos unas 1,000 AGEB | decenas de MB |
| DENUE CDMX (edición vigente) | unos 500 mil establecimientos; nos quedamos con 6 alcaldías | cientos de MB sin comprimir |
| Frecuencia | pocas cargas al año (el DENUE se actualiza 1-2 veces al año; el Censo, cada 10 años) | — |

## Decisión

Usar **AWS Lambda (Python 3.13, solo biblioteca estándar)**, una función por capa:

| Lambda | Disparador | Lee | Escribe |
|---|---|---|---|
| `ingesta` | A mano (o calendario trimestral, apagado por defecto) | INEGI | bronze |
| `limpieza` | Manifiesto nuevo en bronze (EventBridge) | bronze | silver |
| `indicadores` | Manifiesto nuevo en silver | silver | gold |
| `mapa` | Manifiesto nuevo en gold | gold (+ puntos de silver) | gold |

Cada función escribe en un bucket distinto del que la dispara, y el disparo es por el **manifiesto**, que se escribe al final: nunca se procesa una carga a medias y ninguna función se dispara a sí misma.

## Justificación

* **El volumen es chico.** Medimos con 524 mil registros del DENUE: la limpieza tarda unos 5 s y usa 106 MB. La Lambda tiene 2 GB, 3 GB de disco temporal y hasta 15 minutos. Hay margen de sobra; Spark está pensado para gigas o teras repartidos en varios nodos.
* **Costo.** Una carga completa consume unos 250 GB-segundo de Lambda; la capa gratuita es de 400,000 GB-segundo al mes, y sin ella costaría menos de un centavo de dólar. Glue cobra USD 0.44 por DPU-hora, por segundo con mínimo de 1 minuto, y Spark exige al menos 2 DPU; no tiene capa gratuita para trabajos. Con tres trabajos por carga el costo sigue siendo bajo, así que **el costo no decide: decide la complejidad**.
* **Arranque.** Lambda arranca en milisegundos o pocos segundos; un trabajo de Spark en Glue tarda más en levantar el entorno que lo que tarda nuestro cálculo.
* **Menos cosas que aprender y operar.** Lambda se escribe y se prueba como Python normal (en este repo, `scripts/run_local.py` corre las cuatro funciones en la laptop). Glue agrega el modelo de jobs, el Data Catalog, conectores y, con Spark, el propio Spark.
* **Encaja con eventos.** Un objeto nuevo en S3 dispara la siguiente función con una regla de EventBridge, sin orquestador (no hace falta Step Functions ni Glue Workflows).
* **Una sola forma de empaquetar, desplegar y monitorear:** zips en `artifacts`, CloudFormation y alarmas de CloudWatch iguales para las cuatro.

## Alternativas consideradas

* **Glue con Spark:** sobredimensionado; mínimo 2 DPU y un entorno distribuido para un archivo que cabe en memoria.
* **Glue Python shell (0.0625 DPU):** es lo más cercano a Lambda y no tiene el límite de 15 minutos, pero agrega otro servicio, otro rol, otro empaquetado y no se dispara directo por eventos de S3.
* **Seguir con `make pipeline` local (SOW v2.0):** cero costo, pero la carga depende de la laptop de una persona y no queda en la nube del cliente.
* **ECS/Fargate o EC2:** más piezas (contenedores, redes) para el mismo resultado.

## Cuándo cambiaríamos a Glue

* Si el alcance crece a todo el país (unos 6 millones de establecimientos del DENUE) y la limpieza se acerca a los 15 minutos o a la memoria de Lambda.
* Si se agregan uniones espaciales pesadas con el Marco Geoestadístico completo.
* Si el cliente ya opera un Data Catalog y quiere todo bajo Glue.

Las métricas de CloudWatch (duración y memoria máxima por ejecución) dirán si nos acercamos a esos límites.

## Consecuencias

* Costo prácticamente cero, despliegue simple y pruebas locales sin AWS.
* Hay un techo (15 min, 10 GB): si el volumen crece mucho, se migra la capa afectada. Como cada capa se comunica por archivos en S3, la migración queda acotada a una función.
* Si INEGI bloquea descargas desde IPs de AWS, la ingesta acepta los zips subidos a mano (`solo_manifiesto`) y el resto del flujo no cambia.
