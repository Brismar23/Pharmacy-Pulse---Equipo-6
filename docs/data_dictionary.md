# Diccionario de datos y linaje

Responde en un minuto a la pregunta "¿de dónde salió este puntaje?" (SOW 6.5).

## Fuentes (fichas de control)

| Campo | Censo 2020, AGEB y manzana urbana | DENUE, CDMX |
|---|---|---|
| Procedencia | INEGI, Censo de Población y Vivienda 2020 | INEGI, Directorio Estadístico Nacional de Unidades Económicas |
| URL | `.../ccpv/2020/datosabiertos/ageb_manzana/ageb_mza_urbana_09_cpv2020_csv.zip` | `.../masiva/denue/denue_09_csv.zip` (edición vigente) |
| Fecha de referencia | 15 de marzo de 2020 | Edición vigente al descargar (cabecera `Last-Modified` en el manifiesto) |
| Fecha de descarga | `fecha=` en la ruta de bronze y en el manifiesto | igual |
| Unidad geográfica | AGEB urbana (fila con `MZA = 000`) | Establecimiento con coordenadas y clave de AGEB |
| Variables usadas | `POBTOT`, `P_60YMAS`, `P_0A2`, `PDER_SS`, `PSINDER`, `GRAPROES`, `TVIVPARHAB`, `VPH_AUTOM`, `VPH_INTER`, `VPH_PC`, `PAFIL_IPRIV` y grupos de edad (`P_3A5` … `POB65_MAS`) | `id`, `nom_estab`, `codigo_act`, `cve_ent`, `cve_mun`, `ageb`, `nomb_asent`, `latitud`, `longitud` |
| Valores especiales | `*` = confidencial (menos de 3 unidades); `N/D` = no disponible. Se tratan como faltantes. | Coordenadas fuera de la CDMX se descartan (R2); `id` repetido se elimina (R6). |
| Limitaciones | Tiene 6 años; no trae ingreso. | Solo negocios registrados; puede faltar competencia informal. |
| Integridad | `sha256` y tamaño en `bronze/_manifiestos/fecha=...json` | igual |

## Linaje: de la fuente al ranking

| Columna final (gold) | Silver | Bronze / fuente | Transformación | Usada en |
|---|---|---|---|---|
| `cvegeo` | `censo_ageb.cvegeo` | Censo `ENTIDAD+MUN+LOC+AGEB` | Concatenación con ceros a la izquierda | R1, llave de todas las tablas |
| `alcaldia` | `censo_ageb.alcaldia` | Censo `MUN` | Catálogo de las 16 alcaldías; parámetro `Alcaldias` (default: las 6 del RFP) | Mapa, ranking |
| `colonia_referencia` | `denue_ageb.colonia_principal` | DENUE `nomb_asent` | Colonia más frecuente entre los establecimientos de la AGEB | Mapa, ranking (solo referencia) |
| `poblacion` | `censo_ageb.pobtot` | Censo `POBTOT` | Sin cambio | `n_poblacion`, R3, R4 |
| `pct_60ymas` | `censo_ageb.p_60ymas` | Censo `P_60YMAS` | `100 · P_60YMAS / POBTOT` | `n_edades` |
| `escolaridad` | `censo_ageb.graproes` | Censo `GRAPROES` | Sin cambio | `n_ingreso` |
| `pct_viv_auto`, `pct_viv_internet`, `pct_viv_pc` | `censo_ageb.vph_*` | Censo `VPH_AUTOM`, `VPH_INTER`, `VPH_PC`, `TVIVPARHAB` | `100 · VPH_* / TVIVPARHAB` | `n_ingreso` = promedio normalizado de escolaridad y estas 3 (D2) |
| `pct_afiliada_salud` | `censo_ageb.pder_ss` | Censo `PDER_SS` | `100 · PDER_SS / POBTOT` | Solo contexto |
| `lat`, `lon` | `denue_ageb.lat/lon` | DENUE `latitud/longitud` | Promedio de los establecimientos de la AGEB | Punto del mapa, radio |
| `farmacias_radio` | `denue_puntos` (tipo farmacia) | DENUE `codigo_act` 464111/464112 | Conteo a menos de `RADIO_M` metros (haversine) | `n_competencia` |
| `salud_radio` | `denue_puntos` (tipo salud) | DENUE `codigo_act` 621*/622* | Conteo a menos de `RADIO_M` metros | `n_salud` |
| `farmacias`, `unidades_salud` | `denue_ageb` | DENUE | Conteo dentro de la AGEB | Solo contexto |
| `n_*` | — | — | Min-max 0-100 recortado a percentiles 5-95; competencia invertida | IPA, R5 |
| `ipa` | — | — | Suma ponderada con `PESOS_IPA`; reponderada si falta un componente | Ranking, mapa, R5 |
| `confianza` | — | — | Alta/Media/Baja según faltantes, N/D y R7 | Ranking, mapa |
| `por_que` | — | — | Dos componentes con mayor aporte y el más débil, en texto | Ranking, mapa |
| `version_raw` | manifiesto | fecha de descarga | — | Reproducibilidad (SOW 6.6) |

## Tablas por capa

| Capa | Ruta | Descripción |
|---|---|---|
| bronze | `censo/fecha=F/*.zip`, `denue/fecha=F/*.zip` | Archivos originales, nunca se modifican |
| bronze | `_manifiestos/fecha=F.json` | URL, tamaño, sha256 y `Last-Modified` de cada fuente |
| silver | `censo_ageb/version=F/censo_ageb.csv` | Una fila por AGEB urbana de las 6 alcaldías |
| silver | `censo_totales/version=F/censo_totales.csv` | Totales oficiales por alcaldía (R4) |
| silver | `denue_ageb/version=F/denue_ageb.csv` | Conteos DENUE y punto representativo por AGEB |
| silver | `denue_puntos/version=F/denue_puntos.csv` | Farmacias y unidades de salud con coordenadas |
| silver | `calidad/version=F/limpieza.json` | R2, R6 y conteos de la limpieza |
| gold | `zonas_ipa/version=F/zonas_ipa.csv` | Todas las AGEB con indicadores, IPA y confianza |
| gold | `ranking/version=F/ranking.csv`, `ranking/actual/ranking.csv` | Top N (al menos 10) |
| gold | `calidad/version=F/reporte.json` | Todas las reglas y el estado de la carga |
| gold | `mapa/actual/index.html`, `resumen/actual/resumen.md` | Mapa estático y resumen automático |

## Reglas de calidad (SOW 6.3)

| # | Regla | Umbral | Acción | Dónde corre |
|---|---|---|---|---|
| R1 | `CVEGEO` único en curated | 0 duplicados | Bloquea | `indicadores` |
| R2 | Coordenadas DENUE válidas dentro de la CDMX | 100 % de los retenidos | Bloquea | `limpieza` |
| R3 | AGEB con población | ≥ 95 % | Bloquea | `indicadores` |
| R4 | Suma de población por AGEB vs. total urbano de la alcaldía | ±1 % | Bloquea | `indicadores` |
| R5 | Indicadores e IPA en 0-100 | 100 % | Bloquea | `indicadores` |
| R6 | Duplicados DENUE tras limpieza | 0 | Marca | `limpieza` |
| R7 | Antigüedad: Censo ≤ 10 años, DENUE ≤ 24 meses | — | Marca | `indicadores` |
| R8 | AGEB elegibles con todas las variables | ≥ 80 % | Marca y activa plan B | `indicadores` |
| N1 | Zonas en el ranking | ≥ 10 | Bloquea | `indicadores` |
