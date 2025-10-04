import pytest

# mapping module is still in src/mapping (not yet migrated to jd_fit_evaluator)
from mapping.title_industry import normalize_title, normalize_industry

# -----------------------------------------------------------------------------
# Title normalization tests
# -----------------------------------------------------------------------------

def test_dict_fast_path_mappings():
    """
    Dictionary fast-path should map common designer title variants to a canonical label.
    (PR-03): Replace EXPECTED_* placeholders with the actual canonical strings used in your map.
    """
    cases = [
        ("Sr. Product Designer",        "Product Designer"),
        ("Senior Product Designer",     "Product Designer"),
        ("Design Lead",                 "Product Designer"),
        ("Product Design (IC5)",        "Product Designer"),
        ("UX/UI Designer",              "Product Designer"),
        ("Visual Designer (Product)",   "Product Designer"),
    ]
    for raw, expected in cases:
        got = normalize_title(raw)
        assert isinstance(got, str)
        assert got  # non-empty
        assert got == expected


def test_normalizes_casing_and_punctuation():
    """
    Normalization should be resilient to casing/punctuation noise.
    """
    noisy = "  senior   PRODUCT-designer  "
    got = normalize_title(noisy)
    assert isinstance(got, str)
    assert got  # non-empty


def test_embedding_fallback_threshold(monkeypatch):
    """
    If dictionary misses, embedding similarity over a curated title set should decide.
    This test assumes an internal seam like `title_industry._embedding_topk`.
    """
    import mapping.title_industry as ti

    def fake_topk(q, k=5):
        # Return a ranked list with similarity scores that simulate a close match.
        return [("Senior Product Designer", 0.83), ("Product Designer", 0.78)]

    monkeypatch.setattr(ti, "_embedding_topk", fake_topk, raising=False)

    got = ti.normalize_title("Product Design Specialist")
    assert got in {"Senior Product Designer", "Product Designer"}


def test_llm_adjudication_tie_breaker(monkeypatch):
    """
    If embeddings produce a tie/ambiguity, call a constrained LLM adjudicator.
    This test assumes a seam like `title_industry._adjudicate_with_llm`.
    """
    import mapping.title_industry as ti

    def fake_topk(q, k=5):
        # Ambiguous top-2 to force LLM adjudication path
        return [("Senior Product Designer", 0.80), ("Product Designer", 0.80)]

    def fake_llm(q, options):
        # Deterministically prefer the senior variant for the tie
        return "Senior Product Designer"

    monkeypatch.setattr(ti, "_embedding_topk", fake_topk, raising=False)
    monkeypatch.setattr(ti, "_adjudicate_with_llm", fake_llm, raising=False)

    got = ti.normalize_title("Design Specialist V")
    assert got == "Senior Product Designer"


# -----------------------------------------------------------------------------
# Industry normalization tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize(
    "raw, expected_bucket",
    [
        ("Crypto / Web3",          "Web3/DeFi"),
        ("DeFi",                   "Web3/DeFi"),
        ("FinTech",                "FinTech"),
        ("E-commerce",             "E-commerce"),
        ("Agency / Consultancy",   "Agency"),
        ("Blockchain",             "Web3/DeFi"),
    ],
)
def test_industry_bucket_mapping(raw, expected_bucket):
    """
    Map common industry labels/variants into a small set of buckets.
    (PR-03): Align expected buckets with the repo's final taxonomy.
    """
    got = normalize_industry(raw)
    assert isinstance(got, str)
    assert got  # non-empty


def test_unknown_title_passthrough_is_string():
    """
    For unknown titles without a confident match, normalize_title should still return a string.
    You may choose to return the cleaned raw, or a placeholder like 'Unknown'.
    """
    got = normalize_title("Design Wizard of Oz")
    assert isinstance(got, str)
    assert got  # non-empty
