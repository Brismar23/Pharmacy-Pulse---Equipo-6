# Resultados del análisis de la CDMX

Datos reales: Censo 2020 por AGEB y DENUE 05/2026 ([fuentes y extracción](../datos/fuentes_y_extraccion.md)). **2,301 zonas** con 500 habitantes o más y coordenadas, **9.1 millones de habitantes**, **7,450 farmacias** y 19,794 unidades de salud. Método en el [ADR 0004](../adr/0004-machine-learning-exploratorio.md).

Para regenerar todo: `pip install -r requirements-analisis.txt` y `make analisis` (≈ 30 s).

## Hallazgos

1. **La competencia no es pareja.** Milpa Alta (13.1 farmacias por cada 10 mil habitantes), Tláhuac (11.3) e Iztapalapa (9.9) están saturadas; Álvaro Obregón (5.5), Magdalena Contreras y Miguel Hidalgo (6.0) tienen más espacio.
2. **Mejores zonas por IPA:** Granada (Miguel Hidalgo, 82.4), San Miguel Chapultepec (79.5), Tetelpan (Álvaro Obregón, 78.9), Del Valle Norte (78.7), Ciudad de los Deportes (78.5) y Prado Churubusco (78.4).
3. **5 tipos de zona** (k-means): clase media popular y poblada (687), popular densa y saturada (585), clase media-alta con más adultos mayores (529), periferia popular joven (360) y residencial alto con poca competencia (140).
4. **Qué explica dónde hay farmacias** (random forest, R² 0.385): la actividad comercial de la zona y el % de viviendas con auto pesan más que el número de habitantes.
5. **310 zonas con hueco**: tienen al menos 3 farmacias menos de lo que el modelo espera y menos de la mitad que sus 10 zonas gemelas. Se revisaron 20 en Google Maps y **8 no tienen ninguna farmacia a 500 m**:

| Zona | Alcaldía | Habitantes | Farmacias esperadas a 500 m | Tipo |
|---|---|---:|---:|---|
| Lomas de San Lorenzo | Iztapalapa | 11,206 | 20.8 | Periferia popular joven |
| San Gregorio Atlapulco | Xochimilco | 11,635 | 13.2 | Periferia popular joven |
| San Rafael Ticomán | Gustavo A. Madero | 4,725 | 11.8 | Periferia popular joven |
| Tlapechico | Álvaro Obregón | 3,788 | 11.0 | Periferia popular joven |
| Coltongo | Azcapotzalco | 5,207 | 10.5 | Periferia popular joven |
| Tetelpan | Álvaro Obregón | 8,392 | 9.7 | Clase media popular y poblada |
| El Jagüey | Azcapotzalco | 6,325 | 8.0 | Clase media popular y poblada |
| Cuajimalpa | Cuajimalpa | 6,200 | 7.2 | Clase media popular y poblada |

**Tetelpan** (Álvaro Obregón) sale en las dos listas: una de sus AGEB es la 3.ª del IPA y también tiene hueco; otra, la 40.ª, tiene el hueco confirmado en Google Maps.

> El IPA y el hueco son priorizaciones, no pronósticos de ventas. Antes de rentar local: visita de campo, rentas, flujo peatonal y local disponible.

## Gráficas

| # | Archivo | Qué muestra |
|---|---|---|
| 1 | [01_tipos_de_zona_machine_learning.png](01_tipos_de_zona_machine_learning.png) | Perfil de los 5 tipos de zona |
| 2 | [02_mapa_tipos_de_zona.png](02_mapa_tipos_de_zona.png) | Dónde está cada tipo |
| 3 | [03_demanda_vs_competencia.png](03_demanda_vs_competencia.png) | Demanda contra farmacias a 500 m |
| 4 | [04_top15_ipa.png](04_top15_ipa.png) | Las 15 zonas con mayor IPA |
| 5 | [05_vista_machine_learning_pca.png](05_vista_machine_learning_pca.png) | Las zonas en 2 dimensiones (PCA) |
| 6 | [06_zonas_con_hueco_de_farmacias.png](06_zonas_con_hueco_de_farmacias.png) | Farmacias reales contra esperadas |
| 7 | [07_que_explica_donde_hay_farmacias.png](07_que_explica_donde_hay_farmacias.png) | Importancia de cada variable |
| 8 | [08_mapa_donde_faltan_farmacias.png](08_mapa_donde_faltan_farmacias.png) | Mapa de huecos y saturación |
| 9 | [09_alcaldias_saturacion_y_huecos.png](09_alcaldias_saturacion_y_huecos.png) | Las 16 alcaldías comparadas |

Tablas: [`data/resultados/cdmx_zonas_farmacias_analisis_completo.csv`](../../data/resultados/cdmx_zonas_farmacias_analisis_completo.csv) (una fila por zona con IPA, tipo, hueco, gemelas y verificación) y [`data/resultados/resumen_por_alcaldia.csv`](../../data/resultados/resumen_por_alcaldia.csv).

Demo interactiva: [`docs/demo/`](../demo/).
