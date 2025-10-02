
# Product Requirements Document (PRD)

**Project:** JD-Fit Evaluator  
**Owner:** FoundryHR / Internal HR AI Tooling  
**Status:** Draft v1.0 (Living Document)  
**Last Updated:** 2025-09-29  

---

## 1. Vision & Goals

Recruiters and HR teams waste time manually reviewing resumes. We want an AI-assisted system that:

- Pulls candidates from **Greenhouse** automatically.
- Compares each applicant **against the job description (JD)**, not against each other.  
- Produces a **Fit Score (0–100)** plus a **rationale (“why”)**.  
- Uses **multi-signal evaluation** (titles, industries, tenure, skills, context).  
- Learns over time from historical **hire vs. reject** decisions.  

**Goal:** Reduce resume review workload by 70% while maintaining/raising shortlisting quality.  

---

## 2. Users & Use Cases

**Primary Users:**  

- Recruiters / Talent Acquisition  
- HR Business Partners  
- Hiring Managers (view-only)  

**Use Cases:**  

- First-pass resume screen (bulk).  
- Structured shortlisting for a JD.  
- Candidate review with evidence-based rationale.  
- Train-on-history to improve model calibration.  

---

## 3. Key Features

### Ingestion

- Connect to **Greenhouse Harvest API**.  
- Pull job applications, candidates, and attachments (resumes).  
- Parse resumes (PDF/DOCX/TXT).  
- Extract structured **stints** (title, company, start/end).  
- Map companies/industries with taxonomy.  

### Scoring Engine

- **Sub-scores (0–1):**
  - Title relevance (role/level).  
  - Industry alignment.  
  - Tenure (avg, last stint).  
  - Recency of relevant experience.  
  - Skills semantic similarity (JD vs. resume blob).  
  - Context alignment (e.g., “recruiting” as hiring vs. being recruited).  
  - Bonus flags (certs, markets, etc.).  
- **Fit Score (0–100)** = weighted blend of sub-scores.  
- **Rationale** = 3–5 bullet explanation of why the score.  

### Machine Learning

- Train Logistic Regression (later XGBoost/LoRA fine-tune).  
- Inputs: historical sub-scores + labels (advance/hire vs reject).  
- Outputs: calibrated **Prob(Advance)**.  
- Blend: `Final = α·FitScore + (1-α)·Prob(Advance)` (tunable).  

### UI (Streamlit)

- JD editor + weight sliders.  
- Candidate JSON viewer (ingested or manual).  
- Results table with scores, subs, and rationale.  
- Save/load JD profiles (weights + JD text).  
- Export scores to CSV/JSON.  

### API (FastAPI)

- POST `/score` with JD + candidate JSON → returns score & rationale.  

---

## 4. Technical Architecture

Greenhouse ETL → Resume Parsing → Stint Extractor → Taxonomy Mapping
    ↓
Candidate JSON (normalized)
    ↓
Scoring Engine (sub-scores)
    ↓
Fit Score (rule-based blend)
    ↓
[Optional Training Model → Prob(Advance)]
    ↓
Final Output (score + rationale)

**Stack:**  

- Python (Typer CLI, FastAPI API, Streamlit UI).
- Local Llama embeddings via `llama-cpp-python`.  
- Deterministic fallback embeddings (hash-based).  
- Resume parsing: pdfminer.six, python-docx.  
- ML: scikit-learn Logistic Regression.  
- Data: JSON files + CSV labels; taxonomy in `/data/taxonomy/`.  

---

## 5. Data & Taxonomy

- **Candidate JSON:** name, titles_norm, stints[{title,company,start,end,industry_tags}], skills_blob, relevant_bullets_blob.  
- **JD JSON:** extracted fields: titles, level, industries, skills_blob, min_avg_months, min_last_months.  
- **Taxonomy:** `/data/taxonomy/companies.json`, `/data/taxonomy/industries.json`.  
- **Labels:** `/data/labels.csv` → name,label (1=advance,0=reject).  

---

## 6. Compliance & Ethics

- Keep resumes local (no external API for PII).  
- Provide rationale for transparency.  
- AI = decision support only; **never auto-reject**.  
- Version weights & model checkpoints for reproducibility.  

---

## 7. Milestones

**MVP (complete):**  

- Greenhouse ingestion.  
- Resume parsing.  
- Stint extraction.  
- Industry mapping.  
- Rule-based Fit Score.  
- Streamlit with sliders.  
- CLI + API.  

**Next:**  

- Improve stint parsing accuracy (NER).  
- Expand taxonomy coverage.  
- Blend trained model outputs.  
- Save/load weight profiles in CLI as well as UI.  
- Add export to Greenhouse or ATS notes.  

**Future:**  

- UI to compare multiple candidates side-by-side.  
- Multi-JD evaluation (candidate vs. multiple roles).  
- LoRA fine-tuned Llama for richer rationale & scoring.  
- Enterprise deployment (Docker + Postgres).  

---

## 8. Open Questions

- Should training labels use `candidate_id` instead of name? (safer)  
- How to integrate seamlessly back into Greenhouse workflow?  
- How to ensure bias mitigation and fairness across sub-groups?  

---

## 9. Ownership & Workflow

- **Owner:** FoundryHR product team.  
- **Contributors:** Engineering (ML/infra), HR Ops (workflow), TA leads (feedback).  
- **Workflow:** PRD in `/docs/PRD.md` → updated with each sprint; repo is source of truth.  
