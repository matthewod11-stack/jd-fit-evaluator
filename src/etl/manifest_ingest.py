from __future__ import annotations
import csv, json
from pathlib import Path
from pydantic import ValidationError
from typing import List, Dict, Any
import logging
from .manifest_schema import ManifestRow, Manifest

logger = logging.getLogger(__name__)

class ManifestIngestionError(Exception):
    """Custom exception for manifest ingestion errors"""
    pass

def read_manifest(path: str) -> Manifest:
    """Read and validate manifest CSV file."""
    p = Path(path)
    if not p.exists():
        raise ManifestIngestionError(f"Manifest file not found: {path}")
    
    if not p.is_file():
        raise ManifestIngestionError(f"Manifest path is not a file: {path}")
    
    rows: list[ManifestRow] = []
    errors: List[str] = []
    
    try:
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Validate required headers
            required_headers = {"candidate_id", "source_path"}
            if not required_headers.issubset(reader.fieldnames or []):
                missing = required_headers - set(reader.fieldnames or [])
                raise ManifestIngestionError(f"Manifest missing required headers: {missing}")
            
            for i, row in enumerate(reader, start=2):  # header is line 1
                try:
                    rows.append(ManifestRow(**row))
                except ValidationError as e:
                    error_msg = f"Row {i}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
    
    except UnicodeDecodeError as e:
        raise ManifestIngestionError(f"Manifest file encoding error: {e}")
    except Exception as e:
        raise ManifestIngestionError(f"Error reading manifest file: {e}")
    
    if errors:
        raise ManifestIngestionError(f"Manifest validation failed:\n" + "\n".join(errors))
    
    if not rows:
        raise ManifestIngestionError("Manifest contains no valid rows")
    
    return Manifest(rows=rows)

def normalize_candidate_json(row: ManifestRow) -> dict:
    """Convert ManifestRow to normalized candidate JSON format."""
    return {
        "candidate_id": row.candidate_id,
        "name": row.name or "",
        "email": row.email or "",
        "phone": row.phone or "",
        "resume_path": row.source_path,
        "notes": row.notes or "",
        "metadata": {
            "ingestion_timestamp": None,  # Could be added by ingestion process
            "source_manifest": True
        }
    }

def ingest_manifest_rows(manifest_csv: str, out_dir: str) -> Dict[str, Any]:
    """Ingest manifest CSV and produce normalized candidates.jsonl."""
    manifest = read_manifest(manifest_csv)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    out_jsonl = out / "candidates.jsonl"
    out_metadata = out / "ingestion_metadata.json"
    
    # Write candidates
    candidates_written = 0
    with out_jsonl.open("w", encoding="utf-8") as w:
        for row in manifest.rows:
            obj = normalize_candidate_json(row)
            w.write(json.dumps(obj, ensure_ascii=False) + "\n")
            candidates_written += 1
    
    # Write metadata
    metadata = {
        "ingestion_timestamp": None,  # Could use datetime.now().isoformat()
        "source_manifest": manifest_csv,
        "candidates_processed": candidates_written,
        "schema_version": "1.0"
    }
    
    with out_metadata.open("w", encoding="utf-8") as w:
        json.dump(metadata, w, indent=2, ensure_ascii=False)
    
    logger.info(f"Ingested {candidates_written} candidates from {manifest_csv}")
    
    return {
        "candidates_written": candidates_written,
        "output_file": str(out_jsonl),
        "metadata_file": str(out_metadata)
    }