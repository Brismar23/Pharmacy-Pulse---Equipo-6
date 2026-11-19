#!/usr/bin/env bash
# Despliega todo en AWS con la CLI: buckets, código de las Lambdas y funciones.
#
#   AWS_REGION=us-east-1 ALERT_EMAIL=equipo@correo.com ./scripts/deploy.sh
#
# Requisitos: AWS CLI v2 configurada (aws configure) con permisos de CloudFormation,
# S3, Lambda, IAM, EventBridge, SNS, CloudWatch y Budgets.
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT=${PROJECT:-pharmacy-pulse}
ENVIRONMENT=${ENVIRONMENT:-dev}
REGION=${AWS_REGION:-us-east-1}
ALERT_EMAIL=${ALERT_EMAIL:-}
STORAGE_STACK="$PROJECT-$ENVIRONMENT-storage"
LAMBDAS_STACK="$PROJECT-$ENVIRONMENT-lambdas"
export AWS_REGION=$REGION

echo "==> 1/4 Buckets ($STORAGE_STACK, $REGION)"
aws cloudformation deploy --template-file infra/Buckets.yaml --stack-name "$STORAGE_STACK" \
  --parameter-overrides ProjectName="$PROJECT" Environment="$ENVIRONMENT" --no-fail-on-empty-changeset

ARTIFACTS=$(aws cloudformation describe-stacks --stack-name "$STORAGE_STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='ArtifactsBucketName'].OutputValue" --output text)

echo "==> 2/4 Empaquetar y subir código a s3://$ARTIFACTS/lambdas/"
./scripts/build.sh
for z in dist/*.zip; do
  aws s3 cp "$z" "s3://$ARTIFACTS/lambdas/$(basename "$z")"
done

echo "==> 3/4 Lambdas ($LAMBDAS_STACK)"
aws cloudformation deploy --template-file infra/Lambdas.yaml --stack-name "$LAMBDAS_STACK" \
  --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset \
  --parameter-overrides ProjectName="$PROJECT" Environment="$ENVIRONMENT" \
    StorageStackName="$STORAGE_STACK" AlertEmail="$ALERT_EMAIL"

echo "==> 4/4 Refrescar el código (CloudFormation no detecta un zip nuevo con la misma ruta)"
for n in ingesta limpieza indicadores mapa; do
  aws lambda update-function-code --function-name "$PROJECT-$ENVIRONMENT-$n" \
    --s3-bucket "$ARTIFACTS" --s3-key "lambdas/$n.zip" --query LastModified --output text
done

cat <<EOF

Listo. Para correr la primera carga:
  aws lambda invoke --function-name $PROJECT-$ENVIRONMENT-ingesta --invocation-type Event --payload '{}' \\
      --cli-binary-format raw-in-base64-out /dev/stdout

Las otras tres Lambdas se disparan solas. En unos minutos:
  ./scripts/descargar_resultados.sh
EOF
