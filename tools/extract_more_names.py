#!/usr/bin/env python3
import pandas as pd
import glob
import os
import pypdf
import re

def extract_name_aggressive(pdf_path):
    """More aggressive name extraction from PDF first page."""
    try:
        reader = pypdf.PdfReader(pdf_path)
        if not reader.pages: return ""
        text = (reader.pages[0].extract_text() or "").strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        
        # Strategy 1: Look for patterns that look like names in first 12 lines
        for line in lines[:12]:
            # Skip lines that are clearly headers or sections
            if re.search(r'\b(resume|curriculum|vitae|cv|profile|portfolio|contact|information|experience|education|skills|summary|about|objective|professional|technical)\b', line, re.IGNORECASE):
                continue
            
            # Clean the line and look for name patterns
            clean = re.sub(r'\b(UX|UI|Product|Designer|Engineer|Developer|Manager|Director|Senior|Junior|Lead|Principal|Staff|Specialist|Analyst|Architect|Consultant|Coordinator)\b', '', line, flags=re.IGNORECASE)
            clean = re.sub(r'[^\w\s-]', ' ', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            
            # Look for 2-4 consecutive capitalized words
            words = clean.split()
            name_words = []
            
            for word in words:
                if len(word) >= 2 and word.isalpha() and word[0].isupper():
                    # Skip common non-name words
                    if word.lower() not in {'phone', 'email', 'linkedin', 'portfolio', 'website', 'address', 'location', 'city', 'state', 'country', 'zip', 'code', 'mobile', 'work', 'home', 'personal', 'professional', 'contact', 'information', 'profile', 'summary', 'objective', 'skills', 'experience', 'education', 'projects', 'certifications', 'languages', 'interests', 'hobbies', 'references', 'available', 'immediately', 'remote', 'relocation', 'willing', 'travel'}:
                        name_words.append(word)
                else:
                    break  # Stop at first non-name word
            
            if 2 <= len(name_words) <= 4:
                candidate = ' '.join(name_words)
                # Final validation - doesn't contain obvious non-name patterns
                if not re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{4}|Present|Current|Years?|Months?|Experience|Skills|Available|Remote|Freelance)\b', candidate, re.IGNORECASE):
                    return candidate
        
        # Strategy 2: Look for email addresses and extract name from local part
        email_match = re.search(r'([a-zA-Z0-9._%+-]+)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        if email_match:
            local_part = email_match.group(1)
            # Clean up the local part to make a name
            name_parts = re.split(r'[._+-]', local_part)
            name_words = [part.capitalize() for part in name_parts if len(part) >= 2 and part.isalpha()]
            if 2 <= len(name_words) <= 3:
                return ' '.join(name_words)
        
        # Strategy 3: Look at the very first non-empty line and be more permissive
        if lines:
            first_line = lines[0]
            # Remove job titles but keep names
            first_line = re.sub(r'\b(UX|UI|Product|Designer|Engineer|Developer|Manager|Director|Senior|Junior|Lead|Principal|Staff).*$', '', first_line, flags=re.IGNORECASE)
            
            # Extract first few words that could be names
            words = re.findall(r'\b[A-Z][a-z]+\b', first_line)
            if 2 <= len(words) <= 4:
                candidate = ' '.join(words[:3])
                # Basic validation
                if not re.search(r'\b(Resume|Portfolio|Profile|Contact|Skills|Experience|Education)\b', candidate, re.IGNORECASE):
                    return candidate
        
        return ""
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return ""

def create_additional_mappings():
    """Create additional name mappings for files still named nan_*.pdf"""
    # Load existing mapping to avoid duplicates
    existing_mapping = {}
    if os.path.exists("data/raw/name_corrections.csv"):
        existing_df = pd.read_csv("data/raw/name_corrections.csv")
        existing_mapping = dict(zip(existing_df['resume_file'], existing_df['full_name']))
    
    new_mappings = []
    
    # Process each batch
    batches = sorted(glob.glob("data/raw/batch-0*"))
    for batch_dir in batches:
        resumes_dir = os.path.join(batch_dir, "resumes")
        if not os.path.exists(resumes_dir):
            continue
        
        # Only process nan_*.pdf files
        nan_pdfs = sorted(glob.glob(os.path.join(resumes_dir, "nan*.pdf")))
        if not nan_pdfs:
            continue
            
        print(f"Processing {len(nan_pdfs)} unnamed PDFs in {batch_dir}")
        
        for pdf_path in nan_pdfs:
            resume_file = os.path.relpath(pdf_path, start=".")
            
            # Skip if already in existing mapping
            if resume_file in existing_mapping:
                continue
            
            name = extract_name_aggressive(pdf_path)
            if name:
                new_mappings.append({"resume_file": resume_file, "full_name": name})
                print(f"  {os.path.basename(pdf_path)} -> {name}")
            else:
                print(f"  {os.path.basename(pdf_path)} -> No name found")
    
    if new_mappings:
        # Combine with existing mappings
        all_mappings = list(existing_mapping.items()) + [(m['resume_file'], m['full_name']) for m in new_mappings]
        df = pd.DataFrame(all_mappings, columns=['resume_file', 'full_name'])
        
        # Remove duplicates and save
        df = df.drop_duplicates(subset=['resume_file']).reset_index(drop=True)
        df.to_csv("data/raw/name_corrections.csv", index=False)
        print(f"\\nUpdated mapping file with {len(new_mappings)} new entries (total: {len(df)})")
    else:
        print("\\nNo new names found")

if __name__ == "__main__":
    create_additional_mappings()