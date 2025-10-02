SHELL := /bin/bash

.PHONY: setup ingest score score-sample ui api health split-batch run-ui

health:
	@python -c "import importlib; [importlib.import_module(m) for m in ['typer','fastapi','streamlit','pydantic']]; print('OK: core deps present')"

setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

# Split a multi-resume PDF into individual PDFs + manifest
split-batch:
	@[ -n "$$INPUT" ] || (echo "Usage: make split-batch INPUT=data/raw/batch-01/all_resumes.pdf BATCH=batch-01 [GUIDE=data/raw/batch-01/guide.yaml]"; exit 2)
	python tools/split_resumes_and_manifest.py --input "$$INPUT" --batch-id "$$BATCH" $(if $(GUIDE),--guide "$(GUIDE)",) --auto

# Example: make split-batch INPUT=data/raw/batch-01/all_resumes.pdf BATCH=batch-01

# Deprecated: Greenhouse Harvest (temporarily disabled)
ingest:
	@if [ -z "$$ENABLE_GH" ]; then echo "Deprecated: Greenhouse Harvest ingestion temporarily disabled. Set ENABLE_GH=1 to run."; exit 2; fi
	python -m src.cli ingest

score:
	python -m src.cli score data/sample/jd.txt

score-sample:
	python -m src.cli score data/sample/jd.txt --sample

ui:
	streamlit run ui/app.py

# Run Streamlit UI with project root on PYTHONPATH so absolute imports work
.PHONY: run-ui
run-ui:
	PYTHONPATH=. streamlit run ui/app.py

api:
	uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
