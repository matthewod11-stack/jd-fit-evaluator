.PHONY: setup lint test score ui migrate-schema guardpaths pipeline rename parse

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

pipeline:
	python -m jd_fit_evaluator.cli pipeline resumes_raw --role "product-designer" --use-llm --explain -o out

rename:
	python -m jd_fit_evaluator.cli rename resumes_raw

parse:
	python -m jd_fit_evaluator.cli parse resumes_raw -o out/parsed --use-llm

ingest-manifest:
	python -m jd_fit_evaluator.cli ingest-manifest data/test/test_manifest.csv -o data/ingest --verbose

score-mvp:
	python -m jd_fit_evaluator.cli parse data/test -o data/parsed && python -m jd_fit_evaluator.cli score data/parsed --role product --explain -o data/out
