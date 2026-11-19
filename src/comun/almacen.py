"""Lectura y escritura de objetos en S3, o en una carpeta local para pruebas.

En AWS se usa boto3 (ya viene en el runtime de Lambda). Si existe la variable
de entorno LOCAL_DATA_DIR, cada bucket se simula con una carpeta:
LOCAL_DATA_DIR/<bucket>/<key>. Así el mismo código corre en la laptop
(scripts/run_local.py) y en Lambda.
"""
import hashlib
import json
import os
import pathlib
import shutil

_s3 = None


def _local_root():
    raiz = os.environ.get("LOCAL_DATA_DIR")
    return pathlib.Path(raiz) if raiz else None


def _cliente():
    global _s3
    if _s3 is None:
        import boto3  # incluido en el runtime de Lambda
        _s3 = boto3.client("s3")
    return _s3


def _ruta(bucket, key):
    return _local_root() / bucket / key


def existe(bucket, key):
    if _local_root():
        return _ruta(bucket, key).is_file()
    from botocore.exceptions import ClientError
    try:
        _cliente().head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


def leer_bytes(bucket, key):
    if _local_root():
        return _ruta(bucket, key).read_bytes()
    return _cliente().get_object(Bucket=bucket, Key=key)["Body"].read()


def leer_json(bucket, key):
    return json.loads(leer_bytes(bucket, key).decode("utf-8"))


def escribir_bytes(bucket, key, datos, content_type="application/octet-stream"):
    if _local_root():
        p = _ruta(bucket, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(datos)
        return
    _cliente().put_object(Bucket=bucket, Key=key, Body=datos, ContentType=content_type)


def escribir_texto(bucket, key, texto, content_type="text/plain; charset=utf-8"):
    escribir_bytes(bucket, key, texto.encode("utf-8"), content_type)


def escribir_json(bucket, key, obj):
    texto = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    escribir_texto(bucket, key, texto + "\n", "application/json")


def descargar(bucket, key, destino):
    destino = pathlib.Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if _local_root():
        shutil.copyfile(_ruta(bucket, key), destino)
    else:
        _cliente().download_file(bucket, key, str(destino))
    return destino


def subir(origen, bucket, key, content_type="application/zip"):
    if _local_root():
        p = _ruta(bucket, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origen, p)
        return
    _cliente().upload_file(str(origen), bucket, key, ExtraArgs={"ContentType": content_type})


def sha256_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def key_del_evento(event):
    """Devuelve (bucket, key) de un evento 'Object Created' de EventBridge o de S3."""
    detalle = event.get("detail") or {}
    if detalle.get("object"):
        return detalle["bucket"]["name"], detalle["object"]["key"]
    registros = event.get("Records") or []
    if registros:
        s3 = registros[0]["s3"]
        from urllib.parse import unquote_plus
        return s3["bucket"]["name"], unquote_plus(s3["object"]["key"])
    return None, event.get("key")
