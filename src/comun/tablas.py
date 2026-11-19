"""Utilidades de CSV, números y alertas, sin dependencias externas."""
import csv
import io
import json
import logging
import os

LOG = logging.getLogger()
LOG.setLevel("INFO")

# Las 16 alcaldías de la CDMX (entidad 09), con su clave INEGI de municipio.
TODAS_LAS_ALCALDIAS = {
    "002": "Azcapotzalco", "003": "Coyoacán", "004": "Cuajimalpa de Morelos", "005": "Gustavo A. Madero",
    "006": "Iztacalco", "007": "Iztapalapa", "008": "La Magdalena Contreras", "009": "Milpa Alta",
    "010": "Álvaro Obregón", "011": "Tláhuac", "012": "Tlalpan", "013": "Xochimilco",
    "014": "Benito Juárez", "015": "Cuauhtémoc", "016": "Miguel Hidalgo", "017": "Venustiano Carranza",
}
# Por defecto, las seis del RFP (sección 6). Variable de entorno ALCALDIAS: "todas" o claves separadas por coma.
ALCALDIAS_RFP = "003,005,007,010,012,014"


def _alcaldias():
    valor = os.environ.get("ALCALDIAS", ALCALDIAS_RFP).strip().lower()
    claves = TODAS_LAS_ALCALDIAS if valor == "todas" else [c.strip().zfill(3) for c in valor.split(",") if c.strip()]
    desconocidas = [c for c in claves if c not in TODAS_LAS_ALCALDIAS]
    if desconocidas:
        raise ValueError(f"Claves de alcaldía desconocidas en ALCALDIAS: {desconocidas}")
    return {c: TODAS_LAS_ALCALDIAS[c] for c in sorted(claves)}


ALCALDIAS = _alcaldias()
ENTIDAD = "09"


def a_numero(valor):
    """Convierte un valor del INEGI a float. '*', 'N/D', vacío -> None."""
    if valor is None:
        return None
    v = str(valor).strip()
    if v in ("", "*", "N/D", "ND", "NA", "nan"):
        return None
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return None


def redondear(x, n=4):
    return None if x is None else round(x, n)


def csv_a_texto(filas, columnas):
    """CSV determinista: mismas filas -> mismos bytes (idempotencia)."""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columnas, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for f in filas:
        w.writerow({k: ("" if f.get(k) is None else f.get(k)) for k in columnas})
    return buf.getvalue()


def texto_a_filas(texto):
    return list(csv.DictReader(io.StringIO(texto)))


def detectar_codificacion(muestra):
    """INEGI publica archivos en UTF-8 (a veces con BOM) o en Latin-1."""
    corte = muestra.rfind(b"\n")
    muestra = muestra[:corte] if corte > 0 else muestra
    try:
        muestra.decode("utf-8")
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "latin-1"


def alertar(asunto, mensaje):
    """Publica en SNS si está configurado; siempre deja el mensaje en el log."""
    LOG.warning(json.dumps({"alerta": asunto, "detalle": mensaje}, ensure_ascii=False, default=str))
    topic = os.environ.get("ALERTS_TOPIC_ARN")
    if not topic or os.environ.get("LOCAL_DATA_DIR"):
        return
    import boto3
    texto = mensaje if isinstance(mensaje, str) else json.dumps(mensaje, ensure_ascii=False, indent=2, default=str)
    boto3.client("sns").publish(TopicArn=topic, Subject=asunto[:100], Message=texto[:250000])
