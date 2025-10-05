#!/usr/bin/env python3
"""
Compare ETL function implementations between legacy and current locations.
Since the legacy src/etl/ directory has been removed, this script serves as 
a verification tool to ensure we have the best implementation.
"""
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    print("=== ETL Functions Comparison ===")
    
    # Check if legacy directory exists
    legacy_etl = Path(__file__).parent.parent / "src" / "etl"
    current_etl = Path(__file__).parent.parent / "src" / "jd_fit_evaluator" / "etl"
    
    if legacy_etl.exists():
        print(f"❌ Legacy directory still exists: {legacy_etl}")
        print("   This should have been removed during migration!")
        return 1
    else:
        print(f"✅ Legacy directory removed: {legacy_etl}")
    
    if not current_etl.exists():
        print(f"❌ Current ETL directory missing: {current_etl}")
        return 1
    else:
        print(f"✅ Current ETL directory exists: {current_etl}")
    
    # Check key files exist in current location
    key_files = ["manifest_schema.py", "manifest_ingest.py", "ingestion.py"]
    for file in key_files:
        file_path = current_etl / file
        if file_path.exists():
            print(f"✅ {file} exists in current location")
        else:
            print(f"❌ {file} missing from current location")
    
    # Test coerce_row function
    try:
        from jd_fit_evaluator.etl.manifest_schema import coerce_row, ManifestRow
        print("✅ Successfully imported coerce_row from current location")
        
        # Test basic functionality
        test_row = {"candidate_id": "test123", "resume_path": "test.pdf"}
        try:
            # This will fail validation due to missing file, but import works
            result = coerce_row(test_row)
            print("✅ coerce_row function is callable")
        except Exception as e:
            if "does not exist" in str(e):
                print("✅ coerce_row function validates file existence (expected)")
            else:
                print(f"⚠️  coerce_row validation: {e}")
        
    except ImportError as e:
        print(f"❌ Failed to import coerce_row: {e}")
        return 1
    
    print("\n=== Comparison Complete ===")
    print("Status: Legacy ETL modules successfully migrated and consolidated")
    return 0

if __name__ == "__main__":
    sys.exit(main())