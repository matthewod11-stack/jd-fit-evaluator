from datetime import date
from typing import List, Tuple


def _first_of_month(d: date) -> date:
    return d.replace(day=1)


def months_between(a: date, b: date) -> int:
    if a > b:
        raise ValueError("start date must not exceed end date")

    start = _first_of_month(a)
    end = _first_of_month(b)
    return (end.year - start.year) * 12 + (end.month - start.month)

def union_intervals(ranges: List[Tuple[date, date]], tolerance_days: int = 0) -> List[Tuple[date, date]]:
    if not ranges:
        return []

    tolerance = max(tolerance_days, 0)
    sorted_ranges = sorted(ranges, key=lambda r: (r[0], r[1]))

    merged: List[Tuple[date, date]] = []
    current_start, current_end = sorted_ranges[0]

    for start, end in sorted_ranges[1:]:
        if start <= current_end:
            if end > current_end:
                current_end = end
            continue

        gap = (start - current_end).days
        if gap <= tolerance:
            if end > current_end:
                current_end = end
            continue

        merged.append((current_start, current_end))
        current_start, current_end = start, end

    merged.append((current_start, current_end))
    return merged
