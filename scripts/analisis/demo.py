"""Demo web (un solo HTML, sin servidor ni CDN): docs/demo/index.html."""
import json
import pathlib

import pandas as pd

RAIZ = pathlib.Path(__file__).resolve().parents[2]
PLANTILLA = pathlib.Path(__file__).resolve().parent / "demo_plantilla.html"
LEAFLET = RAIZ / "src" / "mapa" / "vendor"
SALIDA = RAIZ / "docs" / "demo" / "index.html"


def construir(d, z, p, tipos):
    pr = lambda s: s.rank(pct=True) * 100
    comp = 100 - pr(d.farm_500m)
    sc = {"ipa": d.ipa, "edad": .5 * pr(d.pct60) + .5 * comp, "pob": .5 * pr(d.pob) + .5 * comp,
          "sesA": .5 * pr(d.ses) + .5 * comp, "sesB": .5 * (100 - pr(d.ses)) + .5 * comp, "hueco": pr(d.brecha)}
    # grupos de edad: 0-2, 3-5, 6-11, 12-17, 18-24, 25-59, 60-64, 65+
    ed = z.set_index("cvegeo")
    edades = pd.DataFrame({"a": ed.p02, "b": ed.p35, "c": ed.p611, "d": ed.p1214 + ed.p1517, "e": ed.p1824,
                           "f": ed.p18mas - ed.p1824 - ed.p60, "g": ed.p60 - ed.p65, "h": ed.p65})
    r1 = lambda x: None if pd.isna(x) else round(float(x), 1)
    Z = []
    for i, r in d.iterrows():
        Z.append([r.cvegeo, r.alcaldia, r.colonia if isinstance(r.colonia, str) else "", tipos.index(r.segmento), int(r.pob), r1(r.pct60), r1(r.esc),
                  r1(r.pct_auto), r1(r.pct_inter), r1(r.pct_priv), int(r.farm_500m), int(r.salud_500m), int(round(r.dist_farm_m)), r1(r.farm_esperadas),
                  r1(r.ses), 1 if r.verificado_google_maps == "sin farmacia a 500 m" else 0, round(r.lat, 5), round(r.lon, 5)]
                 + [r1(sc[k][i]) for k in ["ipa", "edad", "pob", "sesA", "sesB", "hueco"]]
                 + [r1(comp[i]), [None if pd.isna(v) else int(v) for v in edades.loc[r.cvegeo]]])
    F = [[round(a, 5), round(b, 5), n if isinstance(n, str) else ""] for t, a, b, n in p.itertuples(index=False) if t == "farmacia"]
    datos = json.dumps({"Z": Z, "F": F, "SEG": list(tipos)}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (PLANTILLA.read_text(encoding="utf-8").replace("/*LEAFLET_CSS*/", (LEAFLET / "leaflet.css").read_text(encoding="utf-8"))
            .replace("/*LEAFLET_JS*/", (LEAFLET / "leaflet.js").read_text(encoding="utf-8")).replace("/*DATA*/", datos))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(html, encoding="utf-8")
    print(f"  {len(Z)} zonas y {len(F)} farmacias en {SALIDA.relative_to(RAIZ)} ({len(html) // 1024} KB)")
