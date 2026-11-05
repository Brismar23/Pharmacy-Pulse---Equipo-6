# Documentación del diagrama de arquitectura

Diagrama de la plataforma de datos de Pharmacy Pulse en AWS.

- **Archivo del diagrama:** [`diagrama-arquitectura.json`](diagrama-arquitectura.json)
- **Cómo abrirlo:** en [Diagramon](https://github.com/dataengileb/diagramon), abrir `index.html` y usar **Import**.
- **Fuente:** [`SOW.md`](SOW.md) v2.0, secciones 5 (arquitectura de datos) y 9 (repositorio).

---

## 1. Componentes

### Fuera de AWS

| Componente | Función | SOW |
|---|---|---|
| INEGI | Fuente: Censo, DENUE (CSV completo) y Marco Geoestadístico | 6.1 |
| `make pipeline` | Ejecuta `src/01_extract` a `05_map` (Python) | 5.3 |
| Reglas de calidad | Reglas R1 a R8, en cada carga | 6.3 |
| DuckDB | Consulta SQL sobre los Parquet | 5.4 |
| Mapa y ranking | `ranking.csv` y mapa estático | 3, 8 |
| Pharmacy Pulse | Recibe ranking, mapa y resumen ejecutivo | 1, 8 |

### Dentro de AWS

| Componente | Función | SOW |
|---|---|---|
| CloudFormation | `infra/template.yaml` crea buckets, IAM y presupuesto | 5.2 |
| IAM | Rol de mínimo privilegio para el pipeline | 5.2 |
| AWS Budgets | Tope de USD 5, alerta al 80 % | 5.5 |
| S3 `raw` | Descargas por fuente y fecha, inmutables | 5.1, 6.6 |
| S3 `clean` | Parquet tipado y homologado | 5.1 |
| S3 `curated` | Parquet con indicadores e IPA | 5.1 |
| Athena (opcional) | Alternativa a DuckDB, sin Glue Crawler | 5.4 |

---

## 2. Flujo de datos

| Paso | De | A | Qué ocurre |
|:---:|---|---|---|
| 1 | INEGI | `make pipeline` | Descarga de CSV y SHP |
| 2 | `make pipeline` | S3 `raw` | `01_extract` guarda en `raw/<fuente>/<fecha>/` |
| 3 | S3 `raw` | `make pipeline` | `02_clean` lee los datos originales |
| 4 | `make pipeline` | S3 `clean` | Escribe Parquet tipado |
| 5 | S3 `clean` | `make pipeline` | `03_indicators` y `04_scoring` calculan el IPA |
| 6 | `make pipeline` | S3 `curated` | Escribe la tabla final |
| 7 | S3 `curated` | DuckDB | Consulta SQL |
| 8 | DuckDB | Mapa y ranking | `05_map` genera las salidas |

Las líneas punteadas del diagrama son de control, no de datos:

- **valida:** las reglas de calidad revisan `clean` y `curated`.
- **crea:** CloudFormation despliega buckets, IAM y presupuesto.

---

## 3. Cumplimiento del SOW

| Requisito del SOW | Cómo lo refleja el diagrama | SOW |
|---|---|---|
| Pipeline reproducible en AWS | S3 en tres zonas, dentro de cuenta y región | 1 |
| Scripts leen y escriben en S3, no en disco local | Los pasos 2 a 6 van contra los buckets | 5.1 |
| Infraestructura como código | CloudFormation crea S3, IAM y Budgets | 5.2 |
| Rol IAM de mínimo privilegio | Nodo IAM; el pipeline asume el rol | 5.2 |
| Costo de $0 efectivo con alerta | AWS Budgets, tope USD 5; S3 con costo 0 | 5.5 |
| Ejecución por comando | `make pipeline` local, sin Lambda ni EventBridge | 5.3 |
| DuckDB base, Athena alternativa | DuckDB local; Athena marcado opcional; sin Glue | 5.4 |
| Reglas de calidad en cada carga | Nodo de reglas que valida `clean` y `curated` | 6.3 |
| Sin aplicación web ni servidor | Sin cómputo permanente en AWS; mapa estático | 4 |

---

## 4. Alcance y límites del diagrama

- **Región:** el SOW no la fija. Se decide en el Gate 1.
- **Procesos, no componentes:** el linaje, el versionado de `raw` por fecha y la etiqueta de confianza (SOW 6.4 a 6.6) no se dibujan como nodos.
- **Sustituto de ingreso:** se define en el hito 1 (SOW 7.5) y no aparece.
- **Ícono de AWS Budgets:** Diagramon no trae uno oficial; usa uno genérico.
- **Costo de S3:** el valor 0 es un supuesto del free tier. El SOW pide revisarlo antes del Gate 1.
- **Servicios no incluidos:** VPC, KMS, CloudWatch y Lambda, porque el SOW no los contempla.
- **Estado:** el JSON es válido y sus referencias existen. Falta confirmar que Diagramon lo importa sin avisos.
