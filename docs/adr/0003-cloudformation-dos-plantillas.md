# ADR 0003: CloudFormation en dos plantillas (buckets y Lambdas)

* **Estado:** Propuesto
* **Fecha:** 2026-11-18
* **Relacionado:** [ADR 0002](0002-lambda-vs-glue.md), SOW 5.2

## Contexto

El SOW v2.0 proponía una sola plantilla `infra/template.yaml`. Con cuatro Lambdas, la plantilla crece y mezcla dos cosas con ciclos de vida distintos: **los datos** (que no se deben borrar nunca por accidente) y **el cómputo** (que se actualiza seguido).

## Decisión

Dos plantillas de CloudFormation, desplegadas en orden:

1. **`infra/Buckets.yaml`** (stack `pharmacy-pulse-dev-storage`): buckets `bronze`, `silver`, `gold` y `artifacts`, con versionado, cifrado, bloqueo de acceso público, solo HTTPS, reglas de ciclo de vida y notificaciones a EventBridge. Los buckets de datos tienen `DeletionPolicy: Retain`.
2. **`infra/Lambdas.yaml`** (stack `pharmacy-pulse-dev-lambdas`): las cuatro funciones, un rol IAM por función con mínimo privilegio, reglas de EventBridge, calendario opcional, tema SNS de alertas, alarmas de errores y el AWS Budget (tope USD 5, alerta al 80 %). Importa los nombres de los buckets con `Fn::ImportValue`.

`scripts/deploy.sh` hace todo en orden; también se puede hacer desde la consola de CloudFormation.

## Por qué

* Se puede borrar y volver a crear el stack de Lambdas sin tocar los datos.
* Cada plantilla se entiende sola y es más fácil de revisar en clase.
* Mismo patrón que el proyecto de referencia del curso.
* CloudFormation, no Terraform ni CDK: nativo de AWS, sin estado externo que guardar y alineado con el curso (SOW 5.2).

## Consecuencias

* El stack de buckets no se puede borrar mientras el de Lambdas importe sus salidas (es una protección, no un problema).
* CloudFormation no detecta un zip nuevo si la ruta en S3 es la misma; por eso `deploy.sh` llama a `aws lambda update-function-code` al final.
* El Budget necesita un correo (`AlertEmail`); si no se da, no se crea.
