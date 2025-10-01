# JD-Fit Evaluator (Greenhouse + Local Embeddings)

A **multi-signal, JD-anchored candidate evaluator**. Pulls applications from **Greenhouse**, computes **absolute fit to a Job Description**, and returns a **0–100 Fit Score** plus concise rationales.

- Signals: titles/level, industries/companies, tenure, skills (semantic), context disambiguation (e.g., *recruiting = hiring* vs *being recruited*), recency, bonus flags.
- Embeddings: **local Llama** via `llama-cpp-python` (with graceful fallback if model not present).
- Fine-tuning: classical model (LogReg/XGBoost-ready) trained on your historical labels.
- Interfaces: **CLI**, **FastAPI**, **Streamlit**.

## Quick Start

```bash
# 1) Create & activate venv, install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) Set env (copy and edit your token/job IDs)  # Deprecated (will return post-MVP)
cp .env.example .env

# 3) Try the sample scoring with local files (no Greenhouse needed)
make score-sample

# 4) Launch the UI
make ui
# or the API
make api
```

> **Local embeddings**: Drop a GGUF embedding-capable model in `models/` (e.g., `models/llama-3.1-8b-instruct-q5_0.gguf`). If not found, the app **falls back** to a deterministic pseudo-embedding so you can test the full flow without GPU/large models. Replace with your preferred local **GGUF** embedding model (LLaMA, Nomic, etc.).

## File-based Resume Ingestion (No Harvest API)

If you cannot use Greenhouse Harvest, you can ingest resumes from a single PDF per batch (~30 resumes).

**Step 1 — Split and build manifest**
source .venv/bin/activate
pip install -r tools/requirements.txt
make split-batch INPUT=data/raw/batch-01/all_resumes.pdf BATCH=batch-01
# (optional) add GUIDE=data/raw/batch-01/guide.yaml

**Outputs**
- data/raw/batch-01/resumes/<candidate_id>.pdf
- data/raw/batch-01/candidate_manifest.csv

**Step 2 — Ingest from manifest**
(Coming next: python -m src.cli ingest --manifest data/raw/batch-01/candidate_manifest.csv)

## Environment (Deprecated — Harvest API will return post-MVP)

Create `.env`:
```
GH_TOKEN=gh_harvest_token_here
GH_JOB_ID=123456
EMBED_MODEL_PATH=models/llama-3.1-8b-instruct-q5_0.gguf
EMBED_CTX=8192
```
Only `GH_TOKEN` is required for pulling real candidates; otherwise use the sample flow.

## Make Targets

- `make setup` – install deps, preflight
- `make split-batch` – split a multi-resume PDF into per-candidate PDFs + manifest
- `make ingest` – **Deprecated (will return post-MVP)** pull from Greenhouse for the configured `GH_JOB_ID`
- `make score` – score ingested candidates against `data/sample/jd.txt` (or your JD path via flag)
- `make score-sample` – score the included sample candidate JSON against the sample JD
- `make ui` – launch Streamlit at http://localhost:8501
- `make api` – launch FastAPI at http://localhost:8000

## Architecture

```
src/
  etl/greenhouse.py      # Harvest API ingestion (applications, candidates, attachments)
  parsing/resume.py      # PDF/DOCX/text extraction + normalization
  models/embeddings.py   # Local Llama embeddings w/ graceful fallback
  scoring/features.py    # Feature extraction (titles, industry, tenure, skills sim, context, recency, bonus)
  scoring/finalize.py    # Weighted fit score + rationale prompting
  training/train.py      # Classical fine-tune on historical labels
app/api.py               # FastAPI wrapper for programmatic scoring
ui/app.py                # Streamlit reviewer UI
data/sample/             # Sample JD + candidate JSON for local-only demo
```

## Legal & Ethics

- Keep AI as **decision support**, not auto-rejection. Show **why** and keep an audit trail.
- Handle PII responsibly; keep resumes local where possible.
- Version weights per JD for reproducibility.
