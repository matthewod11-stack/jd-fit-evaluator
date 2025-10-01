#!/usr/bin/env python3
import pandas as pd
import glob
import os

def smart_rebuild_manifests():
    """Rebuild manifests while preserving existing renamed files."""
    
    batches = sorted(glob.glob("data/raw/batch-0*"))
    for batch_dir in batches:
        manifest_path = os.path.join(batch_dir, "candidate_manifest.csv")
        resumes_dir = os.path.join(batch_dir, "resumes")
        
        if not os.path.exists(resumes_dir):
            continue
        
        # Get all PDF files (both renamed and nan_*.pdf)
        all_pdfs = sorted(glob.glob(os.path.join(resumes_dir, "*.pdf")))
        if not all_pdfs:
            continue
        
        batch_name = os.path.basename(batch_dir)
        rows = []
        
        for i, pdf_path in enumerate(all_pdfs, start=1):
            candidate_id = f"{batch_name}-{i:04d}"
            resume_file = os.path.relpath(pdf_path, start=".")
            
            # Try to extract name from filename if it's not a nan_ file
            full_name = ""
            filename = os.path.basename(pdf_path)
            if not filename.startswith('nan'):
                # Extract name from filename (convert underscores to spaces, title case)
                name_part = os.path.splitext(filename)[0]
                full_name = ' '.join(word.capitalize() for word in name_part.split('_'))
            
            rows.append({
                "candidate_id": candidate_id,
                "full_name": full_name,
                "email": "",
                "source_batch": batch_name,
                "resume_file": resume_file,
                "applied_role": "",
                "applied_date": "",
                "notes": "",
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(manifest_path, index=False)
        named_count = len(df[df['full_name'] != ''])
        print(f"Rebuilt {manifest_path} with {len(df)} entries ({named_count} already have names)")

if __name__ == "__main__":
    smart_rebuild_manifests()