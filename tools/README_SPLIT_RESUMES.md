# Split a Large PDF of Multiple Resumes

This tool splits one PDF (~30 resumes) into per-resume PDFs and generates a `candidate_manifest.csv`.

## Install (in your project venv)
source .venv/bin/activate
pip install -r tools/requirements.txt

## Run (AUTO)
python tools/split_resumes_and_manifest.py   --input data/raw/batch-01/all_resumes.pdf   --batch-id batch-01   --auto

## Run with a GUIDE (recommended for tricky batches)
guide.yaml (1-based page ranges):

2025-AGD-0001:
  name: "Jane Q. Designer"
  email: "jane@example.com"
  pages: [1, 3]
2025-AGD-0002:
  name: "Alex Rivera"
  email: "alex@example.com"
  pages: [4, 6]

python tools/split_resumes_and_manifest.py   --input data/raw/batch-01/all_resumes.pdf   --batch-id batch-01   --guide data/raw/batch-01/guide.yaml

**Outputs**
- PDFs: data/raw/batch-01/resumes/<candidate_id>.pdf
- Manifest: data/raw/batch-01/candidate_manifest.csv
