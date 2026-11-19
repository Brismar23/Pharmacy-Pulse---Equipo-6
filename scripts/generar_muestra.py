#!/usr/bin/env python3
"""Genera una MUESTRA SINTÉTICA con el mismo formato que los archivos del INEGI.

Sirve para probar el pipeline completo sin internet ni AWS. NO son datos reales:
las colonias se llaman "Zona demo ..." para que nunca se confundan con resultados.

    python3 scripts/generar_muestra.py data/muestra

Crea:
    ageb_mza_urbana_09_cpv2020_csv.zip   (Censo 2020, AGEB y manzana urbana, CDMX)
    denue_09_csv.zip                     (DENUE CDMX, codificado en Latin-1 como el original)

Incluye a propósito casos difíciles: asteriscos (*), N/D, AGEB con poca población,
registros duplicados, coordenadas inválidas y una alcaldía fuera del estudio.
Semilla fija: produce siempre los mismos archivos.
"""
import csv
import io
import pathlib
import random
import sys
import zipfile

SEMILLA = 20261118
ALCALDIAS = {  # clave: (nombre, n_ageb, lat, lon, dispersión)
    "003": ("Coyoacán", 120, 19.330, -99.150, 0.030),
    "005": ("Gustavo A. Madero", 170, 19.490, -99.110, 0.035),
    "007": ("Iztapalapa", 220, 19.355, -99.060, 0.035),
    "010": ("Álvaro Obregón", 140, 19.355, -99.215, 0.030),
    "012": ("Tlalpan", 130, 19.285, -99.170, 0.030),
    "014": ("Benito Juárez", 60, 19.375, -99.160, 0.018),
    "015": ("Cuauhtémoc", 40, 19.430, -99.150, 0.015),  # fuera del estudio: debe filtrarse
}
COLS_CENSO = ["ENTIDAD", "NOM_ENT", "MUN", "NOM_MUN", "LOC", "NOM_LOC", "AGEB", "MZA", "POBTOT", "POBFEM",
              "POBMAS", "P_0A2", "P_3A5", "P_6A11", "P_12A14", "P_15A17", "P_18A24", "P_18YMAS", "P_60YMAS", "POB65_MAS",
              "GRAPROES", "PDER_SS", "PSINDER", "PAFIL_IPRIV", "VIVTOT", "TVIVHAB", "TVIVPARHAB", "VPH_AUTOM", "VPH_INTER", "VPH_PC"]
COLS_DENUE = ["id", "nom_estab", "raz_social", "codigo_act", "nombre_act", "per_ocu", "tipo_vial", "nom_vial",
              "tipo_v_e_1", "nom_v_e_1", "tipo_v_e_2", "nom_v_e_2", "tipo_v_e_3", "nom_v_e_3", "numero_ext",
              "letra_ext", "edificio", "edificio_e", "numero_int", "letra_int", "tipo_asent", "nomb_asent",
              "tipoCenCom", "nom_CenCom", "num_local", "cod_postal", "cve_ent", "entidad", "cve_mun", "municipio",
              "cve_loc", "localidad", "ageb", "manzana", "telefono", "correoelec", "www", "tipoUniEco", "latitud",
              "longitud", "fecha_alta"]
ACTIVIDADES = [  # (código SCIAN, nombre, peso relativo)
    ("464111", "Comercio al por menor de productos farmacéuticos sin minisúper", 0),
    ("464112", "Comercio al por menor de productos farmacéuticos con minisúper", 0),
    ("621111", "Consultorios de medicina general del sector privado", 0),
    ("622111", "Hospitales generales del sector privado", 0),
    ("461110", "Comercio al por menor en tiendas de abarrotes, ultramarinos y misceláneas", 40),
    ("722517", "Restaurantes con servicio de preparación de tacos y tortas", 20),
    ("812110", "Salones y clínicas de belleza y peluquerías", 15),
    ("461121", "Comercio al por menor de carnes rojas", 8),
    ("811111", "Reparación mecánica en general de automóviles y camiones", 10),
    ("465311", "Comercio al por menor de artículos de papelería", 7),
]


def _ageb_clave(rng, usados):
    while True:
        base = f"{rng.randint(1, 999):03d}"
        clave = base + rng.choice("0123456789A")
        if clave not in usados:
            usados.add(clave)
            return clave


def generar(salida):
    rng = random.Random(SEMILLA)
    salida = pathlib.Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    filas_censo, filas_denue, ident = [], [], 10_000_000
    total_ent = 0
    for mun, (nom, n, lat0, lon0, disp) in ALCALDIAS.items():
        usados, agebs = set(), []
        for k in range(n):
            ageb = _ageb_clave(rng, usados)
            # población: casi todas residenciales; algunas casi vacías (parques, zonas industriales)
            pob = rng.choice([rng.randint(0, 300)] + [int(rng.lognormvariate(8.0, 0.45))] * 9)
            p60 = int(pob * rng.uniform(0.07, 0.24))
            esc = round(rng.uniform(8.5, 15.8) if mun in ("014", "003") else rng.uniform(7.8, 12.5), 2)
            afil = int(pob * rng.uniform(0.55, 0.85))
            lat, lon = lat0 + rng.gauss(0, disp), lon0 + rng.gauss(0, disp)
            fila = {"ENTIDAD": "09", "NOM_ENT": "Ciudad de México", "MUN": mun, "NOM_MUN": nom, "LOC": "0001",
                    "NOM_LOC": nom, "AGEB": ageb, "MZA": "000", "POBTOT": pob, "POBFEM": pob // 2 + 3,
                    "POBMAS": pob - pob // 2 - 3, "P_0A2": int(pob * 0.04), "P_60YMAS": p60, "GRAPROES": esc,
                    "PDER_SS": afil, "PSINDER": pob - afil, "VIVTOT": pob // 3, "TVIVHAB": pob // 3}
            viv = max(pob // 3, 1); rico = (esc - 7.8) / 8
            fila.update({"P_3A5": int(pob * .04), "P_6A11": int(pob * .08), "P_12A14": int(pob * .04), "P_15A17": int(pob * .04),
                         "P_18A24": int(pob * .1), "P_18YMAS": int(pob * .76), "POB65_MAS": int(p60 * .7),
                         "PAFIL_IPRIV": int(pob * rico * .2), "TVIVPARHAB": viv, "VPH_AUTOM": int(viv * (.25 + .6 * rico)),
                         "VPH_INTER": int(viv * (.55 + .4 * rico)), "VPH_PC": int(viv * (.35 + .55 * rico))})
            if pob < 30:
                fila.update({c: "*" for c in ("P_0A2", "P_60YMAS", "GRAPROES", "PDER_SS", "PSINDER", "VPH_AUTOM", "VPH_PC")})
            if k == 7:
                fila.update({"P_60YMAS": "N/D", "GRAPROES": "N/D", "PDER_SS": "N/D", "PSINDER": "N/D"})
            if k == 11:
                fila["GRAPROES"] = "*"
            agebs.append((fila, lat, lon))
        pob_mun = sum(f["POBTOT"] for f, _, _ in agebs)
        total_ent += pob_mun
        cabecera = {c: "" for c in COLS_CENSO}
        cabecera.update({"ENTIDAD": "09", "NOM_ENT": "Ciudad de México", "MUN": mun, "NOM_MUN": nom})
        filas_censo.append({**cabecera, "NOM_LOC": "Total de la entidad", "LOC": "0000", "AGEB": "0000", "MZA": "000",
                            "POBTOT": pob_mun + rng.randint(500, 3000)})  # incluye población rural
        filas_censo.append({**cabecera, "NOM_LOC": "Total de la localidad urbana", "LOC": "0001", "AGEB": "0000",
                            "MZA": "000", "POBTOT": pob_mun})
        for fila, lat, lon in agebs:
            filas_censo.append(fila)
            for m in range(1, 4):  # algunas manzanas: el pipeline debe ignorarlas
                filas_censo.append({**fila, "MZA": f"{m:03d}", "POBTOT": fila["POBTOT"] // 9})
            # ------------------------------------------------ establecimientos DENUE de la AGEB
            pob = fila["POBTOT"]
            colonia = f"Zona demo {mun}-{fila['AGEB']}"
            n_otros = max(2, int(pob / 45 * rng.uniform(0.4, 1.8)))
            n_farm = sum(1 for _ in range(int(pob / 900)) if rng.random() < rng.choice([0.03, 0.12, 0.3]))
            n_salud = sum(1 for _ in range(int(pob / 400)) if rng.random() < rng.uniform(0.05, 0.4))
            tipos = ([ACTIVIDADES[rng.choice([0, 1])] for _ in range(n_farm)] +
                     [ACTIVIDADES[rng.choice([2, 2, 2, 3])] for _ in range(n_salud)] +
                     rng.choices(ACTIVIDADES[4:], weights=[a[2] for a in ACTIVIDADES[4:]], k=n_otros))
            for cod, nom_act, _ in tipos:
                ident += 1
                filas_denue.append({c: "" for c in COLS_DENUE} | {
                    "id": ident, "nom_estab": f"ESTABLECIMIENTO DEMO {ident}", "codigo_act": cod,
                    "nombre_act": nom_act, "per_ocu": "0 a 5 personas", "tipo_asent": "COLONIA",
                    "nomb_asent": colonia.upper(), "cve_ent": "09", "entidad": "CIUDAD DE MÉXICO", "cve_mun": mun,
                    "municipio": nom.upper(), "cve_loc": "0001", "localidad": nom.upper(), "ageb": fila["AGEB"],
                    "manzana": f"{rng.randint(1, 40):03d}", "tipoUniEco": "Fijo",
                    "latitud": f"{lat + rng.gauss(0, 0.0025):.7f}", "longitud": f"{lon + rng.gauss(0, 0.0025):.7f}",
                    "fecha_alta": "2019-11"})
    filas_censo.insert(0, {**{c: "" for c in COLS_CENSO}, "ENTIDAD": "09", "NOM_ENT": "Ciudad de México", "MUN": "000",
                           "NOM_MUN": "Total de la entidad", "LOC": "0000", "AGEB": "0000", "MZA": "000", "POBTOT": total_ent})
    # casos sucios del DENUE: duplicados y coordenadas inválidas
    filas_denue += [dict(f) for f in rng.sample(filas_denue, 6)]
    for f in rng.sample(filas_denue, 4):
        g = dict(f)
        ident += 1
        g.update({"id": ident, "latitud": "0", "longitud": "0"})
        filas_denue.append(g)

    def a_zip(ruta_zip, interno, filas, columnas, codificacion):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=columnas, lineterminator="\r\n")
        w.writeheader()
        w.writerows(filas)
        with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(interno, buf.getvalue().encode(codificacion))
            z.writestr(interno.split("/")[0] + "/LEEME_MUESTRA_SINTETICA.txt",
                       "Datos SINTETICOS generados por scripts/generar_muestra.py. No son datos del INEGI.\n")

    a_zip(salida / "ageb_mza_urbana_09_cpv2020_csv.zip",
          "ageb_mza_urbana_09_cpv2020/conjunto_de_datos/conjunto_de_datos_ageb_urbana_09_cpv2020.csv",
          filas_censo, COLS_CENSO, "utf-8-sig")
    a_zip(salida / "denue_09_csv.zip", "conjunto_de_datos/denue_inegi_09_.csv", filas_denue, COLS_DENUE, "latin-1")
    print(f"Muestra sintética en {salida}: {len(filas_censo)} filas de Censo, {len(filas_denue)} de DENUE")


if __name__ == "__main__":
    generar(sys.argv[1] if len(sys.argv) > 1 else "data/muestra")
