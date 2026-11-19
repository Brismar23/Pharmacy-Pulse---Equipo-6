#!/usr/bin/env bash
# Empaqueta cada Lambda de src/<nombre>/ en dist/<nombre>.zip.
# Cada zip lleva handler.py en la raíz y la carpeta comun/ (código compartido).
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist && mkdir dist
for d in src/*/; do
  n=$(basename "$d")
  [ "$n" = "comun" ] && continue
  python3 -I - "$d" "src/comun" "dist/$n.zip" <<'PY'
import sys, zipfile, pathlib
src, comun, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for base, prefijo in ((src, ""), (comun, "comun/")):
        for p in sorted(base.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
                z.write(p, prefijo + str(p.relative_to(base)))
PY
  echo "dist/$n.zip"
done
