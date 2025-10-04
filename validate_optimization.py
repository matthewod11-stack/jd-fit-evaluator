#!/usr/bin/env python3
"""
🔍 Validation script for optimized final run
Validates that all optimizations are working correctly.
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
app = typer.Typer()

def validate_environment() -> Dict[str, Any]:
    """Validate environment setup."""
    results = {}
    
    # Check Python version
    results["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Check required packages
    required_packages = ["openai", "rich", "typer", "numpy", "pandas"]
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    results["missing_packages"] = missing_packages
    results["all_packages_available"] = len(missing_packages) == 0
    
    # Check environment variables
    import os
    results["openai_api_key_set"] = bool(os.getenv("OPENAI_API_KEY"))
    results["embedding_provider"] = os.getenv("JD_FIT_EMBEDDINGS__PROVIDER", "mock")
    
    return results

def validate_files() -> Dict[str, Any]:
    """Validate required files exist."""
    results = {}
    
    files_to_check = [
        "optimized_final_run.py",
        "setup_final_run.sh", 
        "optimized_config.env",
        "data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json",
        "Makefile"
    ]
    
    missing_files = []
    for file_path in files_to_check:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    results["missing_files"] = missing_files
    results["all_files_present"] = len(missing_files) == 0
    
    # Check candidates folder
    candidates_path = Path.home() / "Desktop" / "Candidates"
    results["candidates_folder_exists"] = candidates_path.exists()
    
    if candidates_path.exists():
        pdf_count = len(list(candidates_path.glob("*.pdf")))
        results["candidate_count"] = pdf_count
    else:
        results["candidate_count"] = 0
    
    # Check manifest
    manifest_path = Path("data/manifest.json")
    results["manifest_exists"] = manifest_path.exists()
    
    return results

def validate_performance() -> Dict[str, Any]:
    """Validate performance optimizations."""
    results = {}
    
    # Check cache
    cache_path = Path(".cache/embeddings.db")
    results["cache_exists"] = cache_path.exists()
    
    if cache_path.exists():
        cache_size = cache_path.stat().st_size / (1024 * 1024)  # MB
        results["cache_size_mb"] = round(cache_size, 2)
    else:
        results["cache_size_mb"] = 0
    
    # Check if optimized script is importable
    try:
        sys.path.insert(0, ".")
        import optimized_final_run
        results["optimized_script_importable"] = True
    except Exception as e:
        results["optimized_script_importable"] = False
        results["import_error"] = str(e)
    
    return results

@app.command()
def validate():
    """Run comprehensive validation of optimized setup."""
    
    console.print(Panel.fit(
        "🔍 JD-Fit Optimization Validation",
        title="Validation",
        border_style="blue"
    ))
    
    # Run validations
    env_results = validate_environment()
    file_results = validate_files()
    perf_results = validate_performance()
    
    # Create summary table
    table = Table(title="Validation Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    # Environment validation
    if env_results["all_packages_available"]:
        table.add_row("Python Environment", "✅ PASS", f"Python {env_results['python_version']}")
    else:
        table.add_row("Python Environment", "❌ FAIL", f"Missing: {', '.join(env_results['missing_packages'])}")
    
    # API Key
    if env_results["openai_api_key_set"]:
        table.add_row("OpenAI API Key", "✅ PASS", "API key configured")
    else:
        table.add_row("OpenAI API Key", "⚠️ WARN", "Using mock embeddings")
    
    # Files
    if file_results["all_files_present"]:
        table.add_row("Required Files", "✅ PASS", "All files present")
    else:
        table.add_row("Required Files", "❌ FAIL", f"Missing: {', '.join(file_results['missing_files'])}")
    
    # Candidates
    if file_results["candidates_folder_exists"]:
        table.add_row("Candidates", "✅ PASS", f"{file_results['candidate_count']} PDFs found")
    else:
        table.add_row("Candidates", "❌ FAIL", "Candidates folder not found")
    
    # Manifest
    if file_results["manifest_exists"]:
        table.add_row("Manifest", "✅ PASS", "Manifest file exists")
    else:
        table.add_row("Manifest", "⚠️ WARN", "Will be created during run")
    
    # Performance
    if perf_results["optimized_script_importable"]:
        table.add_row("Optimized Script", "✅ PASS", "Script importable")
    else:
        table.add_row("Optimized Script", "❌ FAIL", perf_results.get("import_error", "Unknown error"))
    
    # Cache
    if perf_results["cache_exists"]:
        table.add_row("Embedding Cache", "✅ PASS", f"{perf_results['cache_size_mb']} MB")
    else:
        table.add_row("Embedding Cache", "ℹ️ INFO", "Will be created during run")
    
    console.print(table)
    
    # Overall status
    all_passed = (
        env_results["all_packages_available"] and
        file_results["all_files_present"] and
        file_results["candidates_folder_exists"] and
        perf_results["optimized_script_importable"]
    )
    
    if all_passed:
        console.print(Panel.fit(
            "🎉 All validations passed!\n"
            "Ready for optimized final run.",
            title="Success",
            border_style="green"
        ))
        console.print("\n🚀 Run optimized scoring with:")
        console.print("   make final-run")
    else:
        console.print(Panel.fit(
            "⚠️ Some validations failed.\n"
            "Please fix the issues above before running.",
            title="Issues Found",
            border_style="yellow"
        ))
        console.print("\n🔧 Fix issues with:")
        console.print("   make setup-final-run")

@app.command()
def benchmark():
    """Run a quick benchmark of the optimized system."""
    console.print("🏃 Running performance benchmark...")
    
    start_time = time.time()
    
    # Test import speed
    import_start = time.time()
    sys.path.insert(0, ".")
    import optimized_final_run
    import_time = time.time() - import_start
    
    # Test configuration loading
    config_start = time.time()
    from jd_fit_evaluator.config import cfg
    config_time = time.time() - config_start
    
    total_time = time.time() - start_time
    
    table = Table(title="Performance Benchmark")
    table.add_column("Operation", style="cyan")
    table.add_column("Time (ms)", style="green")
    
    table.add_row("Import Optimized Script", f"{import_time*1000:.1f}")
    table.add_row("Load Configuration", f"{config_time*1000:.1f}")
    table.add_row("Total Benchmark", f"{total_time*1000:.1f}")
    
    console.print(table)
    
    if total_time < 1.0:
        console.print("✅ Benchmark passed - system is fast!")
    else:
        console.print("⚠️ Benchmark slower than expected")

if __name__ == "__main__":
    app()
