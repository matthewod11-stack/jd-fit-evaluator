"""Shared UI table/export schema."""

from __future__ import annotations

TABLE_COLUMNS: tuple[str, ...] = (
    "candidate",
    "fit",
    "title",
    "industry",
    "skills",
    "context",
    "tenure",
    "recency",
    "bonus",
)

EXPORT_COLUMNS: tuple[str, ...] = TABLE_COLUMNS

SUB_COLUMNS: tuple[str, ...] = tuple(c for c in TABLE_COLUMNS if c not in {"candidate", "fit"})
