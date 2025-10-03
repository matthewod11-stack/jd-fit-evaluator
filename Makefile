.PHONY: setup lint test score ui migrate-schema guardpaths

setup:
	python -m venv .venv || true; . .venv/bin/activate; pip install -e .[dev]

lint:
	ruff check src tests || true

test:
	pytest -q || true

score:
	python -m jd_fit_evaluator.cli score data/sample --role "product-designer" --explain -o out

ui:
	PYTHONPATH=. streamlit run ui/app.py

migrate-schema:
	python -m jd_fit_evaluator.cli migrate_schema < legacy.json > canonical.json

guardpaths:
	! grep -R "sys\.path\.insert" -n src tests ui || (echo "ERROR: sys.path.insert found" && exit 1)
