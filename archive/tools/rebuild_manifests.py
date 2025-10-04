#!/usr/bin/env python3
"""
TODO(PR12): ARCHIVED - This script is redundant and has been replaced.
Use split_resumes_and_manifest.py for the canonical workflow.
This file has been moved to archive/tools/ for reference only.
"""
import pandas as pd
import glob
import os

def rebuild_manifest_for_batch(batch_dir):
    """Rebuild a manifest CSV file from the actual PDFs in the resumes directory."""
    manifest_path = os.path.join(batch_dir, "candidate_manifest.csv")
    resumes_dir = os.path.join(batch_dir, "resumes")
    
    if not os.path.exists(resumes_dir):
        print(f"No resumes directory found at {resumes_dir}")
        return
    
    # Get all PDFs
    pdfs = sorted(glob.glob(os.path.join(resumes_dir, "*.pdf")))
    if not pdfs:
        print(f"No PDFs found in {resumes_dir}")
        return
    
    rows = []
    batch_name = os.path.basename(batch_dir)
    
    for i, pdf_path in enumerate(pdfs, start=1):
        candidate_id = f"{batch_name}-{i:04d}"
        resume_file = os.path.relpath(pdf_path, start=".")
        
        rows.append({
            "candidate_id": candidate_id,
            "full_name": "",
            "email": "",
            "source_batch": batch_name,
            "resume_file": resume_file,
            "applied_role": "",
            "applied_date": "",
            "notes": "",
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(manifest_path, index=False)
    print(f"Rebuilt {manifest_path} with {len(df)} entries")
    return manifest_path

def main():
    batches = sorted(glob.glob("data/raw/batch-0*"))
    for batch in batches:
        if os.path.isdir(batch):
            rebuild_manifest_for_batch(batch)

if __name__ == "__main__":
    main()