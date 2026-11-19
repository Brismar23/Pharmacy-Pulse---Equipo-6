# Fuentes de datos y cómo se extraen

Todo lo que usa Pharmacy Pulse es **público y gratuito**. No hay datos de clientes, ventas ni personas.

## 1. Fuentes

| # | Fuente | Qué trae | Archivo oficial | Tamaño | Versión usada |
|---|---|---|---|---|---|
| F1 | INEGI, **Censo de Población y Vivienda 2020**, principales resultados por AGEB y manzana urbana, CDMX | Población, edades, escolaridad, derechohabiencia y equipamiento de la vivienda por AGEB | [ageb_mza_urbana_09_cpv2020_csv.zip](https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/ageb_manzana/ageb_mza_urbana_09_cpv2020_csv.zip) | 13 MB (UTF-8) | Censo 2020 (única edición) |
| F2 | INEGI, **DENUE** (Directorio Estadístico Nacional de Unidades Económicas), CDMX | Cada negocio con actividad SCIAN, clave de AGEB, colonia y coordenadas | [denue_09_csv.zip](https://www.inegi.org.mx/contenidos/masiva/denue/denue_09_csv.zip) | 45 MB (latin-1) | Edición 05/2026 |
| F3 | **Google Maps** (consulta manual) | Confirmar que una zona candidata no tiene farmacia a 500 m | — | — | 2026-11-18 |

Licencia: los datos del INEGI son de libre uso citando la fuente ("Fuente: INEGI, Censo de Población y Vivienda 2020" e "INEGI, DENUE 05/2026").

### Qué se toma de cada fuente

* **Censo (F1)**: solo las filas de **AGEB** (`MZA = 000`, sin totales de localidad `AGEB = 0000` ni de municipio `LOC = 0000`). Columnas: `POBTOT`, `P_60YMAS`, `POB65_MAS`, `P_0A2`, `P_3A5`, `P_6A11`, `P_12A14`, `P_15A17`, `P_18A24`, `P_18YMAS`, `GRAPROES`, `PDER_SS`, `PDER_IMSS`, `PSINDER`, `PAFIL_IPRIV`, `TVIVPARHAB`, `VPH_AUTOM`, `VPH_INTER`, `VPH_PC`. Los totales por alcaldía (`LOC = 0000`) se guardan aparte para la regla R4.
* **DENUE (F2)**:
  * **Farmacias** = SCIAN **464111** (con minisúper) y **464112** (sin minisúper). Naturistas y ópticas no cuentan.
  * **Unidades de salud** = SCIAN **621\*** (consultorios, laboratorios) y **622\*** (hospitales). Generan recetas.
  * De cada una: `clee`, `nom_estab`, `codigo_act`, `cve_mun`, `ageb`, `nomb_asent` (colonia), `latitud`, `longitud`.

## 2. Dos formas de extraer (dan los mismos datos)

### A. Pipeline en AWS (producción)

La Lambda `ingesta` descarga los dos zips a **S3 bronze** (`censo/fecha=AAAA-MM-DD/`, `denue/fecha=AAAA-MM-DD/`) y escribe un manifiesto con URL, tamaño, `sha256` y `Last-Modified`. Bronze nunca se sobrescribe. Después `limpieza` → `indicadores` → `mapa` (ver [README](../../README.md)).

Si el INEGI bloquea la descarga desde AWS (pasa con algunas IP de nube), se suben los zips a mano y se llama a la ingesta con `{"solo_manifiesto": true}` (ver README, "Si INEGI bloquea la descarga").

### B. Desde el navegador (análisis de las 16 alcaldías)

El sitio del INEGI siempre responde a un navegador normal, así que la extracción del análisis se hizo con un script de consola, sin instalar nada:

1. Abrir <https://www.inegi.org.mx/app/descarga/?ti=6> en Chrome, Edge o Brave.
2. F12 → **Console** → pegar [`scripts/analisis/extraer_inegi_navegador.js`](../../scripts/analisis/extraer_inegi_navegador.js) → Enter.
3. El script:
   1. descarga los dos zips con `fetch` (misma página del INEGI, sin problemas de CORS);
   2. lee el directorio central del zip y descomprime el CSV en memoria con `DecompressionStream("deflate-raw")`;
   3. lee el Censo como UTF-8 y el DENUE como latin-1 (`TextDecoderStream`);
   4. se queda con las AGEB de la CDMX y con las farmacias y unidades de salud;
   5. resume el DENUE por AGEB (establecimientos, farmacias, colonia más frecuente, coordenada promedio);
   6. descarga 3 CSV.
4. Copiar los CSV a `data/extraido/`.

Tarda de 5 a 10 segundos. Para probar sin descargar archivos: `window.EXTRAER_SOLO_CONTAR = true` antes de pegarlo (deja los conteos en `window.EXTRACCION_PHARMACY_PULSE`).

### Archivos resultantes (`data/extraido/`)

| Archivo | Filas | Contenido | SHA-256 |
|---|---|---|---|
| `cdmx_zonas_inegi.csv` | 2,433 | Una fila por AGEB urbana de las 16 alcaldías: Censo + resumen DENUE | `a456c621…dbf150e`* |
| `cdmx_totales_alcaldias.csv` | 16 | Población oficial por alcaldía (para R4) | `f951c0d4…1f4e5b` |
| `cdmx_puntos_denue.csv` | 27,244 | 7,450 farmacias y 19,794 unidades de salud con coordenadas | `52d1a071…2eaada` |
| `verificacion_google_maps.csv` | 20 | Zonas candidatas revisadas a mano en Google Maps | `df0f203e…4938b9` |

\* Hashes completos: `sha256sum data/extraido/*.csv`. Volver a correr el extractor con la misma edición del DENUE produce **exactamente los mismos bytes** (se comprobó comparando los SHA-256).

Diccionario de columnas de `cdmx_zonas_inegi.csv`:

| Columna | Origen | Significado |
|---|---|---|
| `cvegeo` | Censo `ENTIDAD+MUN+LOC+AGEB` | Clave única de la AGEB (13 caracteres) |
| `cve_mun`, `alcaldia` | Censo `MUN` | Clave y nombre de la alcaldía |
| `colonia` | DENUE `nomb_asent` | Colonia más frecuente entre los negocios de la AGEB (referencia) |
| `nd` | Censo | Número de campos con `*` o `N/D` (dato reservado por confidencialidad) |
| `pob`, `p60`, `p65`, `p02` | `POBTOT`, `P_60YMAS`, `POB65_MAS`, `P_0A2` | Población total y por edad |
| `p35`, `p611`, `p1214`, `p1517`, `p1824`, `p18mas` | `P_3A5` … `P_18YMAS` | Grupos de edad para el filtro "De __ a __ años" |
| `esc` | `GRAPROES` | Años promedio de escolaridad |
| `der`, `sinder`, `priv`, `imss` | `PDER_SS`, `PSINDER`, `PAFIL_IPRIV`, `PDER_IMSS` | Derechohabiencia; `priv` = seguro privado |
| `viv`, `auto`, `inter`, `pc` | `TVIVPARHAB`, `VPH_AUTOM`, `VPH_INTER`, `VPH_PC` | Viviendas habitadas y con auto, internet, computadora |
| `establecimientos`, `farm_ageb` | DENUE | Negocios y farmacias dentro de la AGEB |
| `lat`, `lon` | DENUE | Promedio de coordenadas de los negocios de la AGEB (punto de la zona) |

## 3. Verificación con Google Maps (F3)

El DENUE solo tiene negocios registrados y se actualiza por ediciones, así que **toda zona que el modelo marca con hueco se confirma antes de recomendarla**:

1. Se toman las zonas candidatas (hueco ≥ 3 farmacias y ≥ 1,500 habitantes), empezando por las de mayor hueco.
2. En Google Maps se busca "farmacia" alrededor del punto de la zona y se mide la farmacia más cercana.
3. Se registra en `verificacion_google_maps.csv`: farmacias a 500 m, distancia a la más cercana y resultado.

Resultado: de 20 zonas revisadas, **8 no tienen ninguna farmacia a 500 m** y 12 sí tenían alguna (se descartan).

Límites: la búsqueda devuelve pocos resultados por consulta, así que **solo sirve para confirmar ausencia cerca**, no para contar toda la competencia. La revisión es de una fecha; antes de rentar local hay que ir a campo.

## 4. Calidad de los datos (resultados reales)

| Regla | Qué revisa | Resultado |
|---|---|---|
| R1 | `cvegeo` único | OK |
| R3 | Zonas con población válida ≥ 95 % | OK |
| R4 | Suma de población de las AGEB vs. total oficial de cada alcaldía, diferencia ≤ 1 % | OK (0.0 %) |
| Unión DENUE | AGEB con al menos un negocio del DENUE (para tener punto en el mapa) | 99.5 % |
| Zonas analizadas | AGEB con 500 habitantes o más | 2,308 (2,301 con coordenadas), 9.1 millones de habitantes |

Las reglas completas (R1-R8) están en el [diccionario de datos](../data_dictionary.md).

## 5. Limitaciones

* El Censo es de **2020**: la población de zonas que crecieron mucho desde entonces está subestimada.
* El Censo **no trae ingreso**: el nivel socioeconómico es un sustituto (escolaridad y equipamiento de la vivienda).
* El DENUE no ve farmacias informales ni consultorios dentro de farmacias que no estén registrados aparte.
* El punto de cada zona es el promedio de sus negocios, no el centro geométrico de la AGEB.
