import pytest

from game.logic import sort_leaderboard_records, validate_nickname


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Ava", True),
        ("neo_7", True),
        ("ab", False),
        ("bad-name", False),
        ("x" * 17, False),
    ],
)
def test_validate_nickname(name, expected):
    assert validate_nickname(name) is expected


def test_sort_leaderboard_records_prefers_fastest_time_then_more_coins():
    records = [
        {"nickname": "Rex", "total_time": 40.0, "coins": 8},
        {"nickname": "Zoe", "total_time": 35.0, "coins": 7},
        {"nickname": "Ari", "total_time": 35.0, "coins": 10},
        {"nickname": "Mia", "total_time": 35.0, "coins": 10},
    ]

    ordered = sort_leaderboard_records(records)

    assert [row["nickname"] for row in ordered] == ["Ari", "Mia", "Zoe", "Rex"]
