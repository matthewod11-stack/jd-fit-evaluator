import pytest
from datetime import date, timedelta

from src.scoring.tenure import months_between, union_intervals

assert months_between.__module__ == union_intervals.__module__ == "src.scoring.tenure"

# -------------------------------
# months_between() unit tests
# -------------------------------
@pytest.mark.parametrize(
    "a,b,expected",
    [
        # Same month → 0 months
        (date(2024, 5, 1), date(2024, 5, 15), 0),
        # One full month apart
        (date(2024, 5, 1), date(2024, 6, 1), 1),
        # Cross-year
        (date(2023, 12, 1), date(2024, 1, 1), 1),
        # Multi-month span
        (date(2023, 1, 1), date(2024, 1, 1), 12),
    ],
)
def test_months_between_happy_paths(a, b, expected):
    assert months_between(a, b) == expected

def test_months_between_order_invariance():
    a, b = date(2024, 6, 1), date(2024, 5, 1)
    with pytest.raises(ValueError):
        months_between(a, b)

# -------------------------------
# union_intervals() unit tests
# -------------------------------
def d(y, m, d=1):  # helper
    return date(y, m, d)

def test_union_merges_overlapping():
    # Intervals overlap by 15 days → must merge to one
    ranges = [(d(2024, 1), d(2024, 3)), (d(2024, 2), d(2024, 4))]
    merged = union_intervals(ranges, tolerance_days=60)
    assert merged == [(d(2024, 1), d(2024, 4))]

    # Intervals that meet exactly at the endpoint should also merge (inclusive end)
    touching = [(d(2024, 1), d(2024, 3)), (d(2024, 3), d(2024, 4))]
    assert union_intervals(touching, tolerance_days=0) == [(d(2024, 1), d(2024, 4))]

def test_union_merges_adjacent_within_tolerance():
    # Adjacent within tolerance (30 days) → single merged interval
    ranges = [(d(2024, 1), d(2024, 2)), (d(2024, 2), d(2024, 3))]
    merged = union_intervals(ranges, tolerance_days=60)
    assert merged == [(d(2024, 1), d(2024, 3))]

def test_union_does_not_merge_beyond_tolerance():
    # Gap > tolerance → keep separate
    ranges = [(d(2024, 1), d(2024, 2)), (d(2024, 4), d(2024, 5))]
    merged = union_intervals(ranges, tolerance_days=30)
    assert merged == ranges

def test_union_sorts_and_normalizes():
    # Unordered inputs must be sorted before merging
    ranges = [(d(2024, 3), d(2024, 4)), (d(2024, 1), d(2024, 2))]
    merged = union_intervals(ranges, tolerance_days=0)
    assert merged == [(d(2024, 1), d(2024, 2)), (d(2024, 3), d(2024, 4))]

def test_union_handles_inclusive_endpoints():
    ranges = [(d(2024, 1), d(2024, 2)), (d(2024, 2), d(2024, 2))]
    merged = union_intervals(ranges, tolerance_days=0)
    assert merged == [(d(2024, 1), d(2024, 2))]

# -------------------------------
# Integration-ish sanity check
# -------------------------------
def test_total_months_from_merged_intervals():
    ranges = [(d(2023, 1), d(2023, 6)), (d(2023, 5), d(2023, 8))]
    merged = union_intervals(ranges, tolerance_days=60)
    # Expect merged single block Jan→Aug
    assert merged == [(d(2023, 1), d(2023, 8))]
    total_months = sum(months_between(start, end) for start, end in merged)
    assert total_months == months_between(d(2023, 1), d(2023, 8))

# NOTE:
# - After implementing months_between/union_intervals, replace placeholder asserts with exact expectations.
# - Add more edge cases: open-ended stints (end=None), partial dates, timezone irrelevance (dates only).
