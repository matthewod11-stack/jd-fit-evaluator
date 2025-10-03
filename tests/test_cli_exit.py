import subprocess, sys, os

def test_cli_exit_code(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "jd_fit_evaluator.cli", "score", "nonexistent-dir", "--role", "x"],
        capture_output=True,
    )
    assert result.returncode == 1