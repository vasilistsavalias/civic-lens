from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_eval_harness_generates_reports() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "tools" / "eval" / "run_eval.py"
    completed = subprocess.run([sys.executable, str(script)], cwd=str(root), check=True, capture_output=True, text=True)
    assert completed.returncode == 0

    report_dir = root / "docs" / "research" / "eval_reports"
    report_json = report_dir / "latest_report.json"
    report_md = report_dir / "latest_report.md"
    assert report_json.exists()
    assert report_md.exists()

    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert "macro_f1" in payload
    assert "calibration" in payload
