#!/usr/bin/env python3

import json
import sys
from pathlib import Path

# Use proper package imports instead of sys.path hack
from jd_fit_evaluator.scoring.finalize import compute_fit
from jd_fit_evaluator.parsing.stints import extract_stints

def load_sample_candidate() -> dict:
    p = Path("data/sample/candidate_example.json")
    return json.loads(p.read_text())

def load_role_from_jd(jd_path: str) -> dict:
    text = Path(jd_path).read_text()
    lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]
    titles = [l.replace("Title:", "").strip() for l in lines if l.lower().startswith("title:")]
    level = next((l.split(":")[1].strip() for l in lines if l.lower().startswith("level:")), "senior")
    industries = [s.strip() for l in lines if l.lower().startswith("industries:") for s in l.split(":")[1].split(",")]
    must = [l for l in lines if l.lower().startswith("must-have:")]
    nice = [l for l in lines if l.lower().startswith("nice-to-have:")]
    skills_blob = "\n".join(must + nice)
    role = dict(
        titles=[t.lower() for t in titles] or ["recruiter"],
        level=level.lower(),
        industries=[i.lower() for i in industries],
        jd_skills_blob=skills_blob,
        min_avg_months=18, min_last_months=12
    )
    return role

def main():
    print("Testing direct scoring without CLI...")
    
    # Check if Agoric JD file exists
    jd_path = "docs/Agoric_Senior_Product_Designer_JD.txt"
    if not Path(jd_path).exists():
        print(f"❌ JD file not found: {jd_path}")
        return
    
    # Check if sample candidate exists
    sample_path = "data/sample/candidate_example.json"
    if not Path(sample_path).exists():
        print(f"❌ Sample candidate not found: {sample_path}")
        return
    
    try:
        print("✅ Loading role from JD...")
        role = load_role_from_jd(jd_path)
        print(f"   Role: {role}")
        
        print("✅ Loading sample candidate...")
        cand = load_sample_candidate()
        print(f"   Candidate: {cand.get('name', 'unknown')}")
        
        print("✅ Computing fit score...")
        result = compute_fit(cand, role)
        print(f"   Fit Score: {result['fit']}")
        print(f"   Why: {' | '.join(result['why'])}")
        
        # Save output
        out_dir = Path("data/out")
        out_dir.mkdir(parents=True, exist_ok=True)
        
        rows = [{"candidate": cand.get("name", "unknown"), "fit": result["fit"], **result["subs"], "why": result["why"]}]
        output_file = out_dir / "scores.json"
        output_file.write_text(json.dumps(rows, indent=2))
        print(f"✅ Saved scores to {output_file}")
        
        print("🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()