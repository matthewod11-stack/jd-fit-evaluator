from collections.abc import Mapping
from typing import Any, Optional

from pydantic import BaseModel


class ManifestRow(BaseModel):
    candidate_id: str
    resume_path: str
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None


_CANDIDATE_ID_KEYS = ("candidate_id", "candidateId", "candidateID", "id")
_RESUME_PATH_KEYS = (
    "resume_path",
    "resume_file",
    "pdf_path",
    "resume",
    "resumeFile",
    "resume_filepath",
    "resumeFilePath",
)
_OPTIONAL_FIELD_KEYS: dict[str, tuple[str, ...]] = {
    "email": ("email", "primary_email", "candidate_email", "email_address"),
    "phone": ("phone", "phone_number", "mobile", "mobile_phone", "contact_phone"),
    "notes": ("notes", "note", "comment", "comments"),
}


def coerce_row(raw: dict) -> ManifestRow:
    if not isinstance(raw, Mapping):
        raise TypeError("manifest row must be a mapping")

    def _normalized(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
        else:
            stripped = str(value).strip()
        return stripped or None

    def _extract_required(keys: tuple[str, ...]) -> str:
        for key in keys:
            if key in raw:
                candidate = _normalized(raw[key])
                if candidate:
                    return candidate
        raise ValueError(f"missing required field: {keys[0]}")

    data: dict[str, Any] = {
        "candidate_id": _extract_required(_CANDIDATE_ID_KEYS),
        "resume_path": _extract_required(_RESUME_PATH_KEYS),
    }

    for field, keys in _OPTIONAL_FIELD_KEYS.items():
        for key in keys:
            if key in raw:
                value = _normalized(raw[key])
                if value is not None:
                    data[field] = value
                break

    return ManifestRow(**data)
