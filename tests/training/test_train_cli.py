import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from jd_fit_evaluator.cli import app
from src.training.train import train


def _write_scores(tmp_path: Path) -> Path:
    records = [
        {
            "candidate_id": "c-1",
            "candidate": "Ada Lovelace",
            "title": 0.9,
            "industry": 0.8,
            "skills": 0.7,
            "context": 0.6,
            "tenure": 0.5,
            "recency": 0.4,
            "bonus": 0.3,
        },
        {
            "candidate_id": "c-2",
            "candidate": "Grace Hopper",
            "title": 0.2,
            "industry": 0.3,
            "skills": 0.4,
            "context": 0.5,
            "tenure": 0.6,
            "recency": 0.7,
            "bonus": 0.8,
        },
        {
            "candidate_id": "c-3",
            "candidate": "Katherine Johnson",
            "title": 0.1,
            "industry": 0.2,
            "skills": 0.3,
            "context": 0.4,
            "tenure": 0.5,
            "recency": 0.6,
            "bonus": 0.7,
        },
    ]
    scores_path = tmp_path / "scores.json"
    scores_path.write_text(json.dumps(records))
    return scores_path


def test_accepts_either_id_or_name(tmp_path):
    scores_path = _write_scores(tmp_path)

    id_labels = tmp_path / "labels_by_id.csv"
    id_labels.write_text("candidate_id,label\nc-1,1\nc-2,0\nc-3,1\n")

    out_by_id = tmp_path / "model_id.pkl"
    path_id, meta_id = train(
        scores_path=str(scores_path),
        labels_csv=str(id_labels),
        out_path=str(out_by_id),
    )

    assert out_by_id.exists()
    assert path_id == str(out_by_id)
    assert meta_id["n"] == 3

    name_labels = tmp_path / "labels_by_name.csv"
    name_labels.write_text(
        "name,label\nAda Lovelace,1\nGrace Hopper,0\nKatherine Johnson,1\n"
    )

    out_by_name = tmp_path / "model_name.pkl"
    path_name, meta_name = train(
        scores_path=str(scores_path),
        labels_csv=str(name_labels),
        out_path=str(out_by_name),
    )

    assert out_by_name.exists()
    assert path_name == str(out_by_name)
    assert meta_name["n"] == 3

def test_noop_without_labels_exits_zero(tmp_path):
    scores_path = tmp_path / "scores.json"
    scores_path.write_text("[]")
    labels_path = tmp_path / "labels.csv"
    out_path = tmp_path / "model.pkl"

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "train",
            "--scores",
            str(scores_path),
            "--labels",
            str(labels_path),
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0
    assert "No labels found" in result.stdout
    assert not out_path.exists()
