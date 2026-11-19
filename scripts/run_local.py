#!/usr/bin/env python3
"""Corre las cuatro Lambdas en tu computadora, sin AWS (los buckets se simulan con carpetas).

Uso:
    # 1) con la muestra sintética (no necesita internet)
    python3 scripts/run_local.py

    # 2) con los archivos REALES del INEGI que descargaste a mano
    python3 scripts/run_local.py --censo ~/Descargas/ageb_mza_urbana_09_cpv2020_csv.zip \\
                                 --denue ~/Descargas/denue_09_csv.zip

Resultados en outputs/: ranking.csv, zonas_ipa.csv, reporte_calidad.json, resumen.md y mapa.html.
Para cambiar los pesos del IPA: PESOS_IPA='{"poblacion":0.4,...}' python3 scripts/run_local.py
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import pathlib
import shutil
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

BUCKETS = {"BRONZE_BUCKET": "pharmacy-pulse-local-bronze", "SILVER_BUCKET": "pharmacy-pulse-local-silver",
           "GOLD_BUCKET": "pharmacy-pulse-local-gold"}
URLS = {"CENSO_URL": "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/ageb_manzana/ageb_mza_urbana_09_cpv2020_csv.zip",
        "DENUE_URL": "https://www.inegi.org.mx/contenidos/masiva/denue/denue_09_csv.zip"}


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(f"lambda_{nombre}", RAIZ / "src" / nombre / "handler.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.lambda_handler


def evento_s3(bucket, key):
    """Mismo formato que manda EventBridge cuando S3 crea un objeto."""
    return {"source": "aws.s3", "detail-type": "Object Created", "detail": {"bucket": {"name": bucket}, "object": {"key": key}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--censo", help="zip del Censo 2020 por AGEB (CDMX)")
    ap.add_argument("--denue", help="zip del DENUE de la CDMX")
    ap.add_argument("--fecha", default=dt.date.today().isoformat(), help="versión de bronze (fecha de descarga)")
    ap.add_argument("--datos", default=str(RAIZ / ".local_s3"), help="carpeta que simula S3")
    ap.add_argument("--salida", default=str(RAIZ / "outputs"))
    ap.add_argument("--limpiar", action="store_true", help="borra la carpeta que simula S3 antes de correr")
    a = ap.parse_args()

    if a.limpiar:
        shutil.rmtree(a.datos, ignore_errors=True)
    os.environ.update(BUCKETS | URLS | {"LOCAL_DATA_DIR": a.datos})
    censo, denue = a.censo, a.denue
    if not (censo and denue):
        muestra = RAIZ / "data" / "muestra"
        if not (muestra / "denue_09_csv.zip").exists():
            import generar_muestra  # noqa: E402  (scripts/ está en sys.path al ejecutar este archivo)
            generar_muestra.generar(muestra)
        censo, denue = muestra / "ageb_mza_urbana_09_cpv2020_csv.zip", muestra / "denue_09_csv.zip"
        print("AVISO: corriendo con la MUESTRA SINTÉTICA (no son datos reales del INEGI).")

    # "Subida manual" a bronze, como cuando INEGI bloquea la descarga desde AWS.
    bronze = pathlib.Path(a.datos) / BUCKETS["BRONZE_BUCKET"]
    for fuente, ruta in (("censo", censo), ("denue", denue)):
        nombre = URLS[f"{fuente.upper()}_URL"].split("/")[-1]
        destino = bronze / fuente / f"fecha={a.fecha}" / nombre
        if not destino.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ruta, destino)

    pasos = []
    r = cargar("ingesta")({"fecha": a.fecha, "solo_manifiesto": True}); pasos.append(("ingesta", r))
    r = cargar("limpieza")(evento_s3(BUCKETS["BRONZE_BUCKET"], r["manifiesto"])); pasos.append(("limpieza", r))
    r = cargar("indicadores")(evento_s3(BUCKETS["SILVER_BUCKET"], f"_manifiestos/version={a.fecha}.json")); pasos.append(("indicadores", r))
    if r["estado"] != "BLOQUEADO":
        r = cargar("mapa")(evento_s3(BUCKETS["GOLD_BUCKET"], f"_manifiestos/version={a.fecha}.json")); pasos.append(("mapa", r))
    for nombre, res in pasos:
        print(f"{nombre:12s} {json.dumps(res, ensure_ascii=False)}")

    gold = pathlib.Path(a.datos) / BUCKETS["GOLD_BUCKET"]
    salida = pathlib.Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    copias = {f"calidad/version={a.fecha}/reporte.json": "reporte_calidad.json",
              f"zonas_ipa/version={a.fecha}/zonas_ipa.csv": "zonas_ipa.csv",
              f"ranking/version={a.fecha}/ranking.csv": "ranking.csv",
              f"resumen/version={a.fecha}/resumen.md": "resumen.md",
              f"mapa/version={a.fecha}/index.html": "mapa.html"}
    for origen, destino in copias.items():
        if (gold / origen).exists():
            shutil.copyfile(gold / origen, salida / destino)
    print(f"Resultados en {salida}/ (abre mapa.html en el navegador)")
    return 0 if pasos[-1][1]["estado"] != "BLOQUEADO" else 1


if __name__ == "__main__":
    sys.exit(main())
