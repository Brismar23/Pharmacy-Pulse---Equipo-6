"""Pruebas del pipeline completo con la muestra sintética.

    python3 -m unittest discover -s tests -v

* Sin dependencias: corre las cuatro Lambdas con buckets simulados en carpetas.
* Con `pip install boto3 moto`: además corre todo contra S3 simulado (mismas llamadas que en AWS)
  y prueba la descarga HTTP de la ingesta con un servidor local.
"""
import functools
import hashlib
import http.server
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
import generar_muestra  # noqa: E402
from comun import almacen  # noqa: E402

B = {"BRONZE_BUCKET": "t-bronze", "SILVER_BUCKET": "t-silver", "GOLD_BUCKET": "t-gold"}
FECHA = "2026-11-18"
MUESTRA = pathlib.Path(tempfile.mkdtemp(prefix="muestra_"))
generar_muestra.generar(MUESTRA)
ZIPS = {"censo": MUESTRA / "ageb_mza_urbana_09_cpv2020_csv.zip", "denue": MUESTRA / "denue_09_csv.zip"}


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(f"t_{nombre}", RAIZ / "src" / nombre / "handler.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.lambda_handler


def evento(bucket, key):
    return {"source": "aws.s3", "detail-type": "Object Created", "detail": {"bucket": {"name": B[bucket]}, "object": {"key": key}}}


def correr_todo(con_ingesta_http=False):
    if con_ingesta_http:
        r1 = cargar("ingesta")({"fecha": FECHA})
    else:
        for fuente, ruta in ZIPS.items():
            almacen.subir(ruta, B["BRONZE_BUCKET"], f"{fuente}/fecha={FECHA}/{ruta.name}")
        r1 = cargar("ingesta")({"fecha": FECHA, "solo_manifiesto": True})
    r2 = cargar("limpieza")(evento("BRONZE_BUCKET", r1["manifiesto"]))
    r3 = cargar("indicadores")(evento("SILVER_BUCKET", f"_manifiestos/version={FECHA}.json"))
    r4 = cargar("mapa")(evento("GOLD_BUCKET", f"_manifiestos/version={FECHA}.json")) if r3["estado"] != "BLOQUEADO" else None
    return r1, r2, r3, r4


def sha(bucket, key):
    return hashlib.sha256(almacen.leer_bytes(B[bucket], key)).hexdigest()


class PipelineLocal(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="s3local_")
        os.environ.update(B | {"LOCAL_DATA_DIR": self.dir, "CENSO_URL": "http://x/" + ZIPS["censo"].name,
                               "DENUE_URL": "http://x/" + ZIPS["denue"].name})
        os.environ.pop("PESOS_IPA", None)

    def test_punta_a_punta_y_reglas(self):
        _, r2, r3, r4 = correr_todo()
        self.assertEqual(r2["estado"], "OK")
        self.assertEqual(r3["estado"], "APROBADO")
        self.assertGreaterEqual(r3["zonas_en_ranking"], 10)  # N1
        self.assertEqual(r4["estado"], "OK")
        rep = almacen.leer_json(B["GOLD_BUCKET"], f"calidad/version={FECHA}/reporte.json")
        self.assertEqual({r["id"] for r in rep["reglas"]}, {"R1", "R3", "R4", "R5", "R7", "R8", "N1"})
        limp = almacen.leer_json(B["SILVER_BUCKET"], f"calidad/version={FECHA}/limpieza.json")
        self.assertGreater(limp["conteos_denue"]["duplicados_eliminados"], 0)          # R6 limpió duplicados
        self.assertGreater(limp["conteos_denue"]["coordenadas_invalidas_descartadas"], 0)  # R2 descartó
        ranking = almacen.leer_bytes(B["GOLD_BUCKET"], f"ranking/version={FECHA}/ranking.csv").decode()
        self.assertNotIn("Cuauhtémoc", ranking)  # solo las seis alcaldías del RFP
        html = almacen.leer_bytes(B["GOLD_BUCKET"], "mapa/actual/index.html").decode()
        self.assertIn("const ZONAS = [", html)

    def test_idempotencia(self):
        correr_todo()
        claves = [("GOLD_BUCKET", f"zonas_ipa/version={FECHA}/zonas_ipa.csv"), ("GOLD_BUCKET", f"ranking/version={FECHA}/ranking.csv"),
                  ("SILVER_BUCKET", f"censo_ageb/version={FECHA}/censo_ageb.csv"), ("SILVER_BUCKET", f"denue_ageb/version={FECHA}/denue_ageb.csv")]
        antes = [sha(*c) for c in claves]
        cargar("limpieza")(evento("BRONZE_BUCKET", f"_manifiestos/fecha={FECHA}.json"))
        cargar("indicadores")(evento("SILVER_BUCKET", f"_manifiestos/version={FECHA}.json"))
        self.assertEqual(antes, [sha(*c) for c in claves])

    def test_ingesta_no_sobrescribe_bronze(self):
        correr_todo()
        r = cargar("ingesta")({"fecha": FECHA})
        self.assertEqual(r["estado"], "YA_EXISTE")

    def test_regla_bloqueante_detiene_publicacion(self):
        correr_todo()
        # Se altera el total oficial de una alcaldía: R4 debe bloquear y no publicar ranking nuevo.
        k = f"censo_totales/version={FECHA}/censo_totales.csv"
        texto = almacen.leer_bytes(B["SILVER_BUCKET"], k).decode().splitlines()
        partes = texto[1].split(",")
        partes[2] = str(int(float(partes[2]) * 1.5))
        texto[1] = ",".join(partes)
        almacen.escribir_texto(B["SILVER_BUCKET"], k, "\n".join(texto) + "\n")
        os.remove(pathlib.Path(self.dir) / B["GOLD_BUCKET"] / f"ranking/version={FECHA}/ranking.csv")
        r = cargar("indicadores")(evento("SILVER_BUCKET", f"_manifiestos/version={FECHA}.json"))
        self.assertEqual(r["estado"], "BLOQUEADO")
        self.assertIn("R4", r["reglas_fallidas"])
        self.assertFalse(almacen.existe(B["GOLD_BUCKET"], f"ranking/version={FECHA}/ranking.csv"))

    def test_pesos_cambian_el_ranking_y_se_validan(self):
        correr_todo()
        base = almacen.leer_bytes(B["GOLD_BUCKET"], f"ranking/version={FECHA}/ranking.csv")
        os.environ["PESOS_IPA"] = json.dumps({"poblacion": 0.6, "edades": 0.1, "ingreso": 0.1, "salud": 0.1, "competencia": 0.1})
        cargar("indicadores")(evento("SILVER_BUCKET", f"_manifiestos/version={FECHA}.json"))
        self.assertNotEqual(base, almacen.leer_bytes(B["GOLD_BUCKET"], f"ranking/version={FECHA}/ranking.csv"))
        os.environ["PESOS_IPA"] = json.dumps({"poblacion": 0.6, "competencia": 0.6})
        with self.assertRaises(ValueError):
            cargar("indicadores")(evento("SILVER_BUCKET", f"_manifiestos/version={FECHA}.json"))


try:
    import boto3
    from moto import mock_aws
except ImportError:  # moto es opcional
    mock_aws = None


@unittest.skipIf(mock_aws is None, "instala boto3 y moto para probar contra S3 simulado")
class PipelineS3Simulado(unittest.TestCase):
    """Mismas llamadas a S3 que en AWS (head/get/put/upload/download) y descarga HTTP real."""

    def setUp(self):
        os.environ.pop("LOCAL_DATA_DIR", None)
        os.environ.pop("PESOS_IPA", None)
        os.environ.update({"AWS_DEFAULT_REGION": "us-east-1", "AWS_ACCESS_KEY_ID": "test", "AWS_SECRET_ACCESS_KEY": "test"})
        manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(MUESTRA))
        manejador.log_message = lambda *a: None
        self.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), manejador)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{self.http.server_port}/"
        os.environ.update(B | {"CENSO_URL": url + ZIPS["censo"].name, "DENUE_URL": url + ZIPS["denue"].name})
        self.mock = mock_aws()
        self.mock.start()
        almacen._s3 = None
        s3 = boto3.client("s3")
        for b in B.values():
            s3.create_bucket(Bucket=b)

    def tearDown(self):
        self.mock.stop()
        self.http.shutdown()
        almacen._s3 = None

    def test_punta_a_punta_en_s3_con_descarga(self):
        r1, r2, r3, r4 = correr_todo(con_ingesta_http=True)
        self.assertEqual(r1["estado"], "OK")
        man = almacen.leer_json(B["BRONZE_BUCKET"], r1["manifiesto"])
        self.assertEqual(man["archivos"]["denue"]["origen"], "descarga_inegi")
        self.assertEqual(len(man["archivos"]["censo"]["sha256"]), 64)
        self.assertEqual(r3["estado"], "APROBADO")
        self.assertEqual(r4["estado"], "OK")
        self.assertEqual(cargar("ingesta")({"fecha": FECHA})["estado"], "YA_EXISTE")
        objetos = boto3.client("s3").list_objects_v2(Bucket=B["GOLD_BUCKET"])["Contents"]
        claves = {o["Key"] for o in objetos}
        self.assertIn("ranking/actual/ranking.csv", claves)
        self.assertIn("mapa/actual/index.html", claves)


if __name__ == "__main__":
    unittest.main()
