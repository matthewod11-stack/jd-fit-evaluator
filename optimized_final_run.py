#!/usr/bin/env python3
"""
🚀 JD-Fit Final Candidate Run - Optimized for 170+ Candidates
Optimized version with parallel processing, progress monitoring, and error handling.
"""

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
import sys
import os

# Load .env file before importing config
from dotenv import load_dotenv
load_dotenv()  # This loads .env from the current directory

from jd_fit_evaluator.config import cfg
from jd_fit_evaluator.logging import init_logging
from jd_fit_evaluator.utils.schema import CanonicalScore, write_scores
from jd_fit_evaluator.scoring.finalize import score_candidates, _load_role

console = Console()
app = typer.Typer(no_args_is_help=True, add_completion=False)

class OptimizedScorer:
    """Optimized scorer with parallel processing and progress monitoring."""
    
    def __init__(self, 
                 manifest_path: str,
                 job_path: str,
                 max_workers: int = 8,
                 batch_size: int = 32,
                 explain: bool = True):
        self.manifest_path = Path(manifest_path)
        self.job_path = Path(job_path)
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.explain = explain
        self.logger = logging.getLogger(__name__)
        
        # Load role definition
        self.role_dict = _load_role(str(self.job_path))
        
        # Results tracking
        self.results = []
        self.errors = []
        self.stats = {
            "total_candidates": 0,
            "processed": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def load_candidates_from_manifest(self) -> List[Dict[str, Any]]:
        """Load candidates from manifest file."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")
        
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        
        candidates = []
        for item in manifest.get('candidates', []):
            candidate_path = Path(item['path'])
            if candidate_path.exists():
                with open(candidate_path, 'r') as f:
                    parsed = json.load(f)
                    candidates.append({
                        "path": str(candidate_path),
                        "parsed": parsed
                    })
            else:
                self.logger.warning(f"Candidate file not found: {candidate_path}")
        
        self.stats["total_candidates"] = len(candidates)
        return candidates
    
    def score_candidate_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score a batch of candidates. Returns a dict with success and flat results list."""
        try:
            # Score the batch - score_candidates now returns a flat list of CanonicalResult
            batch_results = score_candidates(batch, self.role_dict, self.explain, wrap_artifact=False)
            return [{"success": True, "results": batch_results}]
        except Exception as e:
            self.logger.error(f"Batch scoring failed: {e}")
            return [{"success": False, "error": str(e), "batch": batch}]
    
    def process_candidates_parallel(self, candidates: List[Dict[str, Any]]) -> List[CanonicalScore]:
        """Process candidates in parallel batches."""
        # Create batches
        batches = []
        for i in range(0, len(candidates), self.batch_size):
            batch = candidates[i:i + self.batch_size]
            batches.append(batch)
        
        console.print(f"Processing {len(candidates)} candidates in {len(batches)} batches with {self.max_workers} workers")
        
        all_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("Scoring candidates...", total=len(batches))
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all batches
                future_to_batch = {
                    executor.submit(self.score_candidate_batch, batch): i 
                    for i, batch in enumerate(batches)
                }
                
                # Process completed batches
                for future in as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        batch_results = future.result()
                        for result in batch_results:
                            if result["success"]:
                                # result["results"] is already a flat list of CanonicalResult
                                all_results.extend(result["results"])
                                self.stats["processed"] += len(result["results"])
                            else:
                                self.errors.append(result)
                                self.stats["errors"] += 1
                                
                    except Exception as e:
                        self.logger.error(f"Future failed for batch {batch_idx}: {e}")
                        self.stats["errors"] += 1
                    
                    progress.update(task, advance=1)
        
        return all_results
    
    def create_progress_report(self) -> Table:
        """Create a detailed progress report (returns a rich Table)."""
        duration = self.stats["end_time"] - self.stats["start_time"] if self.stats["end_time"] else 0
        
        table = Table(title="Final Run Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Candidates", str(self.stats["total_candidates"]))
        table.add_row("Successfully Processed", str(self.stats["processed"]))
        table.add_row("Errors", str(self.stats["errors"]))
        table.add_row("Success Rate", f"{(self.stats['processed']/max(1, self.stats['total_candidates'])*100):.1f}%")
        table.add_row("Duration", f"{duration:.1f} seconds")
        table.add_row("Rate", f"{self.stats['processed']/max(1, duration):.1f} candidates/sec")
        
        return table
    
    def run(self) -> List[CanonicalScore]:
        """Run the optimized scoring process."""
        self.stats["start_time"] = time.time()
        
        try:
            # Load candidates
            console.print("📂 Loading candidates from manifest...")
            candidates = self.load_candidates_from_manifest()
            console.print(f"✅ Loaded {len(candidates)} candidates")
            
            # Process candidates in parallel
            console.print("🚀 Starting parallel scoring...")
            results = self.process_candidates_parallel(candidates)
            
            self.stats["end_time"] = time.time()
            
            # Display results
            console.print("\n" + "="*60)
            console.print(self.create_progress_report())
            
            if self.errors:
                console.print(f"\n⚠️  {len(self.errors)} errors occurred during processing")
                for error in self.errors[:5]:  # Show first 5 errors
                    console.print(f"Error: {error.get('error', 'Unknown error')}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Scoring process failed: {e}")
            raise


@app.command()
def run_optimized(
    manifest_path: str = typer.Argument(..., help="Path to manifest.json"),
    job_path: str = typer.Argument(..., help="Path to job profile JSON"),
    max_workers: int = typer.Option(8, "--workers", "-w", help="Number of parallel workers"),
    batch_size: int = typer.Option(32, "--batch-size", "-b", help="Candidates per batch"),
    out_dir: Path = typer.Option("out", "--out", "-o", help="Output directory"),
    explain: bool = typer.Option(True, "--explain", help="Include detailed explanations"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level")
):
    """
    Run optimized scoring for 170+ candidates with parallel processing.

    Example:
        python optimized_final_run.py run-optimized data/manifest.json data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json
    """

    # Initialize logging
    init_logging(log_level)

    console.print(Panel.fit(
        "🚀 JD-Fit Final Candidate Run - Optimized\n"
        f"Manifest: {manifest_path}\n"
        f"Job Profile: {job_path}\n"
        f"Workers: {max_workers} | Batch Size: {batch_size}",
        title="Configuration",
        border_style="green"
    ))

    try:
        # Create scorer
        scorer = OptimizedScorer(
            manifest_path=manifest_path,
            job_path=job_path,
            max_workers=max_workers,
            batch_size=batch_size,
            explain=explain
        )

        # Run scoring
        results = scorer.run()

        # Write results
        console.print("\n💾 Writing results...")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        write_scores(results, out_dir)

        console.print(f"✅ Results written to {out_dir}")
        console.print(f"📊 Files created:")
        console.print(f"   - {out_dir}/scores.json")
        console.print(f"   - {out_dir}/scores.csv")
        console.print(f"   - {out_dir}/batch_summary.md")

        # Final summary
        console.print(Panel.fit(
            f"🎉 Final run completed successfully!\n"
            f"Processed {scorer.stats['processed']} candidates\n"
            f"Output: {out_dir}",
            title="Success",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def run_from_folder(
    candidates_folder: str = typer.Argument(..., help="Path to folder with parsed candidate JSON files"),
    job_path: str = typer.Argument(..., help="Path to job profile JSON"),
    max_workers: int = typer.Option(8, "--workers", "-w", help="Number of parallel workers"),
    batch_size: int = typer.Option(32, "--batch-size", "-b", help="Candidates per batch"),
    out_dir: Path = typer.Option("out", "--out", "-o", help="Output directory"),
    explain: bool = typer.Option(True, "--explain", help="Include detailed explanations"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level")
):
    """
    Run optimized scoring directly from a folder of parsed candidates (no manifest needed).

    Example:
        python optimized_final_run.py run-from-folder data/candidates data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json
    """

    # Initialize logging
    init_logging(log_level)

    console.print(Panel.fit(
        "🚀 JD-Fit Final Candidate Run - Optimized (Direct Folder)\n"
        f"Candidates Folder: {candidates_folder}\n"
        f"Job Profile: {job_path}\n"
        f"Workers: {max_workers} | Batch Size: {batch_size}",
        title="Configuration",
        border_style="green"
    ))

    try:
        # Create temporary manifest
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            temp_manifest = tmp.name

        # Generate manifest from folder
        console.print(f"📂 Scanning candidates folder...")
        candidates_path = Path(candidates_folder).expanduser().resolve()
        if not candidates_path.exists():
            console.print(f"❌ Candidates folder not found: {candidates_path}", style="red")
            raise typer.Exit(1)

        json_files = list(candidates_path.glob("*.json"))
        if not json_files:
            console.print(f"❌ No JSON files found in {candidates_path}", style="red")
            raise typer.Exit(1)

        manifest = {
            "version": "1.0",
            "source": str(candidates_path),
            "total_candidates": len(json_files),
            "candidates": [
                {"candidate_id": f.stem, "path": str(f.absolute())}
                for f in sorted(json_files)
            ]
        }

        with open(temp_manifest, 'w') as f:
            json.dump(manifest, f)

        console.print(f"✅ Found {len(json_files)} candidates")

        # Create scorer
        scorer = OptimizedScorer(
            manifest_path=temp_manifest,
            job_path=job_path,
            max_workers=max_workers,
            batch_size=batch_size,
            explain=explain
        )

        # Run scoring
        results = scorer.run()

        # Clean up temp manifest
        Path(temp_manifest).unlink()

        # Write results
        console.print("\n💾 Writing results...")
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        write_scores(results, out_dir)

        console.print(f"✅ Results written to {out_dir}")
        console.print(f"📊 Files created:")
        console.print(f"   - {out_dir}/scores.json")
        console.print(f"   - {out_dir}/scores.csv")
        console.print(f"   - {out_dir}/batch_summary.md")

        # Final summary
        console.print(Panel.fit(
            f"🎉 Final run completed successfully!\n"
            f"Processed {scorer.stats['processed']} candidates\n"
            f"Output: {out_dir}",
            title="Success",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def create_manifest(
    candidates_folder: str = typer.Argument(..., help="Path to folder with parsed candidate JSON files"),
    manifest_path: str = typer.Option("data/manifest.json", "--manifest", "-m", help="Path to manifest file")
):
    """Create manifest from parsed candidate JSON files."""
    console.print(f"📂 Creating manifest from {candidates_folder}")

    candidates_path = Path(candidates_folder).expanduser().resolve()
    if not candidates_path.exists():
        console.print(f"❌ Candidates folder not found: {candidates_path}", style="red")
        raise typer.Exit(1)

    # Find all JSON files in the candidates folder
    json_files = list(candidates_path.glob("*.json"))

    if not json_files:
        console.print(f"❌ No JSON files found in {candidates_path}", style="red")
        raise typer.Exit(1)

    console.print(f"Found {len(json_files)} candidate JSON files")

    # Create manifest structure
    manifest = {
        "version": "1.0",
        "source": str(candidates_path),
        "total_candidates": len(json_files),
        "candidates": []
    }

    # Add each candidate to manifest
    for json_file in sorted(json_files):
        manifest["candidates"].append({
            "candidate_id": json_file.stem,
            "path": str(json_file.absolute())
        })

    # Write manifest
    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)

    with manifest_file.open("w") as f:
        json.dump(manifest, f, indent=2)

    console.print(f"✅ Manifest created: {manifest_path}")
    console.print(f"📊 Total candidates: {len(json_files)}")


@app.command()
def parse_candidates(
    input_folder: str = typer.Argument(..., help="Path to folder with candidate PDFs"),
    output_folder: str = typer.Option("data/candidates", "--output", "-o", help="Output folder for parsed JSON files"),
    use_llm: bool = typer.Option(False, "--use-llm", help="Use LLM for parsing (slower but more accurate)"),
):
    """
    Parse candidate PDFs to JSON format for scoring.

    Example:
        python optimized_final_run.py parse-candidates ~/Desktop/Candidates
    """
    from jd_fit_evaluator.cli import parse as cli_parse

    console.print(Panel.fit(
        f"📂 Parsing Candidate PDFs\n"
        f"Input: {input_folder}\n"
        f"Output: {output_folder}\n"
        f"Mode: {'LLM-based' if use_llm else 'Rule-based'}",
        title="Parse Configuration",
        border_style="blue"
    ))

    input_path = Path(input_folder).expanduser().resolve()
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        console.print(f"❌ Input folder not found: {input_path}", style="red")
        raise typer.Exit(1)

    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        console.print(f"❌ No PDF files found in {input_path}", style="red")
        raise typer.Exit(1)

    console.print(f"Found {len(pdf_files)} PDF files to parse")

    # Call the CLI parse function
    try:
        cli_parse(
            input_dir=str(input_path),
            out_dir=output_path,
            use_llm=use_llm
        )

        # Count parsed files
        parsed_count = len(list(output_path.glob("*.json")))
        console.print(Panel.fit(
            f"✅ Successfully parsed {parsed_count} candidates\n"
            f"Output: {output_folder}",
            title="Parse Complete",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"❌ Parsing failed: {e}", style="red")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


@app.command()
def health_check():
    """Perform health check before final run."""
    console.print("🔍 Performing health check...")

    # Check environment
    console.print("Checking environment...")
    if os.getenv("OPENAI_API_KEY"):
        console.print("✅ OpenAI API key found")
    else:
        console.print("⚠️  OpenAI API key not found - using mock embeddings")

    # Check dependencies
    console.print("Checking dependencies...")
    try:
        import openai
        console.print("✅ OpenAI package available")
    except ImportError:
        console.print("⚠️  OpenAI package not installed")

    # Check cache
    cache_path = Path(".cache/embeddings.db")
    if cache_path.exists():
        console.print(f"✅ Embedding cache found ({cache_path.stat().st_size / 1024 / 1024:.1f} MB)")
    else:
        console.print("ℹ️  No embedding cache found - will create during run")

    # Check raw candidates folder
    candidates_path = Path("~/Desktop/Candidates").expanduser()
    if candidates_path.exists():
        count = len(list(candidates_path.glob("*.pdf")))
        console.print(f"✅ Raw candidates folder found ({count} PDFs)")
    else:
        console.print("⚠️  Raw candidates folder not found")

    # Check parsed candidates
    parsed_path = Path("data/candidates")
    if parsed_path.exists():
        parsed_count = len(list(parsed_path.glob("*.json")))
        if parsed_count > 0:
            console.print(f"✅ Parsed candidates found ({parsed_count} JSON files)")
        else:
            console.print("⚠️  No parsed candidates - run parse-candidates first")
    else:
        console.print("⚠️  Parsed candidates folder not found")

    console.print("\n🎯 Health check complete!")


if __name__ == "__main__":
    app()
