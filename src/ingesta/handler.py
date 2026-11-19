"""Lambda 1 · ingesta: INEGI -> S3 bronze.

Descarga los dos archivos públicos del INEGI y los guarda tal cual en el
bucket bronze, en una carpeta por fuente y fecha de descarga:

    censo/fecha=2026-11-23/ageb_mza_urbana_09_cpv2020_csv.zip
    denue/fecha=2026-11-23/denue_09_csv.zip
    _manifiestos/fecha=2026-11-23.json   <- se escribe al final y dispara la Lambda de limpieza

Reglas:
* bronze nunca se sobrescribe: si el manifiesto de esa fecha ya existe, no se hace nada
  (idempotente). Para una carga nueva se usa otra fecha.
* Si INEGI bloquea la descarga desde AWS, se suben los zips a mano a las mismas rutas y se
  invoca con {"fecha": "AAAA-MM-DD", "solo_manifiesto": true}.

Evento (todo opcional): {"fecha": "AAAA-MM-DD", "solo_manifiesto": false}
"""
import datetime as dt
import json
import os
import pathlib
import tempfile
import urllib.request
import zipfile

from comun import almacen
from comun.tablas import LOG

USER_AGENT = "Mozilla/5.0 (compatible; PharmacyPulse-DataPipeline/1.0)"


def _hoy_cdmx():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/Mexico_City")).date()
    except Exception:  # sin base de zonas horarias: CDMX es UTC-6 todo el año
        return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=6)).date()


def _fuentes():
    return {
        "censo": os.environ["CENSO_URL"],
        "denue": os.environ["DENUE_URL"],
    }


def _descargar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=int(os.environ.get("HTTP_TIMEOUT", "120"))) as r, \
            open(destino, "wb") as f:
        cabeceras = {k.lower(): v for k, v in r.headers.items()}
        while True:
            bloque = r.read(1 << 20)
            if not bloque:
                break
            f.write(bloque)
    if not zipfile.is_zipfile(destino):
        raise ValueError(f"La respuesta de {url} no es un zip (¿página de error o bloqueo?).")
    return {
        "last_modified": cabeceras.get("last-modified"),
        "content_length": cabeceras.get("content-length"),
    }


def lambda_handler(event, context=None):
    event = event or {}
    bronze = os.environ["BRONZE_BUCKET"]
    fecha = event.get("fecha") or _hoy_cdmx().isoformat()
    dt.date.fromisoformat(fecha)  # valida el formato
    clave_manifiesto = f"_manifiestos/fecha={fecha}.json"

    if almacen.existe(bronze, clave_manifiesto):
        LOG.info(json.dumps({"estado": "YA_EXISTE", "manifiesto": clave_manifiesto}))
        return {"estado": "YA_EXISTE", "fecha": fecha, "manifiesto": clave_manifiesto}

    archivos = {}
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ingesta_"))
    for fuente, url in _fuentes().items():
        nombre = url.rstrip("/").split("/")[-1]
        key = f"{fuente}/fecha={fecha}/{nombre}"
        local = tmp / nombre
        info = {"url": url}
        if event.get("solo_manifiesto") or almacen.existe(bronze, key):
            # El archivo ya está en bronze (subida manual o reintento): no se vuelve a escribir.
            almacen.descargar(bronze, key, local)
            info["origen"] = "bronze_existente"
        else:
            info.update(_descargar(url, local))
            almacen.subir(local, bronze, key)
            info["origen"] = "descarga_inegi"
        info.update({
            "key": key,
            "bytes": local.stat().st_size,
            "sha256": almacen.sha256_archivo(local),
        })
        archivos[fuente] = info
        local.unlink()
        LOG.info(json.dumps({"fuente": fuente, **info}))

    manifiesto = {
        "fecha_descarga": fecha,
        "generado_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "archivos": archivos,
    }
    # El manifiesto va al final: solo existe si las dos fuentes quedaron completas.
    almacen.escribir_json(bronze, clave_manifiesto, manifiesto)
    return {"estado": "OK", "fecha": fecha, "manifiesto": clave_manifiesto}
