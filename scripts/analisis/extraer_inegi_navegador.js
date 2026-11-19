/*
 * Extracción de datos del INEGI desde el navegador (Pharmacy Pulse).
 *
 * Por qué en el navegador: el sitio del INEGI rechaza descargas desde algunas redes y
 * servidores (proxies, nubes), pero siempre responde a un navegador normal. Este script
 * corre en la consola del navegador estando en una página de inegi.org.mx, descarga los
 * dos zips oficiales, los descomprime en memoria (DecompressionStream, sin librerías),
 * filtra la CDMX y baja tres CSV listos para el análisis.
 *
 * Uso:
 *   1. Abre https://www.inegi.org.mx/app/descarga/?ti=6 en Chrome, Edge o Brave.
 *   2. Abre la consola (F12 -> Console), pega este archivo completo y presiona Enter.
 *   3. Se descargan: cdmx_zonas_inegi.csv, cdmx_totales_alcaldias.csv, cdmx_puntos_denue.csv
 *   4. Cópialos a data/extraido/ y corre: python3 scripts/analisis/analisis_cdmx.py
 *
 * Fuentes (públicas):
 *   - Censo de Población y Vivienda 2020, principales resultados por AGEB y manzana urbana, CDMX (13 MB)
 *   - DENUE, edición vigente, CDMX (45 MB; la extracción original usó la 05/2026)
 * Tarda unos 5 a 10 segundos en una computadora normal.
 */
(async () => {
  const URL_CENSO = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/ageb_manzana/ageb_mza_urbana_09_cpv2020_csv.zip";
  const URL_DENUE = "https://www.inegi.org.mx/contenidos/masiva/denue/denue_09_csv.zip";
  const ALC = { "002": "Azcapotzalco", "003": "Coyoacán", "004": "Cuajimalpa de Morelos", "005": "Gustavo A. Madero", "006": "Iztacalco",
    "007": "Iztapalapa", "008": "La Magdalena Contreras", "009": "Milpa Alta", "010": "Álvaro Obregón", "011": "Tláhuac", "012": "Tlalpan",
    "013": "Xochimilco", "014": "Benito Juárez", "015": "Cuauhtémoc", "016": "Miguel Hidalgo", "017": "Venustiano Carranza" };
  const SOLO_CONTAR = window.EXTRAER_SOLO_CONTAR === true; // para probar sin descargar archivos

  // ---------- zip: lee el directorio central y descomprime una entrada con DecompressionStream
  async function abrirZip(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${url} respondió ${r.status}`);
    const buf = new Uint8Array(await r.arrayBuffer()), dv = new DataView(buf.buffer);
    let e = buf.length - 22; while (dv.getUint32(e, true) !== 0x06054b50) e--;
    const n = dv.getUint16(e + 10, true); let p = dv.getUint32(e + 16, true); const ents = [];
    for (let i = 0; i < n; i++) {
      const fl = dv.getUint16(p + 28, true), xl = dv.getUint16(p + 30, true), cl = dv.getUint16(p + 32, true);
      ents.push({ name: new TextDecoder().decode(buf.slice(p + 46, p + 46 + fl)), method: dv.getUint16(p + 10, true),
        csize: dv.getUint32(p + 20, true), off: dv.getUint32(p + 42, true) });
      p += 46 + fl + xl + cl;
    }
    return { buf, dv, ents };
  }
  async function leerLineas(z, filtro, codificacion, alLeer) {
    const ent = z.ents.find(filtro);
    const ini = ent.off + 30 + z.dv.getUint16(ent.off + 26, true) + z.dv.getUint16(ent.off + 28, true);
    let s = new Blob([z.buf.subarray(ini, ini + ent.csize)]).stream();
    if (ent.method === 8) s = s.pipeThrough(new DecompressionStream("deflate-raw"));
    const rd = s.pipeThrough(new TextDecoderStream(codificacion)).getReader(); let resto = "", n = 0;
    for (;;) { const { value, done } = await rd.read(); if (done) break;
      const partes = (resto + value).split("\n"); resto = partes.pop(); for (const l of partes) alLeer(l.replace(/\r$/, ""), n++); }
    if (resto) alLeer(resto, n++);
  }
  function separar(l) { // CSV con comillas
    if (l.indexOf('"') < 0) return l.split(",");
    const out = []; let cur = "", q = false;
    for (let i = 0; i < l.length; i++) { const c = l[i];
      if (q) { if (c === '"') { if (l[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
      else if (c === '"') q = true; else if (c === ",") { out.push(cur); cur = ""; } else cur += c; }
    out.push(cur); return out;
  }
  const q = v => v == null ? "" : (typeof v === "string" && /[",]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : (typeof v === "number" && !Number.isInteger(v) ? v.toFixed(5) : v));
  const titulo = s => s.toLowerCase().replace(/(^|\s)\S/g, m => m.toUpperCase());

  // ---------- Censo 2020: una fila por AGEB urbana (MZA = 000) y totales oficiales por alcaldía
  const zc = await abrirZip(URL_CENSO);
  const agebs = [], totLoc = {}, totMun = {}; let hc = null;
  await leerLineas(zc, e => /conjunto_de_datos.*\.csv$/.test(e.name), "utf-8", (l, n) => {
    const f = separar(l);
    if (n === 0) { hc = {}; f.forEach((c, i) => hc[c.replace(/^﻿/, "").trim()] = i); return; }
    const g = c => f[hc[c]];
    if (g("ENTIDAD") !== "09" || !ALC[g("MUN")] || g("MZA") !== "000") return;
    const mun = g("MUN"), loc = g("LOC"), ageb = g("AGEB");
    if (loc === "0000" && ageb === "0000") { totMun[mun] = +g("POBTOT"); return; }
    if (ageb === "0000") { totLoc[mun] = (totLoc[mun] || 0) + (+g("POBTOT")); return; }
    const num = c => { const v = g(c); return (v === "*" || v === "N/D" || v === "" || v === undefined) ? null : +v; };
    agebs.push({ cvegeo: "09" + mun + loc + ageb, k: "09" + mun + ageb, mun, nd: g("POBTOT") === "N/D",
      v: ["POBTOT", "P_60YMAS", "POB65_MAS", "P_0A2", "GRAPROES", "PDER_SS", "PSINDER", "PAFIL_IPRIV", "PDER_IMSS", "TVIVPARHAB",
          "VPH_AUTOM", "VPH_INTER", "VPH_PC"].map(num),
      edades: ["P_3A5", "P_6A11", "P_12A14", "P_15A17", "P_18A24", "P_18YMAS"].map(num) });
  });

  // ---------- DENUE: farmacias y unidades de salud de toda la CDMX + resumen por AGEB
  const zd = await abrirZip(URL_DENUE);
  const porAgeb = {}, puntos = [], vistos = new Set(); let hd = null;
  await leerLineas(zd, e => e.name.startsWith("conjunto_de_datos/") && e.name.endsWith(".csv"), "latin1", (l, n) => {
    const f = separar(l);
    if (n === 0) { hd = {}; f.forEach((c, i) => hd[c.trim()] = i); return; }
    const g = c => (f[hd[c]] || "").trim();
    if (g("cve_ent") !== "09") return;
    const id = g("id"); if (vistos.has(id)) return; vistos.add(id);
    const lat = +g("latitud"), lon = +g("longitud");
    if (!(lat >= 19.0 && lat <= 19.65 && lon >= -99.40 && lon <= -98.90)) return; // fuera de la CDMX
    const act = g("codigo_act");
    const tipo = (act === "464111" || act === "464112") ? "farmacia" : (act.startsWith("621") || act.startsWith("622")) ? "salud" : null;
    if (tipo) puntos.push([tipo, lat, lon, tipo === "farmacia" ? g("nom_estab").slice(0, 40) : ""]);
    const mun = g("cve_mun"), ag = g("ageb").toUpperCase().replace("-", "");
    if (!ALC[mun] || !ag) return;
    const k = "09" + mun + ag.padStart(4, "0");
    const a = porAgeb[k] || (porAgeb[k] = { n: 0, sl: 0, so: 0, farm: 0, col: {} });
    a.n++; a.sl += lat; a.so += lon; if (tipo === "farmacia") a.farm++;
    const col = g("nomb_asent"); if (col) a.col[col] = (a.col[col] || 0) + 1;
  });

  // ---------- armar los CSV
  const colsZ = ["cvegeo", "cve_mun", "alcaldia", "colonia", "nd", "pob", "p60", "p65", "p02", "esc", "der", "sinder", "priv", "imss", "viv",
    "auto", "inter", "pc", "establecimientos", "farm_ageb", "lat", "lon", "p35", "p611", "p1214", "p1517", "p1824", "p18mas"];
  const filas = agebs.map(z => { const d = porAgeb[z.k];
    const col = d ? titulo(Object.entries(d.col).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))[0]?.[0] || "") : "";
    const [pob, p60, p65, p02, esc, der, sinder, priv, imss, viv, auto, inter, pc] = z.v;
    return [z.cvegeo, z.mun, ALC[z.mun], col, z.nd ? 1 : 0, pob, p60, p65, p02, esc, der, sinder, priv, imss, viv, auto, inter, pc,
      d ? d.n : null, d ? d.farm : null, d ? d.sl / d.n : null, d ? d.so / d.n : null, ...z.edades].map(q).join(","); });
  const archivos = {
    "cdmx_zonas_inegi.csv": colsZ.join(",") + "\n" + filas.join("\n") + "\n",
    "cdmx_totales_alcaldias.csv": "cve_mun,alcaldia,pob_mun_oficial,pob_localidades_urbanas\n" +
      Object.keys(ALC).map(m => [m, ALC[m], totMun[m], totLoc[m]].join(",")).join("\n") + "\n",
    "cdmx_puntos_denue.csv": "tipo,lat,lon,nombre\n" + puntos.map(p => [p[0], p[1], p[2], q(p[3])].join(",")).join("\n") + "\n",
  };
  const resumen = { zonas: agebs.length, zonas_con_denue: filas.length - agebs.filter(z => !porAgeb[z.k]).length,
    farmacias: puntos.filter(p => p[0] === "farmacia").length, unidades_salud: puntos.filter(p => p[0] === "salud").length };
  window.EXTRACCION_PHARMACY_PULSE = { archivos, resumen };
  if (!SOLO_CONTAR) for (const [nombre, texto] of Object.entries(archivos)) {
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([texto], { type: "text/csv" }));
    a.download = nombre; document.body.appendChild(a); a.click(); a.remove(); await new Promise(r => setTimeout(r, 1500));
  }
  console.log("Extracción terminada", resumen);
  return resumen;
})();
