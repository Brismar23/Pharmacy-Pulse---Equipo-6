"""Lambda 4 · mapa: S3 gold -> mapa estático y resumen (también en gold).

Se dispara cuando aparece un manifiesto nuevo en gold (_manifiestos/version=...json).
Genera un solo archivo HTML (Leaflet + OpenStreetMap) que se abre con doble clic,
sin servidor ni aplicación web (SOW, sección 4), y un resumen en Markdown:

    mapa/version=F/index.html     y  mapa/actual/index.html
    resumen/version=F/resumen.md  y  resumen/actual/resumen.md
"""
import html
import json
import os
import pathlib

from comun import almacen
from comun.tablas import LOG, a_numero, texto_a_filas

PLANTILLA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pharmacy Pulse · Zonas con potencial para la primera sucursal</title>
<style>__LEAFLET_CSS__</style>
<script>__LEAFLET_JS__</script>
<style>
  :root { --tinta:#1f2a37; --suave:#6b7280; --linea:#e5e7eb; --marca:#0f766e; }
  * { box-sizing:border-box; }
  body { margin:0; font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; color:var(--tinta); display:flex; height:100vh; }
  #panel { width:380px; overflow:auto; padding:18px 18px 28px; border-right:1px solid var(--linea); background:#fff; }
  #mapa { flex:1; }
  h1 { font-size:18px; margin:0 0 4px; } .sub { color:var(--suave); margin:0 0 14px; }
  .aviso { background:#fff7ed; border:1px solid #fed7aa; border-radius:8px; padding:8px 10px; font-size:12.5px; margin-bottom:14px; }
  ol { padding-left:0; list-style:none; margin:0; }
  li.zona { border:1px solid var(--linea); border-radius:8px; padding:8px 10px; margin-bottom:8px; cursor:pointer; }
  li.zona:hover { border-color:var(--marca); }
  .num { display:inline-block; min-width:22px; height:22px; border-radius:11px; background:var(--marca); color:#fff; text-align:center; font-weight:600; font-size:12px; line-height:22px; margin-right:6px; }
  .ipa { float:right; font-weight:700; } .meta { color:var(--suave); font-size:12.5px; }
  .leyenda { display:flex; gap:4px; align-items:center; margin:12px 0 4px; font-size:12px; color:var(--suave); }
  .leyenda span.c { width:28px; height:10px; border-radius:2px; display:inline-block; }
  label { display:block; margin:4px 0; } select { width:100%; padding:6px; margin:6px 0 12px; }
  .etiqueta-top { background:var(--marca); color:#fff; border-radius:11px; text-align:center; font:600 11px/20px system-ui; border:2px solid #fff; }
  @media (max-width:760px) { body { flex-direction:column; } #panel { width:auto; height:45vh; border-right:0; border-bottom:1px solid var(--linea); } }
</style></head><body>
<div id="panel">
  <h1>¿Dónde abrir la primera sucursal?</h1>
  <p class="sub">Índice de Potencial de Apertura (IPA, 0 a 100) por zona · datos INEGI · versión __VERSION__</p>
  <div class="aviso"><b>Cómo leerlo:</b> cada círculo es una zona (AGEB). Más oscuro = más potencial; más grande = más gente.
  Es una <b>priorización relativa</b> para decidir qué zonas visitar, no una garantía de ventas.</div>
  <label for="filtro">Ver alcaldía</label>
  <select id="filtro"><option value="">Las seis alcaldías</option></select>
  <label><input type="checkbox" id="verFarmacias" checked> Farmacias existentes (competencia)</label>
  <label><input type="checkbox" id="verSalud"> Consultorios y hospitales</label>
  <div class="leyenda">IPA <span class="c" style="background:#ecfdf5"></span><span class="c" style="background:#a7f3d0"></span><span class="c" style="background:#34d399"></span><span class="c" style="background:#059669"></span><span class="c" style="background:#064e3b"></span> 0 → 100</div>
  <h2 style="font-size:15px;margin:16px 0 8px">Las 10 zonas con más potencial</h2>
  <ol id="lista"></ol>
  <p class="meta">Fuentes: INEGI, Censo de Población y Vivienda 2020 (AGEB urbana) y DENUE (descarga __VERSION__). Calidad de la carga: __CALIDAD__.</p>
</div>
<div id="mapa"></div>
<script>
const ZONAS = __ZONAS__;
const FARMACIAS = __FARMACIAS__;
const SALUD = __SALUD__;
const color = v => v >= 80 ? "#064e3b" : v >= 60 ? "#059669" : v >= 40 ? "#34d399" : v >= 20 ? "#a7f3d0" : "#ecfdf5";
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const mapa = L.map("mapa", { preferCanvas: true }).setView([19.36, -99.13], 11);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 18, attribution: "© OpenStreetMap" }).addTo(mapa);
const capaZonas = L.layerGroup().addTo(mapa), capaTop = L.layerGroup().addTo(mapa);
const capaFarm = L.layerGroup(FARMACIAS.map(p => L.circleMarker([p[0], p[1]], { radius: 2.5, color: "#b91c1c", weight: 0, fillOpacity: .75 }).bindTooltip(esc(p[2])))).addTo(mapa);
const capaSalud = L.layerGroup(SALUD.map(p => L.circleMarker([p[0], p[1]], { radius: 2, color: "#1d4ed8", weight: 0, fillOpacity: .6 }).bindTooltip(esc(p[2]))));
const fila = (k, v) => `<tr><td style="color:#6b7280;padding-right:8px">${k}</td><td>${v}</td></tr>`;
const ficha = z => `<b>${z.p ? "#" + z.p + " · " : ""}${esc(z.c || "Zona " + z.g)}</b><br><span style="color:#6b7280">${esc(z.a)} · AGEB ${z.g}</span>
  <div style="font-size:22px;font-weight:700;margin:4px 0">IPA ${z.i}</div><table>
  ${fila("Habitantes", z.pob.toLocaleString("es-MX"))}${fila("Farmacias a menos de " + z.r + " m", z.far)}
  ${fila("Consultorios y hospitales a " + z.r + " m", z.sal)}${fila("60 años o más", z.p60 + " %")}${fila("Escolaridad promedio", z.esc + " años")}
  ${fila("Confianza del dato", z.conf)}</table><p style="margin:6px 0 0">${esc(z.why)}</p>`;
const marcadores = {};
function dibujar(alc) {
  capaZonas.clearLayers(); capaTop.clearLayers();
  const visibles = ZONAS.filter(z => !alc || z.a === alc);
  visibles.forEach(z => {
    const m = L.circleMarker([z.lat, z.lon], { radius: 3 + Math.sqrt(z.pob) / 14, color: z.p && z.p <= 10 ? "#0f766e" : "#475569",
      weight: z.p && z.p <= 10 ? 2.5 : .5, fillColor: color(z.i), fillOpacity: .85 }).bindPopup(ficha(z), { maxWidth: 320 });
    capaZonas.addLayer(m); marcadores[z.g] = m;
  });
  const top = visibles.filter(z => z.p).sort((a, b) => a.p - b.p).slice(0, 10);
  top.forEach((z, k) => capaTop.addLayer(L.marker([z.lat, z.lon], { icon: L.divIcon({ className: "", html: `<div class="etiqueta-top">${k + 1}</div>`, iconSize: [22, 22] }) })
    .on("click", () => marcadores[z.g].openPopup())));
  document.getElementById("lista").innerHTML = top.map((z, k) => `<li class="zona" data-g="${z.g}"><span class="num">${k + 1}</span><b>${esc(z.c || "AGEB " + z.g)}</b><span class="ipa">${z.i}</span>
    <div class="meta">${esc(z.a)} · ${z.pob.toLocaleString("es-MX")} hab. · ${z.far} farmacias cerca · confianza ${z.conf}</div></li>`).join("");
  document.querySelectorAll("li.zona").forEach(li => li.onclick = () => { const m = marcadores[li.dataset.g]; mapa.setView(m.getLatLng(), 15); m.openPopup(); });
  if (visibles.length) mapa.fitBounds(L.latLngBounds(visibles.map(z => [z.lat, z.lon])), { padding: [20, 20] });
}
const sel = document.getElementById("filtro");
[...new Set(ZONAS.map(z => z.a))].sort().forEach(a => sel.add(new Option(a, a)));
sel.onchange = () => dibujar(sel.value);
document.getElementById("verFarmacias").onchange = e => e.target.checked ? capaFarm.addTo(mapa) : mapa.removeLayer(capaFarm);
document.getElementById("verSalud").onchange = e => e.target.checked ? capaSalud.addTo(mapa) : mapa.removeLayer(capaSalud);
dibujar("");
</script></body></html>
"""


# Leaflet 1.9.4 (licencia BSD-2) va dentro del zip: el mapa abre sin internet y sin CDN.
_VENDOR = pathlib.Path(__file__).resolve().parent / "vendor"


def _leaflet():
    return (_VENDOR / "leaflet.css").read_text(encoding="utf-8"), (_VENDOR / "leaflet.js").read_text(encoding="utf-8")


def _json_seguro(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def construir_html(zonas, puntos, version, calidad):
    datos = []
    for z in zonas:
        if z.get("elegible") != "True" or not z.get("lat") or not z.get("ipa"):
            continue
        datos.append({
            "g": z["cvegeo"], "p": int(z["posicion"]) if z.get("posicion") else None, "i": float(z["ipa"]),
            "a": z["alcaldia"], "c": z["colonia_referencia"], "lat": float(z["lat"]), "lon": float(z["lon"]),
            "pob": int(float(z["poblacion"])), "far": int(z["farmacias_radio"] or 0), "r": int(z["radio_m"]),
            "sal": int(z["salud_radio"] or 0), "p60": round(a_numero(z["pct_60ymas"]) or 0), "esc": z["escolaridad"] or "s/d",
            "conf": z["confianza"], "why": z["por_que"],
        })
    farm = [[float(p["lat"]), float(p["lon"]), p["nombre"]] for p in puntos if p["tipo"] == "farmacia"]
    salud = [[float(p["lat"]), float(p["lon"]), p["nombre"]] for p in puntos if p["tipo"] == "salud"]
    css, js = _leaflet()
    return (PLANTILLA.replace("__LEAFLET_CSS__", css).replace("__LEAFLET_JS__", js).replace("__ZONAS__", _json_seguro(datos)).replace("__FARMACIAS__", _json_seguro(farm))
            .replace("__SALUD__", _json_seguro(salud)).replace("__VERSION__", html.escape(version))
            .replace("__CALIDAD__", html.escape(calidad))), len(datos)


def construir_resumen(zonas, version, reporte):
    top = sorted((z for z in zonas if z.get("posicion")), key=lambda z: int(z["posicion"]))[:10]
    lineas = [f"# Resumen automático del ranking (versión {version})", "",
              f"Calidad de la carga: **{reporte.get('estado', 's/d')}**. "
              f"Zonas analizadas: {reporte.get('agebs_estudio')}; en el ranking: {reporte.get('agebs_en_ranking')}.", "",
              "| # | Zona | Alcaldía | IPA | Habitantes | Farmacias a 500 m | Confianza |", "|---:|---|---|---:|---:|---:|---|"]
    for z in top:
        lineas.append(f"| {z['posicion']} | {z['colonia_referencia'] or z['cvegeo']} | {z['alcaldia']} | {z['ipa']} | "
                      f"{int(float(z['poblacion'])):,} | {z['farmacias_radio']} | {z['confianza']} |")
    lineas += ["", "## Por qué destacan", ""]
    lineas += [f"{z['posicion']}. **{z['colonia_referencia'] or z['cvegeo']}** ({z['alcaldia']}): {z['por_que']}" for z in top]
    lineas += ["", "## Reglas de calidad", "", "| Regla | Resultado | Valor |", "|---|---|---|"]
    lineas += [f"| {r['id']} {r['regla']} | {r['resultado']} | {r['valor'] if not isinstance(r['valor'], dict) else json.dumps(r['valor'])} |"
               for r in reporte.get("reglas", [])]
    lineas += ["", "> El IPA es una priorización relativa entre zonas con datos públicos del INEGI. No es un pronóstico de",
               "> ventas ni de rentabilidad; las zonas del top deben validarse en campo (rentas, flujo peatonal, locales).", ""]
    return "\n".join(lineas)


def lambda_handler(event, context=None):
    event = event or {}
    silver, gold = os.environ["SILVER_BUCKET"], os.environ["GOLD_BUCKET"]
    _, key = almacen.key_del_evento(event)
    if not key and event.get("version"):
        key = f"_manifiestos/version={event['version']}.json"
    if not key or not key.startswith("_manifiestos/"):
        return {"estado": "IGNORADO", "key": key}

    man = almacen.leer_json(gold, key)
    version = man["version_raw"]
    zonas = texto_a_filas(almacen.leer_bytes(gold, man["zonas"]).decode("utf-8"))
    puntos = texto_a_filas(almacen.leer_bytes(silver, man["puntos_silver"]).decode("utf-8"))
    reporte = almacen.leer_json(gold, f"calidad/version={version}/reporte.json")

    pagina, n = construir_html(zonas, puntos, version, man.get("estado_calidad", ""))
    resumen = construir_resumen(zonas, version, reporte)
    for carpeta in (f"version={version}", "actual"):
        almacen.escribir_texto(gold, f"mapa/{carpeta}/index.html", pagina, "text/html; charset=utf-8")
        almacen.escribir_texto(gold, f"resumen/{carpeta}/resumen.md", resumen, "text/markdown; charset=utf-8")
    LOG.info(json.dumps({"estado": "OK", "version": version, "zonas_en_mapa": n, "puntos": len(puntos)}))
    return {"estado": "OK", "version": version, "zonas_en_mapa": n, "mapa": f"s3://{gold}/mapa/actual/index.html"}
