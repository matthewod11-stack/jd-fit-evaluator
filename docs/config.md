# JD-Fit Evaluator Configuration Reference

Environment variables use the prefix `JD_FIT_`. Values map to `AppConfig` in `src/jd_fit_evaluator/config.py`.

| Variable | Description | Default |
|----------|-------------|---------|
| `JD_FIT_ENV` | Environment name (`dev`, `prod`) | `dev` |
| `JD_FIT_OUT_DIR` | Output directory for artifacts | `out` |
| `JD_FIT_LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |
| `JD_FIT_EMBEDDINGS__PROVIDER` | Embedding provider (`openai`, `ollama`, `mock`) | `openai` |
| `JD_FIT_EMBEDDINGS__MODEL` | Embedding model | `text-embedding-3-small` |
| `JD_FIT_EMBEDDINGS__BATCH_SIZE` | Batch size for embeddings | `256` |
| `JD_FIT_EMBEDDINGS__TIMEOUT_S` | Timeout in seconds | `60` |

Example `.env`:

```bash
JD_FIT_ENV=dev
JD_FIT_OUT_DIR=out
JD_FIT_LOG_LEVEL=DEBUG
JD_FIT_EMBEDDINGS__PROVIDER=ollama
JD_FIT_EMBEDDINGS__MODEL=llama3:8b
JD_FIT_EMBEDDINGS__BATCH_SIZE=128
JD_FIT_EMBEDDINGS__TIMEOUT_S=90
```
