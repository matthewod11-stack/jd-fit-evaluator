## Copilot / AI Agent quick guide (concise)

This repo implements a multi-signal candidate-to-job fit evaluator (resume parsing → feature extraction → scoring → rationales). Use this file to get productive quickly as an AI coding agent.

What to read first (by order):
- `README.md` (high-level workflows & env vars)
- `Makefile` (quick commands: `make setup`, `make ui`, `make health`, `make score`)
- `src/` — key places:
	- `src/jd_fit_evaluator/cli.py` (primary CLI entrypoints)
	- `src/scoring/features.py`, `src/scoring/finalize.py`, `src/scoring/weights.py` (scoring logic)
	- `src/models/embeddings.py` and `src/models/llm.py` (embedding/LLM providers & fallbacks)
	- `app/api.py` (FastAPI), `ui/app.py` (Streamlit UI)

Essential workflows & commands (examples):
- Create venv & deps: `make setup` (or `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`).
- Run sample scoring (no data needed): `python -m jd_fit_evaluator.cli score --sample --role "Senior Product Designer"`
- Launch UI: `make ui` or `python -m jd_fit_evaluator.cli ui` (Streamlit at :8501)
- Start API server: `python -m uvicorn app.api:app --reload`
- Batch optimized run: `python optimized_final_run.py run-optimized <manifest> <profile.json> --workers 8 --batch-size 32 --out out`

Tests and dev notes:
- Run tests: `pytest` (many tests import core modules directly; `tests/test_direct.py` shows using `sys.path.insert(0, "src")` to import package code).
- Health check: `make health` runs a lightweight optimized final-run health routine.

Configuration & conventions:
- Settings come from Pydantic-backed `Settings` and environment variables with prefix `JD_FIT_`. Use a `.env` for local config (see `README.md` examples).
- Embeddings/LLM providers support `mock`, `openai`, and `ollama` with graceful fallbacks — see `src/models/embeddings.py` and `src/models/llm.py` for provider-specific behaviour.
- Data formats:
	- Candidate JSON: `{candidate_id, name, stints: [...], skills: [...], ...}`
	- Scoring output: `{fit_score: float, rationale: [str], component_scores: {...}}`

Patterns to preserve when editing code:
- Prefer `pathlib.Path` for paths, avoid hardcoding relative paths.
- Favor graceful degradation (mock provider) instead of hard failures for external services.
- Scoring weights/config live in `src/scoring/weights.py` — change here for algorithm tweaks.

Files to inspect for common tasks:
- Parsing & ingestion: `tools/split_resumes_and_manifest.py`, `src/parsing/`.
- Scoring internals: `src/scoring/features.py`, `src/scoring/finalize.py`.
- Embeddings/LLM: `src/models/embeddings.py`, `src/models/llm.py`.
- Integration: `app/api.py`, `ui/app.py`, `optimized_final_run.py` (batch orchestration).

If anything here is unclear or you want more examples (tests to inspect, common bug patterns, or CR suggestions), tell me which area to expand.