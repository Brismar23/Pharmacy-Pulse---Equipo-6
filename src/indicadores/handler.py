"""Lambda 3 · indicadores: S3 silver -> S3 gold.

Se dispara cuando aparece un manifiesto nuevo en silver (_manifiestos/version=...json).
Une Censo y DENUE por clave de AGEB, calcula los indicadores de demanda y competencia,
corre las reglas de calidad (R1, R3, R4, R5, R7, R8) y calcula el Índice de Potencial
de Apertura (IPA, 0-100) con los pesos de la variable de entorno PESOS_IPA.

Escribe en gold:
    zonas_ipa/version=F/zonas_ipa.csv   todas las AGEB del estudio con indicadores e IPA
    ranking/version=F/ranking.csv       top N con explicación y etiqueta de confianza
    ranking/actual/ranking.csv          copia del último ranking aprobado
    calidad/version=F/reporte.json      resultado de todas las reglas
    _manifiestos/version=F.json         se escribe al final y dispara la Lambda del mapa

Si falla una regla bloqueante, no publica nada en zonas_ipa/ranking, deja el reporte
con estado BLOQUEADO y manda una alerta por SNS.
"""
import bisect
import datetime as dt
import email.utils
import json
import math
import os

from comun import almacen
from comun.tablas import ALCALDIAS, LOG, a_numero, alertar, csv_a_texto, redondear, texto_a_filas

PESOS_BASE = {"poblacion": 0.30, "edades": 0.15, "ingreso": 0.15, "salud": 0.10, "competencia": 0.30}
COMPONENTES = list(PESOS_BASE)


def _pesos():
    pesos = json.loads(os.environ.get("PESOS_IPA") or json.dumps(PESOS_BASE))
    desconocidos = set(pesos) - set(PESOS_BASE)
    if desconocidos:
        raise ValueError(f"Pesos desconocidos en PESOS_IPA: {sorted(desconocidos)}")
    pesos = {k: float(pesos.get(k, 0)) for k in COMPONENTES}
    if abs(sum(pesos.values()) - 1) > 0.001:
        raise ValueError(f"Los pesos deben sumar 1, suman {sum(pesos.values()):.3f}")
    return pesos


def _percentil(valores, p):
    v = sorted(valores)
    if not v:
        return None
    pos = (len(v) - 1) * p
    i = int(pos)
    return v[i] if i + 1 >= len(v) else v[i] + (v[i + 1] - v[i]) * (pos - i)


def _normalizar(filas, campo, destino, inverso=False):
    """Min-max a 0-100, recortando antes a los percentiles 5 y 95 (ver ADR 0001)."""
    valores = [f[campo] for f in filas if f[campo] is not None]
    lo, hi = _percentil(valores, 0.05), _percentil(valores, 0.95)
    for f in filas:
        x = f[campo]
        if x is None or lo is None:
            f[destino] = None
            continue
        x = min(max(x, lo), hi)
        n = 50.0 if hi == lo else 100.0 * (x - lo) / (hi - lo)
        f[destino] = round(100.0 - n if inverso else n, 2)


def _contar_en_radio(zonas, puntos, radio_m):
    """Cuenta puntos a menos de radio_m metros del punto representativo de cada zona.

    Los puntos se ordenan por latitud y se recorre solo la franja que puede caer dentro
    del radio, así que el cálculo tarda segundos aun con miles de zonas y puntos.
    """
    puntos = sorted(puntos)
    lats = [p[0] for p in puntos]
    dlat = radio_m / 111_320
    conteos = []
    for lat, lon in zonas:
        if lat is None:
            conteos.append(None)
            continue
        dlon = dlat / max(math.cos(math.radians(lat)), 0.1)
        n = 0
        for plat, plon in puntos[bisect.bisect_left(lats, lat - dlat):bisect.bisect_right(lats, lat + dlat)]:
            if abs(plon - lon) > dlon:
                continue
            a = (math.sin(math.radians(plat - lat) / 2) ** 2 +
                 math.cos(math.radians(lat)) * math.cos(math.radians(plat)) * math.sin(math.radians(plon - lon) / 2) ** 2)
            if 2 * 6_371_000 * math.asin(math.sqrt(a)) <= radio_m:
                n += 1
        conteos.append(n)
    return conteos


def _frase(componente, f):
    if componente == "poblacion":
        return f"{f['poblacion']:,.0f} habitantes"
    if componente == "edades":
        return f"{f['pct_60ymas']:.0f} % de la población tiene 60 años o más"
    if componente == "ingreso":
        auto = f" y {f['pct_viv_auto']:.0f} % de viviendas con auto" if f.get("pct_viv_auto") is not None else ""
        return f"nivel socioeconómico alto: {f['escolaridad'] or 0:.1f} años de escolaridad{auto}"
    if componente == "salud":
        return f"{f['salud_radio']} consultorios u hospitales a menos de {f['radio_m']} m (generan recetas)"
    if componente == "competencia":
        if f["farmacias_radio"] == 0:
            return f"ninguna farmacia a menos de {f['radio_m']} m"
        if f["farmacias_radio"] == 1:
            return f"solo 1 farmacia a menos de {f['radio_m']} m"
        return f"{f['farmacias_radio']} farmacias a menos de {f['radio_m']} m"
    return componente


def _explicar(f, pesos):
    aportes = sorted(((pesos[c] * f[f"n_{c}"], c) for c in COMPONENTES if pesos[c] > 0 and f[f"n_{c}"] is not None),
                     key=lambda t: (-t[0], t[1]))
    if not aportes:
        return ""
    fuertes = [c for _, c in aportes[:2]]
    debil = min(((f[f"n_{c}"], c) for c in COMPONENTES if pesos[c] > 0 and f[f"n_{c}"] is not None))[1]
    texto = "Destaca por: " + "; ".join(_frase(c, f) for c in fuertes) + "."
    if debil not in fuertes:
        texto += " Punto débil: " + _frase(debil, f) + "."
    return texto


def _antiguedad_meses(fecha_http, referencia):
    if not fecha_http:
        return None
    try:
        d = email.utils.parsedate_to_datetime(fecha_http).date()
    except (TypeError, ValueError):
        return None
    return (referencia.year - d.year) * 12 + referencia.month - d.month


def lambda_handler(event, context=None):
    event = event or {}
    silver, gold = os.environ["SILVER_BUCKET"], os.environ["GOLD_BUCKET"]
    _, key = almacen.key_del_evento(event)
    if not key and event.get("version"):
        key = f"_manifiestos/version={event['version']}.json"
    if not key or not key.startswith("_manifiestos/"):
        return {"estado": "IGNORADO", "key": key}

    man = almacen.leer_json(silver, key)
    version = man["version_raw"]
    pesos = _pesos()
    min_pob = float(os.environ.get("MIN_POBLACION", "500"))
    top_n = int(os.environ.get("TOP_N", "20"))
    leer = lambda tabla: texto_a_filas(almacen.leer_bytes(silver, f"{tabla}/version={version}/{tabla}.csv").decode("utf-8"))

    radio_m = int(os.environ.get("RADIO_M", "500"))
    censo, totales = leer("censo_ageb"), leer("censo_totales")
    denue = {d["clave_ageb"]: d for d in leer("denue_ageb")}
    puntos = leer("denue_puntos")

    # ---------------------------------------------------------------- unión e indicadores
    zonas = []
    for c in censo:
        d = denue.get(c["clave_ageb"], {})
        pob = a_numero(c["pobtot"])
        f = {
            "cvegeo": c["cvegeo"], "clave_ageb": c["clave_ageb"], "cve_mun": c["cve_mun"], "alcaldia": c["alcaldia"],
            "colonia_referencia": d.get("colonia_principal", ""), "estado_dato": c["estado_dato"],
            "poblacion": pob, "farmacias": int(d.get("farmacias") or 0), "unidades_salud": int(d.get("unidades_salud") or 0),
            "establecimientos": int(d.get("establecimientos") or 0),
            "lat": d.get("lat") or "", "lon": d.get("lon") or "",
            "escolaridad": a_numero(c["graproes"]),
        }
        p60, pder = a_numero(c["p_60ymas"]), a_numero(c["pder_ss"])
        viv = a_numero(c.get("tvivparhab"))
        for col, dest in (("vph_autom", "pct_viv_auto"), ("vph_inter", "pct_viv_internet"), ("vph_pc", "pct_viv_pc")):
            v = a_numero(c.get(col))
            f[dest] = redondear(100 * v / viv, 2) if viv and v is not None else None
        ok_pob = pob is not None and pob > 0
        f["pct_60ymas"] = redondear(100 * p60 / pob, 2) if ok_pob and p60 is not None else None
        f["pct_afiliada_salud"] = redondear(100 * pder / pob, 2) if ok_pob and pder is not None else None
        f["farmacias_10k"] = redondear(10000 * f["farmacias"] / pob, 3) if ok_pob else None
        f["salud_10k"] = redondear(10000 * f["unidades_salud"] / pob, 3) if ok_pob else None
        f["elegible"] = bool(ok_pob and pob >= min_pob)
        f["radio_m"] = radio_m
        zonas.append(f)

    # Competencia y contexto de salud alrededor de la zona, no solo dentro de la AGEB:
    # una farmacia en la acera de enfrente puede estar en la AGEB vecina (ver ADR 0001).
    centros = [(a_numero(z["lat"]), a_numero(z["lon"])) for z in zonas]
    for tipo, campo in (("farmacia", "farmacias_radio"), ("salud", "salud_radio")):
        pts = [(float(p["lat"]), float(p["lon"])) for p in puntos if p["tipo"] == tipo]
        for z, n in zip(zonas, _contar_en_radio(centros, pts, radio_m)):
            z[campo] = n

    elegibles = [z for z in zonas if z["elegible"]]
    _normalizar(elegibles, "poblacion", "n_poblacion")
    _normalizar(elegibles, "pct_60ymas", "n_edades")
    # Nivel socioeconómico (sustituto de ingreso, D2): promedio de escolaridad, % de viviendas con auto,
    # con internet y con computadora, cada uno normalizado 0-100.
    for campo in ("escolaridad", "pct_viv_auto", "pct_viv_internet", "pct_viv_pc"):
        _normalizar(elegibles, campo, f"_n_{campo}")
    for z in elegibles:
        partes = [z[f"_n_{c}"] for c in ("escolaridad", "pct_viv_auto", "pct_viv_internet", "pct_viv_pc") if z[f"_n_{c}"] is not None]
        z["n_ingreso"] = round(sum(partes) / len(partes), 2) if partes else None
    _normalizar(elegibles, "salud_radio", "n_salud")
    _normalizar(elegibles, "farmacias_radio", "n_competencia", inverso=True)

    for z in elegibles:
        disponibles = [c for c in COMPONENTES if pesos[c] > 0 and z[f"n_{c}"] is not None]
        peso_disp = sum(pesos[c] for c in disponibles)
        z["ipa"] = round(sum(pesos[c] * z[f"n_{c}"] for c in disponibles) / peso_disp, 1) if peso_disp else None
        z["variables_faltantes"] = len([c for c in COMPONENTES if pesos[c] > 0]) - len(disponibles)
        z["por_que"] = _explicar(z, pesos)

    # ---------------------------------------------------------------- reglas de calidad
    hoy = dt.date.fromisoformat(version)
    reglas = []

    def regla(id_, texto, umbral, valor, ok, accion, **extra):
        reglas.append({"id": id_, "regla": texto, "umbral": umbral, "valor": valor,
                       "resultado": "OK" if ok else "FALLA", "accion": accion, **extra})

    cvegeos = [z["cvegeo"] for z in zonas]
    regla("R1", "CVEGEO único en la tabla curated", "0 duplicados", len(cvegeos) - len(set(cvegeos)),
          len(cvegeos) == len(set(cvegeos)), "bloquea")

    con_pob = sum(1 for z in zonas if z["poblacion"] is not None)
    pct_r3 = round(100 * con_pob / len(zonas), 2) if zonas else 0
    regla("R3", "AGEB de las seis alcaldías con población", ">= 95 %", f"{pct_r3} %", pct_r3 >= 95, "bloquea")

    detalle_r4, ok_r4, verificable = [], True, False
    for t in totales:
        ref = a_numero(t["pob_localidades_urbanas"])
        suma = sum(z["poblacion"] or 0 for z in zonas if z["cve_mun"] == t["cve_mun"])
        if not ref:
            detalle_r4.append({"alcaldia": ALCALDIAS.get(t["cve_mun"]), "estado": "sin total de referencia"})
            continue
        verificable = True
        dif = round(100 * (suma - ref) / ref, 3)
        ok_r4 &= abs(dif) <= 1
        detalle_r4.append({"alcaldia": ALCALDIAS.get(t["cve_mun"]), "suma_ageb": suma, "total_localidades": ref,
                           "diferencia_pct": dif})
    regla("R4", "Suma de población por AGEB contra el total urbano de cada alcaldía", "±1 %",
          "ver detalle", ok_r4 if verificable else True, "bloquea" if verificable else "marca", detalle=detalle_r4)

    campos_n = [f"n_{c}" for c in COMPONENTES] + ["ipa"]
    fuera = sum(1 for z in elegibles for c in campos_n if z.get(c) is not None and not 0 <= z[c] <= 100)
    regla("R5", "Indicadores normalizados e IPA dentro de 0-100", "100 %", f"{fuera} valores fuera de rango",
          fuera == 0, "bloquea")

    edad_censo = hoy.year - 2020
    meses_denue = _antiguedad_meses(man["fuentes"]["denue"].get("last_modified"), hoy)
    ok_r7 = edad_censo <= 10 and (meses_denue is None or meses_denue <= 24)
    regla("R7", "Antigüedad de las fuentes", "Censo <= 10 años; DENUE <= 24 meses",
          {"censo_anios": edad_censo, "denue_meses": meses_denue}, ok_r7, "marca")

    completas = sum(1 for z in elegibles if z["variables_faltantes"] == 0)
    pct_r8 = round(100 * completas / len(elegibles), 2) if elegibles else 0
    regla("R8", "AGEB elegibles con todas las variables", ">= 80 % (si no, plan B: bajar a alcaldía/colonia)",
          f"{pct_r8} %", pct_r8 >= 80, "marca")

    rankeables = sorted((z for z in elegibles if z["ipa"] is not None), key=lambda z: (-z["ipa"], z["cvegeo"]))
    regla("N1", "Ranking con al menos 10 zonas", ">= 10", len(rankeables), len(rankeables) >= 10, "bloquea")

    # ---------------------------------------------------------------- etiqueta de confianza
    for z in zonas:
        if not z["elegible"]:
            z["confianza"] = ""
            continue
        malas = z["variables_faltantes"] + (1 if z["estado_dato"] != "ok" else 0) + (0 if ok_r7 else 1)
        z["confianza"] = "Alta" if malas == 0 else ("Media" if malas == 1 else "Baja")
    for i, z in enumerate(rankeables, 1):
        z["posicion"] = i

    bloqueantes = [r for r in reglas if r["accion"] == "bloquea" and r["resultado"] == "FALLA"]
    estado = "BLOQUEADO" if bloqueantes else ("APROBADO_CON_MARCAS" if any(r["resultado"] == "FALLA" for r in reglas) else "APROBADO")
    reporte = {"version_raw": version, "estado": estado, "pesos": pesos, "min_poblacion": min_pob,
               "agebs_estudio": len(zonas), "agebs_elegibles": len(elegibles), "agebs_en_ranking": len(rankeables),
               "reglas": reglas, "generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    almacen.escribir_json(gold, f"calidad/version={version}/reporte.json", reporte)

    if bloqueantes:
        alertar(f"Pharmacy Pulse: carga {version} BLOQUEADA",
                {"reglas_fallidas": bloqueantes, "reporte": f"s3://{gold}/calidad/version={version}/reporte.json"})
        return {"estado": estado, "version": version, "reglas_fallidas": [r["id"] for r in bloqueantes]}

    # ---------------------------------------------------------------- publicación
    cols = ["posicion", "ipa", "confianza", "alcaldia", "colonia_referencia", "cvegeo", "poblacion", "pct_60ymas",
            "escolaridad", "pct_viv_auto", "pct_viv_internet", "pct_viv_pc", "farmacias_radio", "salud_radio", "farmacias", "farmacias_10k", "unidades_salud",
            "pct_afiliada_salud",
            "n_poblacion", "n_edades", "n_ingreso", "n_salud", "n_competencia", "por_que", "lat", "lon"]
    todas = sorted(zonas, key=lambda z: (z.get("posicion") or 10**9, z["cvegeo"]))
    almacen.escribir_texto(gold, f"zonas_ipa/version={version}/zonas_ipa.csv",
                           csv_a_texto(todas, cols[:6] + ["elegible", "estado_dato", "establecimientos", "salud_10k",
                                                          "radio_m", "variables_faltantes"] + cols[6:]), "text/csv; charset=utf-8")
    for z in rankeables:
        z["version_raw"] = version  # el ranking registra con qué versión de bronze se calculó
    ranking = csv_a_texto(rankeables[:max(top_n, 10)], cols + ["version_raw"])
    almacen.escribir_texto(gold, f"ranking/version={version}/ranking.csv", ranking, "text/csv; charset=utf-8")
    almacen.escribir_texto(gold, "ranking/actual/ranking.csv", ranking, "text/csv; charset=utf-8")
    almacen.escribir_json(gold, f"_manifiestos/version={version}.json", {
        "version_raw": version, "estado_calidad": estado, "pesos": pesos,
        "zonas": f"zonas_ipa/version={version}/zonas_ipa.csv", "ranking": f"ranking/version={version}/ranking.csv",
        "puntos_silver": f"denue_puntos/version={version}/denue_puntos.csv",
    })
    if estado != "APROBADO":
        alertar(f"Pharmacy Pulse: carga {version} aprobada con marcas",
                [r for r in reglas if r["resultado"] == "FALLA"])
    top = rankeables[0] if rankeables else {}
    LOG.info(json.dumps({"estado": estado, "version": version, "zonas": len(rankeables),
                         "primera": top.get("colonia_referencia"), "ipa": top.get("ipa")}, ensure_ascii=False))
    return {"estado": estado, "version": version, "zonas_en_ranking": len(rankeables)}
