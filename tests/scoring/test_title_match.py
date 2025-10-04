import pytest

from jd_fit_evaluator.scoring.features import new_title_match_score


def test_bidirectional_contains():
    forward = new_title_match_score("senior product designer", "product designer")
    backward = new_title_match_score("product designer", "senior product designer")

    assert forward >= 0.95
    assert backward >= 0.95

def test_level_mapping():
    principal_lead = new_title_match_score("principal software engineer", "lead software engineer")
    principal_senior = new_title_match_score("principal software engineer", "senior software engineer")

    assert principal_lead > principal_senior
    assert principal_lead >= 0.9
    assert principal_senior >= 0.85

def test_token_overlap_fallback_generates_score():
    score = new_title_match_score("design lead", "design manager")

    assert score >= 0.6
    assert score < 0.95
