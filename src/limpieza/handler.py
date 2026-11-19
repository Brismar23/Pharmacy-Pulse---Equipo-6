"""Lambda 2 · limpieza: S3 bronze -> S3 silver.

Se dispara cuando aparece un manifiesto nuevo en bronze (_manifiestos/fecha=...json).
Lee los zips del INEGI sin modificarlos y escribe tablas limpias en silver, en una
carpeta por versión (la fecha de descarga de bronze):

    censo_ageb/version=F/censo_ageb.csv        una fila por AGEB urbana de las 6 alcaldías
    censo_totales/version=F/censo_totales.csv  totales oficiales por alcaldía (regla R4)
    denue_ageb/version=F/denue_ageb.csv        conteos DENUE por AGEB (farmacias, salud, total)
    denue_puntos/version=F/denue_puntos.csv    farmacias y unidades de salud de toda la CDMX (radio de 500 m y mapa)
    calidad/version=F/limpieza.json            reglas R2 y R6 y conteos de la limpieza
    _manifiestos/version=F.json                se escribe al final y dispara la Lambda de indicadores

No hace uniones espaciales: el DENUE ya trae la clave de AGEB de cada establecimiento
(ver ADR 0001).
"""
import collections
import csv
import datetime as dt
import io
import json
import os
import pathlib
import re
import tempfile
import zipfile

from comun import almacen
from comun.tablas import ALCALDIAS, ENTIDAD, LOG, a_numero, csv_a_texto, detectar_codificacion

# Clases SCIAN (ver docs/decision_log.md, decisión D3).
SCIAN_FARMACIAS = {"464111", "464112"}         # farmacias sin minisúper / con minisúper
PREFIJOS_SALUD = ("621", "622")                 # consultorios y hospitales
# Recuadro que contiene a la CDMX (regla R2).
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 19.0, 19.65, -99.40, -98.90

COLS_CENSO = ["POBTOT", "P_60YMAS", "P_0A2", "PDER_SS", "PSINDER", "GRAPROES",
              # nivel socioeconómico (viviendas particulares habitadas con auto, internet y computadora)
              "TVIVPARHAB", "VPH_AUTOM", "VPH_INTER", "VPH_PC", "PAFIL_IPRIV",
              # grupos de edad para filtrar por edad (0-2, 3-5, 6-11, 12-17, 18-24, 25-59, 60-64, 65+)
              "P_3A5", "P_6A11", "P_12A14", "P_15A17", "P_18A24", "P_18YMAS", "POB65_MAS"]


def _abrir_csv_del_zip(ruta_zip, patron):
    """Abre el CSV más grande del zip cuyo nombre cumpla el patrón; devuelve un DictReader."""
    z = zipfile.ZipFile(ruta_zip)
    candidatos = [i for i in z.infolist() if i.filename.lower().endswith(".csv") and re.search(patron, i.filename.lower())]
    if not candidatos:
        raise ValueError(f"No hay CSV que cumpla '{patron}' en {ruta_zip.name}: {z.namelist()[:20]}")
    info = max(candidatos, key=lambda i: i.file_size)
    with z.open(info) as f:
        cod = detectar_codificacion(f.read(65536))
    texto = io.TextIOWrapper(z.open(info), encoding=cod, newline="")
    lector = csv.DictReader(texto)
    lector.fieldnames = [c.strip().lstrip("﻿").strip('"') for c in lector.fieldnames]
    return lector, info.filename, cod


def _limpiar_censo(ruta_zip):
    lector, nombre, cod = _abrir_csv_del_zip(ruta_zip, r"conjunto_de_datos|ageb")
    upper = {c.upper(): c for c in lector.fieldnames}
    faltan = [c for c in ["ENTIDAD", "MUN", "LOC", "AGEB", "MZA", *COLS_CENSO] if c not in upper]
    if faltan:
        raise ValueError(f"Al CSV del Censo le faltan columnas: {faltan}")
    g = lambda fila, c: (fila.get(upper[c]) or "").strip()

    agebs, totales = [], {m: {"cve_mun": m, "pob_alcaldia_oficial": None, "pob_localidades_urbanas": 0.0}
                          for m in ALCALDIAS}
    for fila in lector:
        ent, mun = g(fila, "ENTIDAD").zfill(2), g(fila, "MUN").zfill(3)
        if ent != ENTIDAD or mun not in ALCALDIAS:
            continue
        loc, ageb, mza = g(fila, "LOC").zfill(4), g(fila, "AGEB").upper().zfill(4), g(fila, "MZA").zfill(3)
        if mza != "000":
            continue  # se trabaja a nivel AGEB, no manzana
        pob = a_numero(g(fila, "POBTOT"))
        if loc == "0000" and ageb == "0000":
            totales[mun]["pob_alcaldia_oficial"] = pob
        elif ageb == "0000":
            totales[mun]["pob_localidades_urbanas"] += pob or 0
        else:
            reg = {
                "cvegeo": f"{ent}{mun}{loc}{ageb}",
                "clave_ageb": f"{ent}{mun}{ageb}",
                "cve_mun": mun,
                "alcaldia": ALCALDIAS[mun],
                "cve_loc": loc,
                "ageb": ageb,
                "estado_dato": "N/D" if g(fila, "POBTOT").upper() == "N/D" or g(fila, "P_60YMAS").upper() == "N/D" else "ok",
            }
            for c in COLS_CENSO:
                reg[c.lower()] = a_numero(g(fila, c))
            agebs.append(reg)
    agebs.sort(key=lambda r: r["cvegeo"])
    return agebs, [totales[m] for m in sorted(totales)], {"archivo": nombre, "codificacion": cod}


def _limpiar_denue(ruta_zip):
    lector, nombre, cod = _abrir_csv_del_zip(ruta_zip, r"denue")
    lower = {c.lower(): c for c in lector.fieldnames}
    necesarias = ["id", "nom_estab", "codigo_act", "cve_ent", "cve_mun", "ageb", "latitud", "longitud"]
    faltan = [c for c in necesarias if c not in lower]
    if faltan:
        raise ValueError(f"Al CSV del DENUE le faltan columnas: {faltan}")
    g = lambda fila, c: (fila.get(lower[c]) or "").strip() if c in lower else ""

    vistos, cont = set(), collections.Counter()
    por_ageb = {}
    puntos = []
    for fila in lector:
        if g(fila, "cve_ent").zfill(2) != ENTIDAD:
            continue
        mun = g(fila, "cve_mun").zfill(3)
        cont["leidos_cdmx"] += 1
        ident = g(fila, "id")
        if ident in vistos:
            cont["duplicados_eliminados"] += 1
            continue
        vistos.add(ident)
        lat, lon = a_numero(g(fila, "latitud")), a_numero(g(fila, "longitud"))
        if lat is None or lon is None or not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            cont["coordenadas_invalidas_descartadas"] += 1
            continue
        # Farmacias y unidades de salud de TODA la CDMX: la competencia no respeta límites de alcaldía.
        act = g(fila, "codigo_act")
        tipo = "farmacia" if act in SCIAN_FARMACIAS else ("salud" if act.startswith(PREFIJOS_SALUD) else None)
        ageb = g(fila, "ageb").upper().replace("-", "").zfill(4) if g(fila, "ageb") else ""
        if tipo:
            puntos.append({"id": ident, "tipo": tipo, "nombre": g(fila, "nom_estab")[:80], "codigo_act": act,
                           "cve_mun": mun, "clave_ageb": f"{ENTIDAD}{mun}{ageb}" if ageb else "",
                           "lat": f"{lat:.6f}", "lon": f"{lon:.6f}"})
        if mun not in ALCALDIAS:
            continue
        cont["leidos"] += 1
        if not ageb:
            cont["sin_ageb"] += 1
            continue
        clave = f"{ENTIDAD}{mun}{ageb}"
        cont["retenidos"] += 1
        a = por_ageb.setdefault(clave, {"clave_ageb": clave, "cve_mun": mun, "ageb": ageb, "establecimientos": 0,
                                        "suma_lat": 0.0, "suma_lon": 0.0, "farmacias": 0, "unidades_salud": 0,
                                        "colonias": collections.Counter()})
        a["establecimientos"] += 1
        a["suma_lat"] += lat
        a["suma_lon"] += lon
        colonia = g(fila, "nomb_asent")
        if colonia:
            a["colonias"][colonia.title()] += 1
        if tipo:
            a["farmacias" if tipo == "farmacia" else "unidades_salud"] += 1

    filas = []
    for clave in sorted(por_ageb):
        a = por_ageb[clave]
        n = a["establecimientos"]
        colonia = sorted(a["colonias"].items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if a["colonias"] else ""
        filas.append({"clave_ageb": clave, "cve_mun": a["cve_mun"], "ageb": a["ageb"], "establecimientos": n,
                      "farmacias": a["farmacias"], "unidades_salud": a["unidades_salud"],
                      "lat": f"{a['suma_lat'] / n:.6f}", "lon": f"{a['suma_lon'] / n:.6f}",
                      "colonia_principal": colonia})
    puntos.sort(key=lambda p: (p["tipo"], p["id"]))
    return filas, puntos, dict(cont), {"archivo": nombre, "codificacion": cod}


def lambda_handler(event, context=None):
    event = event or {}
    bronze, silver = os.environ["BRONZE_BUCKET"], os.environ["SILVER_BUCKET"]
    _, key = almacen.key_del_evento(event)
    if not key and event.get("fecha"):
        key = f"_manifiestos/fecha={event['fecha']}.json"
    if not key or not key.startswith("_manifiestos/"):
        return {"estado": "IGNORADO", "key": key}

    manifiesto = almacen.leer_json(bronze, key)
    version = manifiesto["fecha_descarga"]
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="limpieza_"))

    censo_zip = almacen.descargar(bronze, manifiesto["archivos"]["censo"]["key"], tmp / "censo.zip")
    agebs, totales, meta_censo = _limpiar_censo(censo_zip)
    censo_zip.unlink()
    denue_zip = almacen.descargar(bronze, manifiesto["archivos"]["denue"]["key"], tmp / "denue.zip")
    denue_ageb, puntos, cont, meta_denue = _limpiar_denue(denue_zip)
    denue_zip.unlink()

    reglas = [
        {"id": "R2", "regla": "Establecimientos DENUE retenidos con coordenadas válidas dentro de CDMX",
         "umbral": "100 % de los retenidos", "valor": "100 %", "descartados": cont.get("coordenadas_invalidas_descartadas", 0),
         "resultado": "OK", "accion": "bloquea"},
        {"id": "R6", "regla": "Registros DENUE duplicados tras limpieza", "umbral": "0",
         "valor": 0, "eliminados": cont.get("duplicados_eliminados", 0), "resultado": "OK", "accion": "marca"},
    ]
    if not agebs or not denue_ageb:
        raise ValueError(f"Limpieza vacía: {len(agebs)} AGEB del Censo, {len(denue_ageb)} AGEB del DENUE.")

    salidas = {
        f"censo_ageb/version={version}/censo_ageb.csv": csv_a_texto(agebs, [
            "cvegeo", "clave_ageb", "cve_mun", "alcaldia", "cve_loc", "ageb", "estado_dato",
            *[c.lower() for c in COLS_CENSO]]),
        f"censo_totales/version={version}/censo_totales.csv": csv_a_texto(totales, [
            "cve_mun", "pob_alcaldia_oficial", "pob_localidades_urbanas"]),
        f"denue_ageb/version={version}/denue_ageb.csv": csv_a_texto(denue_ageb, [
            "clave_ageb", "cve_mun", "ageb", "establecimientos", "farmacias", "unidades_salud", "lat", "lon",
            "colonia_principal"]),
        f"denue_puntos/version={version}/denue_puntos.csv": csv_a_texto(puntos, [
            "id", "tipo", "nombre", "codigo_act", "cve_mun", "clave_ageb", "lat", "lon"]),
    }
    for k, texto in salidas.items():
        almacen.escribir_texto(silver, k, texto, "text/csv; charset=utf-8")

    calidad = {"version_raw": version, "reglas": reglas, "conteos_denue": cont,
               "agebs_censo": len(agebs), "agebs_denue": len(denue_ageb), "puntos_mapa": len(puntos),
               "fuentes": {"censo": meta_censo, "denue": meta_denue}}
    almacen.escribir_json(silver, f"calidad/version={version}/limpieza.json", calidad)
    almacen.escribir_json(silver, f"_manifiestos/version={version}.json", {
        "version_raw": version, "manifiesto_bronze": key,
        "fuentes": manifiesto["archivos"], "tablas": sorted(salidas),
        "generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    })
    LOG.info(json.dumps({"estado": "OK", "version": version, **calidad["conteos_denue"]}))
    return {"estado": "OK", "version": version, "agebs_censo": len(agebs), "agebs_denue": len(denue_ageb)}
