from datetime import date
import sys
import types

import pytest

fake_docx = types.ModuleType("docx")
fake_docx.Document = lambda *args, **kwargs: types.SimpleNamespace(paragraphs=[])
sys.modules.setdefault("docx", fake_docx)

from jd_fit_evaluator.etl.greenhouse import get_stints
from jd_fit_evaluator.parsing.stints import shape_adapter


def test_manifest_first():
    candidate = {
        "manifest_stints": [
            {
                "company": "Globex",
                "title": "Staff Product Designer",
                "start": "2022-02",
                "end": "present",
                "industry_tags": ["Web3", "Design"],
            },
            {
                "company": "Acme Inc.",
                "title": "Product Designer",
                "start": "2019-04",
                "end": "2021-12",
            },
        ],
        "experience": [
            "Fallback experience entry that should be ignored when manifest stints exist",
        ],
    }

    stints = get_stints(candidate)

    assert stints == [
        {
            "company": "Globex",
            "title": "Staff Product Designer",
            "start_date": date(2022, 2, 1),
            "end_date": None,
            "industry_tags": ["design", "web3"],
        },
        {
            "company": "Acme Inc.",
            "title": "Product Designer",
            "start_date": date(2019, 4, 1),
            "end_date": date(2021, 12, 1),
            "industry_tags": [],
        },
    ]

def test_shape_adapter_minimal_fallback_not_empty():
    stints = shape_adapter({"foo": "bar"})

    assert stints
    assert all(stint.get("title") or stint.get("company") for stint in stints)

def test_date_coercion_and_current_flag():
    candidate = {
        "experience": [
            {
                "company": "Initech",
                "title": "Product Designer",
                "start": "2021-02-17",
                "end": "2022-11-03",
            },
            {
                "company": "Initrode",
                "title": "Staff Product Designer",
                "start": {"year": 2023, "month": 1},
                "end": None,
            },
        ]
    }

    adapted = shape_adapter(candidate)

    assert adapted[0]["start"] == "2021-02"
    assert adapted[0]["end"] == "2022-11"
    assert adapted[1]["start"] == "2023-01"
    assert adapted[1]["end"] is None

    normalized = get_stints(candidate)
    ongoing = next(stint for stint in normalized if stint["company"] == "Initrode")

    assert ongoing["start_date"] == date(2023, 1, 1)
    assert ongoing["end_date"] is None
