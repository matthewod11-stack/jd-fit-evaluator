#!/usr/bin/env python3
"""Split a batch PDF of resumes into individual files plus a candidate manifest."""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
import yaml
from pypdf import PdfReader, PdfWriter

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")


@dataclass
class CandidateSlice:
    candidate_id: str
    pages: List[int]  # zero-based page indexes
    name: str = ""
    email: str = ""
    source: str = "auto"
    extra_emails: List[str] = field(default_factory=list)

    @property
    def human_pages(self) -> List[int]:
        return [p + 1 for p in self.pages]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a multi-resume PDF into individual PDFs and produce a candidate manifest."
    )
    parser.add_argument("--input", required=True, help="Path to the multi-resume PDF to split")
    parser.add_argument("--batch-id", required=True, help="Identifier for the batch (e.g., batch-01)")
    parser.add_argument("--guide", help="Optional YAML file containing explicit page ranges per candidate")
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Enable heuristic auto-splitting when no guide is supplied."
    )
    parser.add_argument(
        "--output-dir",
        help="Override output directory (defaults to data/raw/<batch-id>)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Threshold for auto-splitting sensitivity (0.0-1.0, lower=more sensitive)"
    )
    parser.add_argument(
        "--min-gap-pages",
        type=int,
        default=1,
        help="Minimum gap (in pages) before another start is valid"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove existing outputs for this batch before writing"
    )
    return parser.parse_args()


def ensure_batch_paths(batch_id: str, output_dir: Optional[str]) -> Path:
    if output_dir:
        batch_dir = Path(output_dir).expanduser().resolve()
    else:
        batch_dir = (Path("data/raw") / batch_id).resolve()
    resumes_dir = batch_dir / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)
    return batch_dir


def load_pdf(path: Path) -> PdfReader:
    reader = PdfReader(str(path))
    if len(reader.pages) == 0:
        raise ValueError(f"No pages found in PDF: {path}")
    return reader


def load_guide(reader: PdfReader, guide_path: Path, batch_id: str) -> List[CandidateSlice]:
    with guide_path.open("r", encoding="utf-8") as handle:
        guide_data = yaml.safe_load(handle) or {}
    if not isinstance(guide_data, dict):
        raise ValueError("Guide YAML must be a mapping of candidate_id -> details")

    slices: List[CandidateSlice] = []
    total_pages = len(reader.pages)
    for candidate_id, details in guide_data.items():
        if not isinstance(details, dict):
            raise ValueError(f"Guide entry for {candidate_id} must be a mapping")
        pages = details.get("pages")
        if not pages:
            raise ValueError(f"Guide entry for {candidate_id} missing 'pages'")
        page_indexes = normalise_pages(pages, total_pages)
        name = details.get("name", "") or ""
        email = details.get("email", "") or ""
        slices.append(
            CandidateSlice(
                candidate_id=candidate_id,
                pages=page_indexes,
                name=name,
                email=email,
                source="guide",
            )
        )
    return slices


def normalise_pages(pages: Iterable[int], total_pages: int) -> List[int]:
    if isinstance(pages, list) and len(pages) == 2 and all(isinstance(p, int) for p in pages):
        start, end = pages
        if start < 1 or end < start:
            raise ValueError(f"Invalid page range [{start}, {end}]")
        end = min(end, total_pages)
        return list(range(start - 1, end))
    indexes: List[int] = []
    for p in pages:
        if not isinstance(p, int):
            raise ValueError(f"Page values must be integers; got {p!r}")
        if p < 1 or p > total_pages:
            raise ValueError(f"Page {p} out of range (1-{total_pages})")
        indexes.append(p - 1)
    if not indexes:
        raise ValueError("Page list cannot be empty")
    return sorted(indexes)


def auto_split(reader: PdfReader, batch_id: str, threshold: float = 0.75, min_gap_pages: int = 1) -> List[CandidateSlice]:
    slices: List[CandidateSlice] = []
    current: Optional[CandidateSlice] = None
    current_email_key: Optional[str] = None

    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        emails = sorted({email.lower() for email in EMAIL_RE.findall(text)})
        email_key = ",".join(emails)
        is_new_candidate = False

        if current is None:
            is_new_candidate = True
        elif emails and email_key != current_email_key:
            is_new_candidate = True
        elif not emails and current and len(current.pages) >= max(min_gap_pages, int(3 * threshold)):
            # Heuristic: long resumes without emails likely signal a new candidate
            # Use threshold to adjust sensitivity and min_gap_pages for minimum resume length
            is_new_candidate = True

        if is_new_candidate:
            if current is not None:
                slices.append(current)
            candidate_number = len(slices) + 1
            candidate_id = f"{batch_id}-{candidate_number:04d}"
            name_guess = guess_name(text)
            email_primary = emails[0] if emails else ""
            current = CandidateSlice(
                candidate_id=candidate_id,
                pages=[page_index],
                name=name_guess,
                email=email_primary,
                extra_emails=[e for e in emails[1:]],
            )
            current_email_key = email_key or None
        else:
            current.pages.append(page_index)
            if emails and not current.email:
                current.email = emails[0]
                current.extra_emails = [e for e in emails[1:]]

    if current is not None:
        slices.append(current)

    return slices


def guess_name(text: str) -> str:
    if not text:
        return ""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that look like emails or phone numbers
        if EMAIL_RE.search(line):
            continue
        if any(char.isdigit() for char in line):
            continue
        # Truncate excessively long lines
        if len(line) > 80:
            line = line[:80].strip()
        return line
    return ""


def write_candidate_pdfs(reader: PdfReader, batch_dir: Path, slices: List[CandidateSlice]) -> List[dict]:
    manifest_rows: List[dict] = []
    resumes_dir = batch_dir / "resumes"
    resumes_dir.mkdir(parents=True, exist_ok=True)

    for slice_ in slices:
        output_path = resumes_dir / f"{slice_.candidate_id}.pdf"
        writer = PdfWriter()
        for page_index in slice_.pages:
            writer.add_page(reader.pages[page_index])
        with output_path.open("wb") as handle:
            writer.write(handle)
        print(f"[pdf] {slice_.candidate_id} -> {output_path}")

        manifest_rows.append(
            {
                "candidate_id": slice_.candidate_id,
                "name": slice_.name,
                "email": slice_.email,
                "additional_emails": ";".join(slice_.extra_emails),
                "pdf_path": str(output_path),
                "pages": ",".join(str(p) for p in slice_.human_pages),
                "source": slice_.source,
            }
        )
    return manifest_rows


def write_manifest(batch_dir: Path, rows: List[dict]) -> Path:
    manifest_path = batch_dir / "candidate_manifest.csv"
    df = pd.DataFrame(rows, columns=[
        "candidate_id",
        "name",
        "email",
        "additional_emails",
        "pdf_path",
        "pages",
        "source",
    ])
    df.to_csv(manifest_path, index=False)
    print(f"[manifest] {manifest_path}")
    return manifest_path


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input PDF not found: {input_path}")

    batch_dir = ensure_batch_paths(args.batch_id, args.output_dir)
    
    # Clean existing outputs if --force is specified
    if args.force:
        import shutil
        resumes_dir = batch_dir / "resumes"
        manifest_csv = batch_dir / "candidate_manifest.csv"
        if resumes_dir.exists():
            shutil.rmtree(resumes_dir)
        if manifest_csv.exists():
            manifest_csv.unlink()
    
    reader = load_pdf(input_path)

    slices: List[CandidateSlice]
    if args.guide:
        guide_path = Path(args.guide).expanduser().resolve()
        if not guide_path.exists():
            raise SystemExit(f"Guide file not found: {guide_path}")
        slices = load_guide(reader, guide_path, args.batch_id)
    else:
        if not args.auto:
            raise SystemExit("Auto mode must be enabled when no guide is provided (use --auto or --guide).")
        slices = auto_split(reader, args.batch_id, args.threshold, args.min_gap_pages)
        if not slices:
            raise SystemExit("Auto splitter produced no slices; please provide a guide YAML.")

    rows = write_candidate_pdfs(reader, batch_dir, slices)
    manifest_path = write_manifest(batch_dir, rows)
    print("All done. Files ready for ingest.")
    print(f"Total candidates: {len(rows)}")
    print("Manifest:", manifest_path)


if __name__ == "__main__":
    main()
