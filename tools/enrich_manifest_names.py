#!/usr/bin/env python3
import argparse, os, re, sys, glob
import pandas as pd

BAD_HEADINGS = re.compile(r'^(resume|curriculum vitae|cv|profile|portfolio)\b', re.I)
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
PHONE_RE = re.compile(r'(\+?\d{1,2}[\s\-\.]?)?(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})')

def read_first_page_text(pdf_path: str) -> str:
    try:
        import pypdf
        r = pypdf.PdfReader(pdf_path)
        if not r.pages: return ""
        return (r.pages[0].extract_text() or "").strip()
    except Exception:
        return ""

def guess_name_from_text(text: str) -> str:
    if not text: return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    top = lines[:15]
    best = ""
    for ln in top:
        if BAD_HEADINGS.search(ln): continue
        ln = EMAIL_RE.sub("", ln)
        ln = PHONE_RE.sub("", ln)
        toks = [t for t in re.split(r'[\s,]+', ln) if t]
        words = [w for w in toks if re.fullmatch(r"[A-Za-z\-']{2,}", w)]
        if not (2 <= len(words) <= 4): continue
        cap = sum(1 for w in words if w[0].isupper())
        if cap < max(2, len(words)-1): continue
        if any(w.lower() in {"senior","product","designer","ux","resume","cv","profile","portfolio"} for w in words):
            continue
        cand = " ".join(words)
        if cand and (cand.istitle() or cand.isupper()):
            return cand.title()
        if not best: best = cand.title()
    return best

def sanitize_filename(name: str) -> str:
    if not name or str(name).lower() in {"nan", "none", ""}:
        return "unnamed"
    n = str(name).lower().strip()
    n = re.sub(r"[^a-z0-9 _-]+", "", n)
    n = re.sub(r"\s+", "_", n)
    n = re.sub(r"_+", "_", n)
    return n[:80] or "unnamed"

def enrich_and_rename(manifest_path: str, rename_files: bool = False) -> dict:
    import pypdf
    df = pd.read_csv(manifest_path)
    
    # Use existing columns that match our needs
    pdf_col = "pdf_path" if "pdf_path" in df.columns else "resume_file"
    name_col = "name" if "name" in df.columns else "full_name"
    
    # Ensure name column exists
    if name_col not in df.columns: 
        df[name_col] = ""

    base = os.path.dirname(manifest_path)
    resumes_dir = os.path.join(base, "resumes")
    os.makedirs(resumes_dir, exist_ok=True)

    updated, renamed = 0, 0
    for i, row in df.iterrows():
        pdf = row.get(pdf_col, "")
        if not pdf or not os.path.exists(pdf):
            continue

        # Get existing name and clean it up
        existing_name = str(row.get(name_col, "") or "").strip()
        if existing_name.lower() in {"nan", "none", ""}:
            existing_name = ""
        
        # Clean up existing name if it has too many words or looks like job titles
        cleaned_name = ""
        if existing_name:
            words = existing_name.split()
            # Remove common job title words and keep likely name parts
            name_words = []
            for word in words:
                if word.lower() not in {"product", "designer", "ui/ux", "ux", "ui", "senior", "junior", "lead", "principal", "staff", "manager", "director", "engineer", "developer", "analyst", "specialist"}:
                    name_words.append(word)
            if 2 <= len(name_words) <= 4:
                cleaned_name = " ".join(name_words)
        
        # Use cleaned name or extract new one
        final_name = cleaned_name
        if not final_name:
            text = read_first_page_text(pdf)
            final_name = guess_name_from_text(text)
            if not final_name and isinstance(row.get("email"), str) and "@" in row["email"]:
                local = row["email"].split("@",1)[0]
                final_name = " ".join([w.capitalize() for w in re.split(r'[\W_]+', local) if w])
        
        # Update the name if we got something better
        if final_name and final_name != existing_name:
            df.at[i, name_col] = final_name
            updated += 1

        if rename_files:
            sanitized_name = sanitize_filename(df.at[i, name_col] or os.path.splitext(os.path.basename(pdf))[0])
            new_pdf = os.path.join(resumes_dir, f"{sanitized_name}.pdf")
            c, stem = 1, sanitized_name
            while os.path.exists(new_pdf) and os.path.abspath(new_pdf) != os.path.abspath(pdf):
                sanitized_name = f"{stem}_{c}"; c += 1
                new_pdf = os.path.join(resumes_dir, f"{sanitized_name}.pdf")
            if os.path.abspath(new_pdf) != os.path.abspath(pdf):
                os.replace(pdf, new_pdf)
                renamed += 1
            df.at[i, pdf_col] = os.path.relpath(new_pdf, start=".")

    out_path = re.sub(r"\.csv$", ".enriched.csv", manifest_path)
    df.to_csv(out_path, index=False)
    return {"manifest": manifest_path, "enriched": out_path, "updated_names": updated, "renamed_files": renamed, "rows": len(df)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", help="Path to one manifest CSV")
    ap.add_argument("--glob", help="Glob for many manifests, e.g. 'data/raw/batch-0*/candidate_manifest.csv'")
    ap.add_argument("--rename", action="store_true", help="Also rename PDFs to <full_name>.pdf")
    args = ap.parse_args()

    if not args.manifest and not args.glob:
        print("Provide --manifest or --glob", file=sys.stderr); sys.exit(2)

    targets = []
    if args.manifest: targets.append(args.manifest)
    if args.glob: targets += glob.glob(args.glob)
    targets = sorted(set(t for t in targets if os.path.exists(t)))

    summaries = []
    for p in targets:
        summaries.append(enrich_and_rename(p, args.rename))

    for s in summaries:
        print(f"{s['manifest']} -> {s['enriched']} | names+{s['updated_names']} | renamed+{s['renamed_files']} | rows={s['rows']}")

if __name__ == "__main__":
    main()