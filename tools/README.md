# Tools Directory - Canonical Manifest Processing Workflow

## Overview

This directory contains **2 canonical tools** for processing candidate resume batches. Use this README to eliminate confusion about which tool to use.

## 🎯 Canonical Tools (Use These)

### 1. `split_resumes_and_manifest.py` - Initial Batch Split
**Purpose:** Split a multi-resume PDF into individual files and create the initial manifest

**When to use:** First step when ingesting a new batch of resumes from recruiters

**Usage:**
```bash
# With a YAML guide (recommended for production)
python tools/split_resumes_and_manifest.py \
  --input batch-05-consolidated.pdf \
  --batch-id batch-05 \
  --guide batch-05-guide.yaml

# Auto-split mode (for testing/prototyping)
python tools/split_resumes_and_manifest.py \
  --input batch-05-consolidated.pdf \
  --batch-id batch-05 \
  --auto
```

**Output:**
- `data/raw/batch-XX/resumes/*.pdf` - Individual resume PDFs
- `data/raw/batch-XX/candidate_manifest.csv` - Initial manifest with extracted names/emails

---

## 📋 Canonical Workflow (200-Candidate Batch Process)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SPLIT: Initial ingestion                                 │
│    tools/split_resumes_and_manifest.py                      │
│    ↓ Creates: resumes/*.pdf + candidate_manifest.csv        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. SCORE: Run evaluation                                    │
│    python -m src.cli score                                  │
│    ↓ Creates: results/scores.csv                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. REVIEW: Manual review and filtering                      │
│    - Review scores.csv                                      │
│    - Filter candidates as needed                            │
└─────────────────────────────────────────────────────────────┘
```

## ⚠️ Decision Tree: Which Tool Should I Use?

```
START: I have a batch of resumes to process
  ↓
  ├─ Is this a NEW batch from recruiters?
  │  └─ YES → Use split_resumes_and_manifest.py
  │
  ├─ Do I need to re-score existing resumes?
  │  └─ YES → Use: python -m src.cli score
  │
  └─ Something else?
     └─ STOP → Review this README or ask for help
```

## 🗄️ Archived Tools

The following tools have been **ARCHIVED** to `archive/tools/` and should **NOT** be used:

- ❌ `rebuild_manifests.py` - Redundant, use split tool instead
- ❌ `smart_rebuild_manifests.py` - Redundant, use split tool instead
- ❌ `enrich_manifest_names.py` - Functionality integrated into split tool
- ❌ `create_name_mapping.py` - Functionality integrated into split tool
- ❌ `extract_more_names.py` - Functionality integrated into split tool

**Why archived?** These scripts created overlapping functionality and decision fatigue. The PRD only requires split + score for the 200-candidate batch process.

## 📝 Common Tasks

### First-time batch ingestion
```bash
# Step 1: Split the batch
python tools/split_resumes_and_manifest.py \
  --input ~/Downloads/batch-06.pdf \
  --batch-id batch-06 \
  --guide batch-06-guide.yaml

# Step 2: Score the candidates
python -m src.cli score --manifest data/raw/batch-06/candidate_manifest.csv
```

### Re-score existing batch
```bash
python -m src.cli score --manifest data/raw/batch-05/candidate_manifest.csv
```

## 🔧 Requirements

Install tool dependencies:
```bash
pip install -r tools/requirements.txt
```

## 📚 Additional Documentation

- See `split_resumes_and_manifest.py --help` for detailed options
- See main project README for full workflow documentation
- Archived tool documentation available in `archive/tools/`

## ✅ Success Criteria

- ✅ Only 2 canonical tools remain in tools/
- ✅ Clear decision tree for tool selection
- ✅ No redundant/overlapping functionality
- ✅ Canonical workflow: split → score → review
- ✅ Zero confusion about which tool to use

---

**Last updated:** PR12 - Tool Script Cleanup & Documentation
**Maintainer:** See project README for contact info
