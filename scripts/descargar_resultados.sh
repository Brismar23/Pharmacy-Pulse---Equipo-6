#!/usr/bin/env bash
# Baja de gold el último ranking, el mapa, el resumen y el reporte de calidad a outputs/.
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT=${PROJECT:-pharmacy-pulse}
ENVIRONMENT=${ENVIRONMENT:-dev}
GOLD=$(aws cloudformation describe-stacks --stack-name "$PROJECT-$ENVIRONMENT-storage" \
  --query "Stacks[0].Outputs[?OutputKey=='GoldBucketName'].OutputValue" --output text)
mkdir -p outputs
aws s3 cp "s3://$GOLD/ranking/actual/ranking.csv" outputs/ranking.csv
aws s3 cp "s3://$GOLD/mapa/actual/index.html" outputs/mapa.html
aws s3 cp "s3://$GOLD/resumen/actual/resumen.md" outputs/resumen.md
ULTIMO=$(aws s3 ls "s3://$GOLD/calidad/" | awk '{print $2}' | sort | tail -1)
aws s3 cp "s3://$GOLD/calidad/${ULTIMO}reporte.json" outputs/reporte_calidad.json
echo "Abre outputs/mapa.html en el navegador."
