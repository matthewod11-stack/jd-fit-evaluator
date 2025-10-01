#!/usr/bin/env python3
import argparse, os, re, sys, glob, csv
import pandas as pd

BAD_HEADINGS = re.compile(r'^(resume|curriculum vitae|cv|profile|portfolio)\b', re.I)
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
PHONE_RE = re.compile(r'(\+?\d{1,2}[\s\-\.]?)?(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})')

def read_first_page_text(pdf_path: str) -> str:
    try:
        import pypdf
        r = pypdf.PdfReader(pdf_path)
        if not r.pages: 
            return ""
        return (r.pages[0].extract_text() or "").strip()
    except Exception:
        return ""

def guess_name_from_text(text: str) -> str:
    if not text: 
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    top = lines[:15]
    best = ""
    for ln in top:
        if BAD_HEADINGS.search(ln): 
            continue
        ln = EMAIL_RE.sub("", ln)
        ln = PHONE_RE.sub("", ln)
        toks = [t for t in re.split(r'[\s,]+', ln) if t]
        words = [w for w in toks if re.fullmatch(r"[A-Za-z\-']{2,}", w)]
        if not (2 <= len(words) <= 5): 
            continue
        cap = sum(1 for w in words if w[0].isupper())
        if cap < max(2, len(words)-1): 
            continue
        if any(w.lower() in {"senior","product","designer","ux","resume","cv","profile","portfolio"} for w in words):
            continue
        cand = " ".join(words)
        if cand and (cand.istitle() or cand.isupper()):
            return cand.title()
        if not best: 
            best = cand.title()
    return best

def sanitize_filename(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(r"[^a-z0-9 _-]+", "", n)
    n = re.sub(r"\s+", "_", n)
    n = re.sub(r"_+", "_", n)
    return n[:80] or "unnamed"

def load_mapping(path: str):
    if not path or not os.path.exists(path): 
        return {}
    m = {}
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rf = (row.get("resume_file") or "").strip()
            fn = (row.get("full_name") or "").strip()
            if rf and fn:
                m[rf] = fn
    return m

def ensure_manifest_for_batch(batch_dir: str):
    manifest_csv = os.path.join(batch_dir, "candidate_manifest.csv")
    resumes_dir = os.path.join(batch_dir, "resumes")
    if os.path.exists(manifest_csv): 
        return manifest_csv
    os.makedirs(resumes_dir, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(resumes_dir, "*.pdf")))
    rows = []
    for i, pdf in enumerate(pdfs, start=1):
        cid = f"{os.path.basename(batch_dir)}-{i:04d}"
        rows.append({
            "candidate_id": cid,
            "full_name": "",
            "email": "",
            "source_batch": os.path.basename(batch_dir),
            "resume_file": os.path.relpath(pdf, start="."),
            "applied_role": "",
            "applied_date": "",
            "notes": "",
        })
    pd.DataFrame(rows).to_csv(manifest_csv, index=False)
    return manifest_csv

def enrich_and_optionally_rename(manifest_path: str, mapping: dict, do_rename: bool) -> dict:
    df = pd.read_csv(manifest_path)
    if "full_name" not in df.columns: 
        df["full_name"] = ""

    resumes_dir = os.path.join(os.path.dirname(manifest_path), "resumes")
    os.makedirs(resumes_dir, exist_ok=True)

    updated, renamed = 0, 0
    for i, row in df.iterrows():
        pdf = row.get("resume_file","")
        if not pdf or not os.path.exists(pdf):
            continue

        # 1) mapping override
        map_name = mapping.get(pdf, "").strip()
        if map_name:
            df.at[i, "full_name"] = map_name

        # 2) infer if empty
        name = str(df.at[i, "full_name"] or "").strip()
        if not name:
            text = read_first_page_text(pdf)
            name = guess_name_from_text(text)
            if not name and isinstance(row.get("email"), str) and "@" in row["email"]:
                local = row["email"].split("@",1)[0]
                name = " ".join([w.capitalize() for w in re.split(r'[\W_]+', local) if w])
            if name:
                df.at[i, "full_name"] = name
                updated += 1

        # 3) rename if requested
        if do_rename:
            final_name = sanitize_filename(str(df.at[i, "full_name"] or "") or os.path.splitext(os.path.basename(pdf))[0])
            new_pdf = os.path.join(resumes_dir, f"{final_name}.pdf")
            c, stem = 1, final_name
            while os.path.exists(new_pdf) and os.path.abspath(new_pdf) != os.path.abspath(pdf):
                final_name = f"{stem}_{c}"; c += 1
                new_pdf = os.path.join(resumes_dir, f"{final_name}.pdf")
            if os.path.abspath(new_pdf) != os.path.abspath(pdf):
                os.replace(pdf, new_pdf)
                renamed += 1
            df.at[i, "resume_file"] = os.path.relpath(new_pdf, start=".")

    out_path = re.sub(r"\.csv$", ".enriched.csv", manifest_path)
    df.to_csv(out_path, index=False)
    return {"manifest": manifest_path, "enriched": out_path, "updated_names": updated, "renamed_files": renamed, "rows": len(df)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", help="Path to one manifest CSV")
    ap.add_argument("--glob", help="Glob for many manifests, e.g. 'data/raw/batch-0*/candidate_manifest.csv'")
    ap.add_argument("--rename", action="store_true", help="Rename PDFs to <full_name>.pdf")
    ap.add_argument("--mapping", help="CSV with columns: resume_file,full_name for manual corrections")
    args = ap.parse_args()

    targets = []
    if args.manifest: 
        targets.append(args.manifest)
    if args.glob: 
        targets += glob.glob(args.glob)

    ensured = []
    for t in list(targets):
        if t.endswith("candidate_manifest.csv") and os.path.exists(t):
            ensured.append(t)
        elif "batch-" in t and t.endswith("candidate_manifest.csv"):
            ensured.append(ensure_manifest_for_batch(os.path.dirname(t)))
        else:
            ensured.append(t)
    targets = sorted(set([p for p in ensured if os.path.exists(os.path.dirname(p))]))

    mapping = load_mapping(args.mapping)

    summaries = []
    for p in targets:
        if not os.path.exists(p):
            if p.endswith("candidate_manifest.csv"):
                ensured_path = ensure_manifest_for_batch(os.path.dirname(p))
                summaries.append(enrich_and_optionally_rename(ensured_path, mapping, args.rename))
            continue
        summaries.append(enrich_and_optionally_rename(p, mapping, args.rename))

    for s in summaries:
        print(f"{s['manifest']} -> {s['enriched']} | names+{s['updated_names']} | renamed+{s['renamed_files']} | rows={s['rows']}")

if __name__ == "__main__":
    main()