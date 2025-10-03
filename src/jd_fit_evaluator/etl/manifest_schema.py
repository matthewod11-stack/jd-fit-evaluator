from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
from pathlib import Path
import re

class ManifestRow(BaseModel):
    candidate_id: str = Field(..., description="Stable ID (e.g., slug or GH ID)", min_length=1)
    name: Optional[str] = Field(None, description="Full name if available")
    source_path: str = Field(..., description="Path to resume file (pdf/docx/txt)")
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    phone: Optional[str] = Field(None, description="Phone number")
    notes: Optional[str] = None

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("candidate_id must be a non-empty string")
        # Ensure it's a valid identifier (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("candidate_id must contain only alphanumeric characters, hyphens, and underscores")
        return v.strip()

    @field_validator("source_path")
    @classmethod
    def validate_source_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_path must be a non-empty path to a resume file")
        
        path = Path(v.strip())
        
        # Check if file exists
        if not path.exists():
            raise ValueError(f"source_path file does not exist: {path}")
        
        # Check if it's a file (not directory)
        if not path.is_file():
            raise ValueError(f"source_path must be a file, not a directory: {path}")
        
        # Check file extension
        valid_extensions = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(f"source_path must have a valid resume extension {valid_extensions}, got: {path.suffix}")
        
        # Check if file is readable
        try:
            with path.open('rb') as f:
                f.read(1)  # Try to read first byte
        except (PermissionError, OSError) as e:
            raise ValueError(f"source_path file is not readable: {path} - {e}")
        
        return str(path.resolve())  # Return absolute path

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        
        # Basic phone validation (digits, spaces, hyphens, parentheses, plus)
        cleaned = re.sub(r'[^\d+\-\(\)\s]', '', v)
        if len(re.sub(r'[^\d]', '', cleaned)) < 10:
            raise ValueError("phone must contain at least 10 digits")
        
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        
        # Basic name validation (letters, numbers, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z0-9\s\-']+$", v.strip()):
            raise ValueError("name must contain only letters, numbers, spaces, hyphens, and apostrophes")
        
        return v.strip()

class Manifest(BaseModel):
    rows: list[ManifestRow]
    
    @field_validator("rows")
    @classmethod
    def validate_unique_candidate_ids(cls, v: list[ManifestRow]) -> list[ManifestRow]:
        candidate_ids = [row.candidate_id for row in v]
        if len(candidate_ids) != len(set(candidate_ids)):
            duplicates = [cid for cid in candidate_ids if candidate_ids.count(cid) > 1]
            raise ValueError(f"Duplicate candidate_ids found: {set(duplicates)}")
        return v