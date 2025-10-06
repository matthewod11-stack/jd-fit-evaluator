#!/usr/bin/env python3
"""
Verify that all imported packages are declared in pyproject.toml dependencies.
This script analyzes Python imports across the codebase and checks against declared dependencies.
"""

import ast
import sys
from pathlib import Path
from typing import Set, Dict, List
import subprocess
import json


def get_imports_from_file(file_path: Path) -> Set[str]:
    """Extract top-level imports from a Python file."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get top-level module name
                    module = alias.name.split('.')[0]
                    imports.add(module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get top-level module name
                    module = node.module.split('.')[0]
                    imports.add(module)
    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")
    
    return imports


def get_all_imports(src_dirs: List[Path]) -> Set[str]:
    """Get all imports from Python files in source directories."""
    all_imports = set()
    
    for src_dir in src_dirs:
        if not src_dir.exists():
            continue
            
        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            imports = get_imports_from_file(py_file)
            all_imports.update(imports)
    
    return all_imports


def get_declared_dependencies() -> Set[str]:
    """Extract dependencies from pyproject.toml."""
    import tomllib
    
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    with open(pyproject_path, 'rb') as f:
        data = tomllib.load(f)
    
    dependencies = set()
    
    # Main dependencies
    if "project" in data and "dependencies" in data["project"]:
        for dep in data["project"]["dependencies"]:
            # Extract package name before version specifiers
            pkg_name = dep.split(">=")[0].split("==")[0].split(">")[0].split("<")[0].strip()
            dependencies.add(pkg_name)
    
    # Optional dependencies
    if "project" in data and "optional-dependencies" in data["project"]:
        for group in data["project"]["optional-dependencies"].values():
            for dep in group:
                pkg_name = dep.split(">=")[0].split("==")[0].split(">")[0].split("<")[0].strip()
                dependencies.add(pkg_name)
    
    return dependencies


def get_stdlib_modules() -> Set[str]:
    """Get standard library module names for current Python version."""
    # Common stdlib modules - this is a subset for practicality
    stdlib_modules = {
        '__future__', 'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections',
        'contextlib', 'copy', 'csv', 'dataclasses', 'datetime', 'decimal', 'difflib',
        'enum', 'functools', 'glob', 'hashlib', 'io', 'itertools', 'json', 'logging',
        'math', 'operator', 'os', 'pathlib', 'pickle', 're', 'shutil', 'sqlite3',
        'string', 'subprocess', 'sys', 'tempfile', 'threading', 'time', 'traceback',
        'typing', 'urllib', 'uuid', 'warnings', 'weakref', 'xml'
    }
    return stdlib_modules


def normalize_package_name(import_name: str) -> str:
    """Normalize import names to match PyPI package names."""
    # Handle common package name differences
    name_mapping = {
        'docx': 'python-docx',
        'pdfminer': 'pdfminer.six',
        'sklearn': 'scikit-learn',
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
    }
    return name_mapping.get(import_name, import_name)


def main():
    """Main verification function."""
    print("🔍 Verifying dependency completeness...")
    
    # Get all imports from source code
    src_dirs = [Path("src"), Path("app"), Path("ui"), Path(".")]
    all_imports = get_all_imports(src_dirs)
    
    # Filter out standard library modules and local modules
    stdlib_modules = get_stdlib_modules()
    local_modules = {'jd_fit_evaluator'}  # Our package name
    
    third_party_imports = set()
    for imp in all_imports:
        if imp not in stdlib_modules and imp not in local_modules:
            normalized = normalize_package_name(imp)
            third_party_imports.add(normalized)
    
    print(f"📦 Found {len(third_party_imports)} third-party imports:")
    for imp in sorted(third_party_imports):
        print(f"  - {imp}")
    
    # Get declared dependencies
    try:
        declared_deps = get_declared_dependencies()
        print(f"\n📋 Found {len(declared_deps)} declared dependencies:")
        for dep in sorted(declared_deps):
            print(f"  - {dep}")
    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")
        return 1
    
    # Find missing dependencies
    missing_deps = third_party_imports - declared_deps
    unused_deps = declared_deps - third_party_imports
    
    print(f"\n🔍 Analysis Results:")
    print(f"  Third-party imports: {len(third_party_imports)}")
    print(f"  Declared dependencies: {len(declared_deps)}")
    print(f"  Missing from pyproject.toml: {len(missing_deps)}")
    print(f"  Potentially unused: {len(unused_deps)}")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies in pyproject.toml:")
        for dep in sorted(missing_deps):
            print(f"  - {dep}")
    
    if unused_deps:
        print(f"\n⚠️  Potentially unused dependencies:")
        for dep in sorted(unused_deps):
            print(f"  - {dep}")
    
    if not missing_deps:
        print(f"\n✅ Dependency verification passed!")
        return 0
    else:
        print(f"\n❌ Dependency verification failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())