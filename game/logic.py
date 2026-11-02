import re


def validate_nickname(value):
    """Allow 3-16 characters using letters, numbers, and underscores."""
    if value is None:
        return False
    cleaned = value.strip()
    if not 3 <= len(cleaned) <= 16:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_]+", cleaned))


def sort_leaderboard_records(records):
    """Sort by shortest total time, then by highest coin count."""
    return sorted(
        records,
        key=lambda row: (
            float(row.get("total_time", 0)),
            -int(row.get("coins", 0)),
        ),
    )
