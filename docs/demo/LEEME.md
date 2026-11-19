# Demo: ¿dónde abrir la nueva sucursal?

`index.html` es una página única: datos de las 2,301 zonas y el mapa (Leaflet) van dentro del archivo. No necesita instalar nada.

## Abrirla

* **Doble clic en `index.html`**, o
* como servidor local (para mostrarla en clase en `http://localhost:8000`):

```bash
cd docs/demo
python -m http.server 8000      # en Windows también: py -m http.server 8000
```

El fondo del mapa (OpenStreetMap) necesita internet; los puntos y filtros funcionan sin él.

## Filtros

* **¿Qué buscas?** Combinado (IPA), por edad elegida, mucha población, nivel alto, nivel bajo (genéricos) o hueco de farmacias.
* **Alcaldía**, **nivel socioeconómico** (bajo, medio, alto), **edad de tus clientes** ("De __ a __ años", en % de la zona o en personas), **población mínima**, **máximo de farmacias a 500 m** y **tipo de zona** (machine learning).

## Regenerarla

`make analisis` (o `python3 scripts/analisis/analisis_cdmx.py`). El código está en `scripts/analisis/demo.py` y `scripts/analisis/demo_plantilla.html`.
