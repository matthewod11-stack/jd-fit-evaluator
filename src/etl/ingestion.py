from __future__ import annotations

from typing import Any, Iterable, Tuple

from .manifest_schema import coerce_row


def ingest_manifest_rows(rows: Iterable[dict[str, Any]]) -> Tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Coerce manifest rows, keeping track of successes and validation errors."""
    processed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for raw in rows:
        try:
            row = coerce_row(raw)
        except Exception as exc:  # noqa: BLE001 - propagate reason to reporting seam
            skipped.append({"row": raw, "reason": str(exc)})
        else:
            processed.append(row.model_dump())
    return processed, skipped
