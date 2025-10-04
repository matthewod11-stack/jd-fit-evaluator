from pathlib import Path

from jd_fit_evaluator.scoring.rationale import build_rationale
from jd_fit_evaluator.scoring.jd_profile import AGORIC_SENIOR_PRODUCT_DESIGNER as jd


def test_rationale_matches_snapshot():
    signals = {
        "title_match": {"label": "Senior Product Designer", "score": 0.9},
        "web3_experience": {"years": 3, "score": 0.8, "evidence": "Worked on DeFi product X"},
        "usability_testing": True,
        "design_systems": {"score": 0.4},
    }
    weights = {"title": 0.3, "skills": 0.4, "tenure": 0.2, "recency": 0.1}

    out = build_rationale(signals, weights, jd=jd, use_llm=False)
    expected = Path("tests/fixtures/rationale_pd_snapshot.md").read_text(encoding="utf-8").strip()
    assert out.strip() == expected
