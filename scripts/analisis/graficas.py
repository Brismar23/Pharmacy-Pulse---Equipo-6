"""Gráficas del análisis de la CDMX (se guardan en docs/resultados/)."""
import pathlib

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

SALIDA = pathlib.Path(__file__).resolve().parents[2] / "docs" / "resultados"
SURF, INK, INK2, GRID, GRAY = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#c9c8c2"
BLUE, BLUE_D, RED = "#2a78d6", "#184f95", "#e34948"
DIVERGENTE = [BLUE_D, BLUE, "#f0efec", "#ec835a", RED]
SECUENCIAL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
FUENTE = "Fuente: INEGI, Censo de Población y Vivienda 2020 (AGEB urbana) y DENUE 05/2026. Zonas con 500 habitantes o más en las 16 alcaldías."
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold"})


def _corto(alcaldia):
    return alcaldia.replace("Gustavo A. Madero", "GAM").replace(" de Morelos", "")


def _titulo(fig, t, s):
    fig.subplots_adjust(top=0.95)
    alto = fig.get_size_inches()[1]  # el subtítulo puede tener varias líneas: el título va encima de todas
    fig.text(0.01, 1.02, s, ha="left", va="bottom", color=INK2, fontsize=11)
    fig.text(0.01, 1.02 + (s.count("\n") + 1) * 0.24 / alto + 0.12 / alto, t, ha="left", va="bottom", fontsize=16, fontweight="bold")


def _guardar(fig, nombre):
    SALIDA.mkdir(parents=True, exist_ok=True)
    fig.savefig(SALIDA / nombre, dpi=180, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def _sin_bordes(ax):
    for sp in ax.spines.values():
        sp.set_visible(False)


def generar(d, z, imp, r2, var1, tipos):
    e = d.copy()
    e["etq"] = e.colonia.fillna("") + " (" + e.alcaldia.map(_corto) + ")"
    rotulo = {t: t.replace(" y poca", "\ny poca").replace(" con más", "\ncon más").replace(" popular y", "\npopular y")
              .replace(" popular joven", "\npopular joven").replace(" y saturada", " y\nsaturada de farmacias") for t in tipos}
    verif = set(e.loc[e.verificado_google_maps != "", "cvegeo"])

    # 01 perfil de cada tipo de zona
    vars_ = [("pob", "Habitantes\n(mediana)", "{:,.0f}", "median"), ("pct60", "% 60 años\no más", "{:.0f}%", "mean"),
             ("esc", "Escolaridad\n(años)", "{:.1f}", "mean"), ("pct_auto", "% viviendas\ncon auto", "{:.0f}%", "mean"),
             ("pct_priv", "% con seguro\nprivado", "{:.0f}%", "mean"), ("farm_500m", "Farmacias\na 500 m", "{:.1f}", "mean"),
             ("salud_500m", "Consultorios\na 500 m", "{:.0f}", "median"), ("ipa", "IPA\n(0-100)", "{:.0f}", "mean")]
    M = pd.DataFrame({v: e.groupby("segmento")[v].agg(a) for v, _, _, a in vars_}).loc[tipos]
    Zs = (M - M.mean()) / M.std()
    fig, ax = plt.subplots(figsize=(12.5, 5.2))
    ax.imshow(Zs.values, cmap=LinearSegmentedColormap.from_list("div", DIVERGENTE), vmin=-1.8, vmax=1.8, aspect="auto")
    for i in range(len(tipos)):
        for j, (_, _, f, _) in enumerate(vars_):
            ax.text(j, i, f.format(M.values[i, j]), ha="center", va="center", fontsize=12, fontweight="bold",
                    color="white" if abs(Zs.values[i, j]) > 1.1 else INK)
    n = e.groupby("segmento").size()
    ax.set_xticks(range(len(vars_)), [l for _, l, _, _ in vars_], fontsize=10)
    ax.set_yticks(range(len(tipos)), [f"{rotulo[t]}  ·  {n[t]} zonas" for t in tipos], fontsize=10.5)
    ax.xaxis.tick_top(); ax.tick_params(length=0); _sin_bordes(ax)
    for k in range(1, len(tipos)):
        ax.axhline(k - .5, color=SURF, lw=3)
    for k in range(1, len(vars_)):
        ax.axvline(k - .5, color=SURF, lw=3)
    _titulo(fig, f"Machine learning: las {len(e):,} zonas de la CDMX se agrupan en 5 tipos",
            "k-means sobre 11 variables del Censo 2020 y el DENUE 2026. Rojo = muy por arriba del promedio de los 5 grupos; azul = muy por abajo.")
    fig.text(0.01, -0.04, FUENTE, color=INK2, fontsize=9)
    _guardar(fig, "01_tipos_de_zona_machine_learning.png")

    # 02 dónde está cada tipo
    fig, axs = plt.subplots(1, 5, figsize=(18, 6.2), sharex=True, sharey=True)
    for ax, t in zip(axs, tipos):
        ax.scatter(e.lon, e.lat, s=5, c=GRAY, lw=0)
        g = e[e.segmento == t]
        ax.scatter(g.lon, g.lat, s=9 + g.pob / 900, c=BLUE, lw=.6, edgecolor=SURF, alpha=.9)
        ax.set_title(rotulo[t], fontsize=11.5, loc="left"); ax.set_aspect(1 / np.cos(np.radians(19.35)))
        ax.set_xticks([]); ax.set_yticks([]); _sin_bordes(ax)
        ax.text(0, -0.04, f"{len(g)} zonas · {g.pob.sum() / 1e6:.2f} M hab.\nIPA promedio {g.ipa.mean():.0f}", transform=ax.transAxes,
                va="top", fontsize=10, color=INK2)
    _titulo(fig, "Dónde está cada tipo de zona", "Cada punto es una AGEB (en azul, las del grupo; en gris, el resto). Tamaño = habitantes. Las 16 alcaldías, norte arriba.")
    _guardar(fig, "02_mapa_tipos_de_zona.png")

    # 03 demanda contra competencia, por criterio
    lentes = [("pct60", "% de habitantes con 60 años o más", "Por edad", 1500), ("pob", "Habitantes de la zona", "Por población", 0),
              ("ses", "Índice socioeconómico (percentil 0-100)", "Por nivel socioeconómico", 1500)]
    fig, axs = plt.subplots(1, 3, figsize=(18, 6.4))
    rng = np.random.default_rng(0)
    for ax, (v, xl, t, minpob) in zip(axs, lentes):
        g = e[e.pob >= minpob].dropna(subset=[v])
        puntaje = .5 * g[v].rank(pct=True) + .5 * (1 - g.farm_500m.rank(pct=True))
        top = g.loc[puntaje.sort_values(ascending=False).index[:8]]
        ax.axvspan(g[v].quantile(.75), g[v].max() * 1.02, ymax=(g.farm_500m.quantile(.25) + .5) / (g.farm_500m.quantile(.99) + 1), color="#e8f1fb", zorder=0)
        ax.scatter(g[v], g.farm_500m + rng.uniform(-.25, .25, len(g)), s=10, c=GRAY, lw=0, zorder=1)
        ax.scatter(top[v], top.farm_500m, s=46, c=BLUE, edgecolor=SURF, lw=1.5, zorder=3)
        for k, (_, r) in enumerate(top.head(5).iterrows()):
            ax.annotate(str(k + 1), (r[v], r.farm_500m), xytext=(-4 - 9 * (k % 3), 7 + 9 * (k % 2)), textcoords="offset points",
                        fontsize=9.5, fontweight="bold", color=BLUE_D, zorder=4)
        lista = "\n".join(f"{k + 1}. {r.colonia} ({_corto(r.alcaldia)}) · {int(r.farm_500m)} farm." for k, (_, r) in enumerate(top.head(5).iterrows()))
        ax.text(0, -0.17, lista, transform=ax.transAxes, va="top", fontsize=10, color=INK, linespacing=1.5)
        ax.set_ylim(-0.8, g.farm_500m.quantile(.99) + 1); ax.set_xlabel(xl); ax.set_title(t, loc="left")
        ax.grid(axis="y", color=GRID, lw=.8); ax.set_axisbelow(True)
        if v == "pob":
            ax.set_xscale("log"); ax.set_xticks([500, 1000, 2000, 5000, 10000, 20000], ["500", "1 mil", "2 mil", "5 mil", "10 mil", "20 mil"])
    axs[0].set_ylabel("Farmacias a menos de 500 m (competencia)")
    _titulo(fig, "Dónde hay demanda y poca competencia",
            "Abajo a la derecha = mucha demanda y pocas farmacias (zona sombreada). En azul, las 8 mejores de cada criterio (50 % demanda, 50 % poca competencia).")
    _guardar(fig, "03_demanda_vs_competencia.png")

    # 04 top 15 IPA
    t15 = e.sort_values("ipa", ascending=False).head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.barh(range(15), t15.ipa, color=BLUE, height=.62)
    for i, (_, r) in enumerate(t15.iterrows()):
        ax.text(r.ipa + .6, i, f"{r.ipa:.0f}", va="center", fontsize=10.5, color=INK)
        ax.text(1, i, f"{r.pob:,.0f} hab · {int(r.farm_500m)} farm.", va="center", fontsize=9, color="white")
    ax.set_yticks(range(15), t15.etq, fontsize=10.5); ax.set_xlim(0, 100); ax.tick_params(length=0); ax.set_xticks([])
    ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
    _titulo(fig, "Las 15 zonas con mayor Índice de Potencial de Apertura",
            "IPA = 30 % población + 15 % edad 60+ + 15 % nivel socioeconómico + 10 % consultorios cerca + 30 % poca competencia.")
    _guardar(fig, "04_top15_ipa.png")

    # 05 vista de PCA
    fig, ax = plt.subplots(figsize=(11.5, 7))
    sc = ax.scatter(e.pc1, e.pc2, c=e.ipa, cmap=LinearSegmentedColormap.from_list("seq", SECUENCIAL), s=12 + e.pob / 700, lw=.4,
                    edgecolor=SURF, vmin=20, vmax=80)
    ajuste = {tipos[1]: (.3, .5), tipos[2]: (-.3, -.2)}
    for t in tipos:
        g = e[e.segmento == t]; dx, dy = ajuste.get(t, (0, 0))
        ax.text(g.pc1.median() + dx, g.pc2.median() + dy, rotulo[t], ha="center", va="center", fontsize=9.5, fontweight="bold", color=INK,
                bbox=dict(boxstyle="round,pad=.3", fc=SURF, ec=INK2, alpha=.9), zorder=5)
    cb = fig.colorbar(sc, ax=ax, shrink=.6, pad=.01); cb.set_label("IPA (0-100)"); cb.outline.set_visible(False)
    ax.set_xlabel(f"Componente 1 ({var1:.0f} % de la variación): más escolaridad, autos, internet y adultos mayores  →")
    ax.set_ylabel("Componente 2: más farmacias y consultorios alrededor  →"); ax.grid(color=GRID, lw=.6); ax.set_axisbelow(True)
    ax.set_ylim(e.pc2.quantile(.005) - .3, e.pc2.quantile(.995) + 1.2)
    _titulo(fig, "Así ve el algoritmo las zonas",
            "Análisis de componentes principales (PCA). Las mejores zonas están a la derecha (más nivel y edad) y abajo (menos competencia). Color = IPA; tamaño = habitantes.")
    _guardar(fig, "05_vista_machine_learning_pca.png")

    # 06 hueco de farmacias: esperadas contra reales
    op = e[e.oportunidad].sort_values("brecha", ascending=False).drop_duplicates("colonia")
    conf = op[op.cvegeo.isin(verif)]
    op = pd.concat([conf, op[~op.cvegeo.isin(verif)].head(18 - len(conf))]).sort_values("brecha", ascending=False).iloc[::-1]
    fig, ax = plt.subplots(figsize=(12, 9))
    for i, (_, r) in enumerate(op.iterrows()):
        ax.plot([r.farm_500m, r.farm_esperadas], [i, i], color=GRAY, lw=3, solid_capstyle="round", zorder=1)
        ax.scatter(r.farm_esperadas, i, s=90, color=GRAY, edgecolor=INK2, lw=1, zorder=2)
        ax.scatter(r.farm_500m, i, s=90, color=BLUE, edgecolor=SURF, lw=1.5, zorder=3)
        ax.text(r.farm_esperadas + .5, i, f"faltan ≈{r.brecha:.0f}", va="center", fontsize=9.5, color=INK2)
    ax.set_yticks(range(len(op)), [("✓ " if c in verif else "") + t for c, t in zip(op.cvegeo, op.etq)], fontsize=10.5)
    for etq, c in zip(ax.get_yticklabels(), op.cvegeo):
        if c in verif:
            etq.set_fontweight("bold")
    ax.tick_params(length=0); ax.set_xlabel("Farmacias a menos de 500 m"); ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.set_xlim(-0.5, 25)
    ax.scatter([], [], s=90, color=BLUE, label="Farmacias que hay (DENUE)")
    ax.scatter([], [], s=90, color=GRAY, edgecolor=INK2, label='Farmacias que "debería" tener según el modelo')
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False)
    _titulo(fig, "Zonas con demanda probada y casi sin competencia",
            "Un modelo aprendió cuántas farmacias tienen las zonas según su gente y actividad comercial. Estas tienen muchas menos de lo esperado.\n"
            "✓ = confirmado también en Google Maps: ninguna farmacia a menos de 500 m.")
    _guardar(fig, "06_zonas_con_hueco_de_farmacias.png")

    # 07 qué explica dónde hay farmacias
    fig, ax = plt.subplots(figsize=(10.5, 6))
    s = imp.iloc[::-1]
    ax.barh(range(len(s)), s.values, color=BLUE, height=.6)
    ax.set_yticks(range(len(s)), s.index, fontsize=10.5); ax.tick_params(length=0); ax.set_xticks([])
    ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
    for i, v in enumerate(s.values):
        ax.text(v + .005, i, f"{v:.2f}", va="center", fontsize=10)
    _titulo(fig, "Qué explica dónde hay farmacias en la CDMX",
            f"Importancia de cada variable en el modelo (random forest, validación cruzada; explica {100 * r2:.0f} % de la variación).\n"
            "La actividad comercial y tener auto pesan más que el número de habitantes.")
    _guardar(fig, "07_que_explica_donde_hay_farmacias.png")

    # 08 mapa de huecos
    fig, ax = plt.subplots(figsize=(11, 9.5))
    sc = ax.scatter(e.lon, e.lat, c=e.brecha.clip(-12, 12), cmap=LinearSegmentedColormap.from_list("div", DIVERGENTE[::-1]), vmin=-12, vmax=12,
                    s=8 + e.pob / 600, lw=.3, edgecolor=SURF)
    t = e[e.cvegeo.isin(verif)].sort_values("brecha", ascending=False)
    lista = []
    for k, (_, r) in enumerate(t.iterrows(), 1):
        ax.scatter(r.lon, r.lat, s=240, facecolor="none", edgecolor=INK, lw=2)
        ax.annotate(str(k), (r.lon, r.lat), xytext=(9, 7), textcoords="offset points", fontsize=12, fontweight="bold",
                    bbox=dict(boxstyle="circle,pad=.15", fc=SURF, ec="none", alpha=.85))
        lista.append(f"{k}. {r.colonia} ({_corto(r.alcaldia)}): {r.pob:,.0f} hab.")
    ax.text(0.0, -0.02, "\n".join(lista), transform=ax.transAxes, va="top", fontsize=10.5, linespacing=1.5)
    ax.set_aspect(1 / np.cos(np.radians(19.35))); ax.set_xticks([]); ax.set_yticks([]); _sin_bordes(ax)
    cb = fig.colorbar(sc, ax=ax, shrink=.5, pad=.01); cb.set_label("Farmacias que faltan (+) o sobran (−) vs. lo esperado"); cb.outline.set_visible(False)
    _titulo(fig, "Dónde faltan y dónde sobran farmacias",
            "Azul = menos farmacias de las que el modelo espera (oportunidad). Rojo = más de las esperadas (saturado). Círculos negros: confirmadas con Google Maps.")
    _guardar(fig, "08_mapa_donde_faltan_farmacias.png")

    # 09 las 16 alcaldías
    a = z.groupby("alcaldia").agg(pob=("pob", "sum"), farm=("farm_ageb", "sum"))
    a["farm_10k"] = 10000 * a.farm / a.pob
    o = e.groupby("alcaldia").agg(zonas=("cvegeo", "size"), op=("oportunidad", "sum"))
    a = a.join(o); a["pct_op"] = 100 * a.op / a.zonas
    a = a.sort_values("farm_10k"); a.index = a.index.map(_corto).str.replace("La Magdalena", "Magdalena")
    fig, axs = plt.subplots(1, 2, figsize=(15, 7.5), sharey=True)
    for ax, col, t, f in [(axs[0], "farm_10k", "Farmacias por cada 10 mil habitantes", "{:.1f}"), (axs[1], "pct_op", "% de sus zonas con hueco de farmacias", "{:.0f} %")]:
        ax.barh(range(len(a)), a[col], color=BLUE, height=.62)
        for i, v in enumerate(a[col]):
            ax.text(v + a[col].max() * .01, i, f.format(v), va="center", fontsize=10)
        ax.set_title(t, loc="left", fontweight="bold", fontsize=12.5); ax.set_xticks([]); _sin_bordes(ax); ax.tick_params(length=0)
    axs[0].set_yticks(range(len(a)), a.index, fontsize=11)
    fig.subplots_adjust(top=0.88, wspace=.08)
    fig.text(0.01, 1.0, "Las 16 alcaldías: dónde está saturado y dónde hay espacio", fontsize=16, fontweight="bold", va="bottom")
    fig.text(0.01, 0.955, "Izquierda: competencia total (DENUE 05/2026 entre población del Censo 2020). Derecha: zonas que tienen menos farmacias de las que el modelo espera.",
             color=INK2, fontsize=11, va="bottom")
    fig.savefig(SALIDA / "09_alcaldias_saturacion_y_huecos.png", dpi=180, bbox_inches="tight", facecolor=SURF); plt.close(fig)
    a[["pob", "farm", "farm_10k", "zonas", "op", "pct_op"]].round(1).to_csv(SALIDA.parents[1] / "data" / "resultados" / "resumen_por_alcaldia.csv")
