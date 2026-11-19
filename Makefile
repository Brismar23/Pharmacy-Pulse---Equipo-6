.PHONY: muestra local pipeline test lint build deploy resultados analisis limpiar

muestra:        ## genera la muestra sintética con formato INEGI
	python3 scripts/generar_muestra.py data/muestra

local pipeline: ## corre las 4 Lambdas en local (muestra sintética o CENSO=... DENUE=...)
	python3 scripts/run_local.py $(if $(CENSO),--censo $(CENSO)) $(if $(DENUE),--denue $(DENUE))

test:           ## pruebas: punta a punta, idempotencia, reglas y S3 simulado
	python3 -m unittest discover -s tests -v

lint:           ## valida las plantillas de CloudFormation
	cfn-lint infra/Buckets.yaml infra/Lambdas.yaml

build:          ## dist/<lambda>.zip
	./scripts/build.sh

deploy:         ## despliega en AWS (AWS_REGION, ALERT_EMAIL)
	./scripts/deploy.sh

resultados:     ## baja ranking, mapa y reporte desde gold
	./scripts/descargar_resultados.sh

analisis:       ## análisis CDMX con ML, gráficas y demo (pip install -r requirements-analisis.txt)
	python3 scripts/analisis/analisis_cdmx.py

limpiar:
	rm -rf dist outputs .local_s3 data/muestra
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
