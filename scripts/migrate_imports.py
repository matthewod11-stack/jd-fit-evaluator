"""
Automated import migration script.
Migrates all imports from legacy patterns to jd_fit_evaluator.* pattern.
"""
import re
from pathlib import Path
from typing import List, Tuple


def migrate_file(path: Path) -> Tuple[bool, List[str]]:
    """
    Migrate imports in a single file.
    Returns (changed, list_of_changes)
    """
    content = path.read_text()
    original = content
    changes = []
    
    # Pattern 1: from jd_fit_evaluator.scoring -> from jd_fit_evaluator.scoring
    pattern1 = re.compile(r'from src\.scoring')
    if pattern1.search(content):
        content = pattern1.sub('from jd_fit_evaluator.scoring', content)
        changes.append("src.scoring  jd_fit_evaluator.scoring")
    
    # Pattern 2: from jd_fit_evaluator.parsing -> from jd_fit_evaluator.parsing
    pattern2 = re.compile(r'from src\.parsing')
    if pattern2.search(content):
        content = pattern2.sub('from jd_fit_evaluator.parsing', content)
        changes.append("src.parsing  jd_fit_evaluator.parsing")
    
    # Pattern 3: from jd_fit_evaluator.etl -> from jd_fit_evaluator.etl
    pattern3 = re.compile(r'from src\.etl')
    if pattern3.search(content):
        content = pattern3.sub('from jd_fit_evaluator.etl', content)
        changes.append("src.etl  jd_fit_evaluator.etl")
    
    # Pattern 4: from jd_fit_evaluator.scoring. -> from jd_fit_evaluator.scoring.
    # (bare imports that need sys.path hack)
    pattern4 = re.compile(r'from scoring\.')
    if pattern4.search(content):
        content = pattern4.sub('from jd_fit_evaluator.scoring.', content)
        changes.append("scoring.  jd_fit_evaluator.scoring.")
    
    # Pattern 5: from jd_fit_evaluator.parsing. -> from jd_fit_evaluator.parsing.
    pattern5 = re.compile(r'from parsing\.')
    if pattern5.search(content):
        content = pattern5.sub('from jd_fit_evaluator.parsing.', content)
        changes.append("parsing.  jd_fit_evaluator.parsing.")
    
    # Pattern 6: Remove sys.path.insert hacks
    pattern6 = re.compile(r'sys\.path\.insert\(0,\s*["\']src["\']\)\n')
    if pattern6.search(content):
        content = pattern6.sub('', content)
        changes.append("Removed sys.path.insert(0, 'src')")
    
    # Pattern 7: Remove unused sys import if it was only for path manipulation
    if 'import sys' in content and 'sys.' not in content.replace('import sys', ''):
        content = re.sub(r'^import sys\n', '', content, flags=re.MULTILINE)
        changes.append("Removed unused 'import sys'")
    
    changed = content != original
    if changed:
        path.write_text(content)
    
    return changed, changes


def main():
    """Run migration on all Python files."""
    total_changed = 0
    
    # Directories to scan
    directories = ['src', 'tests', 'app', 'ui', '.']
    
    for dir_path in directories:
        if not Path(dir_path).exists():
            continue
            
        for py_file in Path(dir_path).rglob('*.py'):
            # Skip __pycache__ and .venv
            if '__pycache__' in str(py_file) or '.venv' in str(py_file):
                continue
            
            changed, changes = migrate_file(py_file)
            if changed:
                total_changed += 1
                print(f"\n[32m✓ {py_file}[0m")
                for change in changes:
                    print(f"  - {change}")
    
    print(f"\n{'='*60}")
    print(f"Migration complete: {total_changed} files modified")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("1. Review changes: git diff")
    print("2. Run tests: pytest")
    print("3. Check guardpaths: make guardpaths")


if __name__ == "__main__":
    main()
