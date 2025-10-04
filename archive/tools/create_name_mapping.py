#!/usr/bin/env python3
"""
TODO(PR12): ARCHIVED - This script is redundant and has been replaced.
Use split_resumes_and_manifest.py for the canonical workflow.
This file has been moved to archive/tools/ for reference only.
"""
import pandas as pd
import glob
import os
import pypdf
import re

def extract_name_better(pdf_path):
    """Better name extraction from PDF first page."""
    try:
        reader = pypdf.PdfReader(pdf_path)
        if not reader.pages: return ""
        text = (reader.pages[0].extract_text() or "").strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        
        # Strategy 1: Look for name-like patterns in first few lines
        for line in lines[:8]:
            # Clean the line but preserve word structure
            clean = re.sub(r'\b(UX|UI|Product|Designer|Engineer|Developer|Manager|Director|Senior|Junior|Lead|Principal|Staff)\b', '', line, flags=re.IGNORECASE)
            clean = re.sub(r'[^\w\s-]', ' ', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            words = [w for w in clean.split() if len(w) >= 2 and w.isalpha()]
            
            # Look for 2-3 capitalized words that look like names
            if 2 <= len(words) <= 3:
                if all(w[0].isupper() for w in words):
                    candidate = ' '.join(words)
                    # Skip if it contains common non-name words
                    if not re.search(r'\b(Skills|Experience|Contact|Information|Portfolio|Resume|CV|Profile|About|Summary|Technical|Professional)\b', candidate, re.IGNORECASE):
                        return candidate
        
        # Strategy 2: Take first line and clean it up
        if lines:
            first_line = lines[0]
            # Remove obvious non-name parts
            first_line = re.sub(r'\b(UX|UI|Product|Designer|Engineer|Developer|Manager|Director|Senior|Junior|Lead|Principal|Staff).*$', '', first_line, flags=re.IGNORECASE)
            first_line = re.sub(r'[^\w\s-]', ' ', first_line)
            words = [w for w in first_line.split() if len(w) >= 2 and w.isalpha()]
            if 2 <= len(words) <= 4:
                return ' '.join(words[:3])  # Take first 2-3 words
        
        return ""
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return ""

def create_name_mapping():
    """Create a CSV mapping of resume files to extracted names."""
    mapping_rows = []
    
    batches = sorted(glob.glob("data/raw/batch-0*"))
    for batch_dir in batches:
        resumes_dir = os.path.join(batch_dir, "resumes")
        if not os.path.exists(resumes_dir):
            continue
            
        pdfs = sorted(glob.glob(os.path.join(resumes_dir, "*.pdf")))
        print(f"Processing {len(pdfs)} PDFs in {batch_dir}")
        
        for pdf_path in pdfs:
            name = extract_name_better(pdf_path)
            if name:
                resume_file = os.path.relpath(pdf_path, start=".")
                mapping_rows.append({"resume_file": resume_file, "full_name": name})
                print(f"  {os.path.basename(pdf_path)} -> {name}")
            else:
                print(f"  {os.path.basename(pdf_path)} -> No name found")
    
    # Save the mapping
    if mapping_rows:
        df = pd.DataFrame(mapping_rows)
        df.to_csv("data/raw/name_corrections.csv", index=False)
        print(f"Created mapping file with {len(mapping_rows)} entries")
    else:
        print("No names found to create mapping")

if __name__ == "__main__":
    create_name_mapping()