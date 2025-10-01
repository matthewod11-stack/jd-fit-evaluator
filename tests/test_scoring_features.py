import json
import sys
import types
from pathlib import Path

from src.etl.greenhouse import get_stints
from src.scoring.features import tenure_scores, recency_score


def test_tenure_and_recency_computed(monkeypatch):
    fake_docx = types.ModuleType("docx")
    fake_docx.Document = lambda *args, **kwargs: types.SimpleNamespace(paragraphs=[])
    monkeypatch.setitem(sys.modules, "docx", fake_docx)

    candidate = json.loads(Path("data/sample/candidate_example.json").read_text())
    stints = get_stints(candidate)

    assert stints, "expected normalized stints from sample candidate"

    avg_months, last_months, tenure_score = tenure_scores(stints)
    recency = recency_score(stints)

    assert avg_months > 0
    assert last_months > 0
    assert tenure_score > 0
    assert recency > 0
