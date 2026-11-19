#!/usr/bin/env python3
"""Análisis completo de la CDMX: dónde abrir la nueva sucursal de Pharmacy Pulse.

Entrada (data/extraido/, generada con extraer_inegi_navegador.js):
    cdmx_zonas_inegi.csv          una fila por AGEB urbana de las 16 alcaldías (Censo 2020 + resumen DENUE)
    cdmx_totales_alcaldias.csv    totales oficiales de población (regla R4)
    cdmx_puntos_denue.csv         farmacias y unidades de salud de la CDMX con coordenadas
    verificacion_google_maps.csv  zonas revisadas a mano en Google Maps

Pasos:
    1. Indicadores por zona: competencia y consultorios a 500 m, nivel socioeconómico, edad, IPA.
    2. Machine learning no supervisado: k-means (5 tipos de zona) y PCA para visualizar.
    3. Machine learning supervisado: random forest que estima cuántas farmacias "debería" tener
       cada zona por su gente y su comercio; la diferencia con las reales es el hueco.
    4. Gráficas (docs/resultados/), tabla final (data/resultados/) y demo web (docs/demo/).

Uso:  python3 scripts/analisis/analisis_cdmx.py
"""
import pathlib
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import r2_score, silhouette_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.neighbors import BallTree, NearestNeighbors
from sklearn.preprocessing import StandardScaler

RAIZ = pathlib.Path(__file__).resolve().parents[2]
EXTRAIDO = RAIZ / "data" / "extraido"
RESULTADOS = RAIZ / "data" / "resultados"
SEMILLA = 0
RADIO_M = 500
MIN_POB = 500
PESOS = {"n_pob": .30, "n_edad": .15, "n_ses": .15, "n_salud": .10, "n_comp": .30}  # SOW 7.4
TIPOS = ["Residencial alto y poca competencia", "Clase media-alta con más adultos mayores", "Clase media popular y poblada",
         "Periferia popular joven", "Popular densa y saturada"]


def cargar():
    z = pd.read_csv(EXTRAIDO / "cdmx_zonas_inegi.csv", dtype={"cvegeo": str, "cve_mun": str})
    p = pd.read_csv(EXTRAIDO / "cdmx_puntos_denue.csv")
    t = pd.read_csv(EXTRAIDO / "cdmx_totales_alcaldias.csv", dtype={"cve_mun": str})
    v = pd.read_csv(EXTRAIDO / "verificacion_google_maps.csv", dtype={"cvegeo": str})
    return z, p, t, v


def calidad(z, t):
    """Reglas del SOW 6.3 que aplican al análisis. Se detiene si una bloqueante falla."""
    suma = z.groupby("cve_mun").pob.sum()
    dif = ((suma.reindex(t.cve_mun).values - t.pob_localidades_urbanas) / t.pob_localidades_urbanas * 100).abs().max()
    reglas = {"R1 cvegeo único": z.cvegeo.is_unique, "R3 zonas con población >= 95 %": z.pob.notna().mean() >= .95,
              "R4 suma de población vs total oficial <= 1 %": dif <= 1}
    for nombre, ok in reglas.items():
        print(f"  {'OK   ' if ok else 'FALLA'} {nombre}")
    print(f"  INFO zonas con datos del DENUE: {100 * z.lat.notna().mean():.1f} %")
    if not all(reglas.values()):
        sys.exit("Falla una regla bloqueante: revisa la extracción.")


def indicadores(z, p):
    ok = z.lat.notna()
    centros = np.radians(z.loc[ok, ["lat", "lon"]].to_numpy())
    for tipo, col in (("farmacia", "farm_500m"), ("salud", "salud_500m")):
        arbol = BallTree(np.radians(p[p.tipo == tipo][["lat", "lon"]].to_numpy()), metric="haversine")
        z.loc[ok, col] = arbol.query_radius(centros, r=RADIO_M / 6371000, count_only=True)
        if tipo == "farmacia":
            z.loc[ok, "dist_farm_m"] = arbol.query(centros, k=1)[0][:, 0] * 6371000
    pct = lambda a, b: 100 * z[a] / z[b]
    z["pct60"], z["pct02"], z["pct_der"], z["pct_priv"], z["pct_imss"] = pct("p60", "pob"), pct("p02", "pob"), pct("der", "pob"), pct("priv", "pob"), pct("imss", "pob")
    z["pct_auto"], z["pct_inter"], z["pct_pc"] = pct("auto", "viv"), pct("inter", "viv"), pct("pc", "viv")
    z["est_log"] = np.log1p(z.establecimientos)
    e = z[(z.pob >= MIN_POB) & ok].copy()

    def norm(c, inv=False):  # min-max 0-100 recortado a percentiles 5-95 (ADR 0001)
        lo, hi = e[c].quantile(.05), e[c].quantile(.95)
        n = 100 * (e[c].clip(lo, hi) - lo) / (hi - lo)
        return 100 - n if inv else n
    e["n_pob"], e["n_edad"], e["n_salud"], e["n_comp"] = norm("pob"), norm("pct60"), norm("salud_500m"), norm("farm_500m", True)
    e["n_ses"] = pd.concat([norm(c) for c in ["esc", "pct_auto", "pct_inter", "pct_pc"]], axis=1).mean(axis=1, skipna=True)
    num = sum(e[k].fillna(0) * w for k, w in PESOS.items()); den = sum(e[k].notna() * w for k, w in PESOS.items())
    e["ipa"] = num / den
    faltan = sum(e[k].isna() for k in PESOS) + e.nd
    e["confianza"] = np.select([faltan == 0, faltan == 1], ["Alta", "Media"], "Baja")
    e["ses"] = e[["esc", "pct_auto", "pct_inter", "pct_pc"]].rank(pct=True).mean(axis=1) * 100
    return e


def tipos_de_zona(e):
    """k-means con 5 grupos sobre 11 variables estandarizadas; nombres según el perfil de cada grupo."""
    F = ["pob", "pct60", "pct02", "esc", "pct_auto", "pct_inter", "pct_pc", "pct_priv", "pct_der", "farm_500m", "salud_500m"]
    X = e[F].copy(); X["pob"] = np.log(X.pob); X["salud_500m"] = np.log1p(X.salud_500m); X = X.dropna()
    Xs = StandardScaler().fit_transform(X)
    km = KMeans(5, n_init=50, random_state=SEMILLA).fit(Xs)
    pca = PCA(2).fit(Xs)
    e = e.loc[X.index].copy()
    e["grupo"] = km.labels_; e["pc1"], e["pc2"] = pca.transform(Xs).T
    perfil = e.groupby("grupo")[["pct_priv", "farm_500m", "pct60"]].mean()
    nombre, resto = {}, list(perfil.index)
    for etiqueta, col, mayor in [(TIPOS[0], "pct_priv", True), (TIPOS[4], "farm_500m", True), (TIPOS[3], "pct60", False), (TIPOS[1], "pct60", True)]:
        g = perfil.loc[resto, col].idxmax() if mayor else perfil.loc[resto, col].idxmin()
        nombre[g] = etiqueta; resto.remove(g)
    nombre[resto[0]] = TIPOS[2]
    e["segmento"] = e.grupo.map(nombre)
    print(f"  k-means: silueta {silhouette_score(Xs, km.labels_):.3f}; PCA explica {100 * pca.explained_variance_ratio_[0]:.0f} % "
          f"y {100 * pca.explained_variance_ratio_[1]:.0f} %")
    return e, 100 * pca.explained_variance_ratio_[0]


def modelo_hueco(e, v):
    """Random forest: farmacias a 500 m esperadas por la gente y el comercio de la zona (sin ubicación ni consultorios)."""
    F = ["pob", "pct60", "pct02", "esc", "pct_auto", "pct_inter", "pct_pc", "pct_priv", "pct_der", "pct_imss", "est_log"]
    NOM = {"pob": "Habitantes", "pct60": "% 60 años o más", "pct02": "% bebés 0-2 años", "esc": "Escolaridad", "pct_auto": "% viviendas con auto",
           "pct_inter": "% con internet", "pct_pc": "% con computadora", "pct_priv": "% seguro privado", "pct_der": "% afiliada a salud",
           "pct_imss": "% con IMSS", "est_log": "Negocios en la zona (actividad comercial)"}
    d = e.dropna(subset=F + ["farm_500m"]).copy()
    rf = RandomForestRegressor(500, min_samples_leaf=5, random_state=SEMILLA, n_jobs=-1)
    d["farm_esperadas"] = cross_val_predict(rf, d[F], d.farm_500m, cv=KFold(5, shuffle=True, random_state=SEMILLA))
    r2 = r2_score(d.farm_500m, d.farm_esperadas)
    d["brecha"] = d.farm_esperadas - d.farm_500m
    rf.fit(d[F], d.farm_500m)
    pi = permutation_importance(rf, d[F], d.farm_500m, n_repeats=10, random_state=SEMILLA, scoring="r2")
    imp = pd.Series(pi.importances_mean, index=[NOM[f] for f in F]).sort_values(ascending=False)
    # zonas gemelas: las 10 más parecidas en gente y comercio
    S = ["pob", "pct60", "esc", "pct_auto", "pct_inter", "pct_priv", "pct_der", "est_log"]
    _, idx = NearestNeighbors(n_neighbors=11).fit(StandardScaler().fit_transform(d[S])).kneighbors(StandardScaler().fit_transform(d[S]))
    med, txt = [], []
    for fila in idx:
        g = d.iloc[fila[1:]]; med.append(g.farm_500m.median()); top = g.sort_values("farm_500m", ascending=False).head(3)
        txt.append("; ".join(f"{c} ({a.replace('Gustavo A. Madero', 'GAM')}, {int(f)} farm.)" for c, a, f in zip(top.colonia, top.alcaldia, top.farm_500m)))
    d["farm_gemelas_mediana"], d["zonas_gemelas"] = med, txt
    d["oportunidad"] = (d.brecha >= 3) & (d.farm_500m <= d.farm_gemelas_mediana / 2) & (d.pob >= 1500)
    sin = set(v[v.resultado == "sin farmacia a 500 m"].cvegeo)
    d["verificado_google_maps"] = np.where(d.cvegeo.isin(sin), "sin farmacia a 500 m", "")
    print(f"  random forest: R2 validación cruzada {r2:.3f}; {d.oportunidad.sum()} zonas con hueco; "
          f"{(d.verificado_google_maps != '').sum()} confirmadas en Google Maps")
    return d, imp, r2


def guardar_tabla(d):
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    d = d.sort_values("ipa", ascending=False).copy(); d.insert(0, "posicion_ipa", range(1, len(d) + 1))
    cols = ["posicion_ipa", "cvegeo", "alcaldia", "colonia", "segmento", "ipa", "confianza", "pob", "pct60", "esc", "pct_auto", "pct_inter", "pct_pc",
            "pct_priv", "pct_der", "establecimientos", "farm_500m", "salud_500m", "dist_farm_m", "farm_esperadas", "brecha", "farm_gemelas_mediana",
            "zonas_gemelas", "oportunidad", "verificado_google_maps", "lat", "lon"]
    out = d[cols].copy()
    for c in ["ipa", "pct60", "pct_auto", "pct_inter", "pct_pc", "pct_priv", "pct_der", "farm_esperadas", "brecha"]:
        out[c] = out[c].round(1)
    out["dist_farm_m"] = out.dist_farm_m.round(0)
    out.to_csv(RESULTADOS / "cdmx_zonas_farmacias_analisis_completo.csv", index=False, encoding="utf-8-sig")
    return d


def main():
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import demo
    import graficas
    print("1. Datos y calidad"); z, p, t, v = cargar(); calidad(z, t)
    print("2. Indicadores"); e = indicadores(z, p); print(f"  {len(e)} zonas con 500 habitantes o más")
    print("3. Tipos de zona (k-means)"); e, var1 = tipos_de_zona(e)
    print("4. Hueco de farmacias (random forest)"); d, imp, r2 = modelo_hueco(e, v)
    d = guardar_tabla(d)
    print("5. Gráficas"); graficas.generar(d, z, imp, r2, var1, TIPOS)
    print("6. Demo web"); demo.construir(d, z, p, TIPOS)
    print("Listo: data/resultados/, docs/resultados/ y docs/demo/index.html")


if __name__ == "__main__":
    main()
