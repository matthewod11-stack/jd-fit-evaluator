# Enrich & Rename Resumes by Candidate Name
Run after splitting to fill `full_name` and rename PDFs to `<full_name>.pdf`.

## Usage
```bash
source .venv/bin/activate
pip install -r tools/requirements.txt
python tools/enrich_manifest_names.py --glob "data/raw/batch-0*/candidate_manifest.csv"
```

Outputs `candidate_manifest.enriched.csv` per batch with updated `resume_file` paths.