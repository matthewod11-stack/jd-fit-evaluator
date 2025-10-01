SHELL := /bin/bash

.PHONY: setup ingest score score-sample ui api

setup:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

ingest:
	python -m src.cli ingest

score:
	python -m src.cli score --jd data/sample/jd.txt

score-sample:
	python -m src.cli score --jd data/sample/jd.txt --sample

ui:
	streamlit run ui/app.py

api:
	uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
