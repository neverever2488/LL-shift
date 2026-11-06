"""Testi funkcijām no game/logic.py (palaiž ar komandu: pytest)."""

# pytest: bibliotēka testu rakstīšanai un palaišanai
import pytest

# Funkcijas, kuras mēs testējam
from game.logic import sort_leaderboard_records, validate_nickname


# Viens tests tiek izpildīts vairākas reizes ar dažādiem datiem (parametrize):
# katrs pāris ir (segvārds, vai tas ir derīgs)
@pytest.mark.parametrize(
    "name, expected",
    [
        ("Ava", True),        # 3 burti: derīgs
        ("neo_7", True),      # burti, pasvītra un cipars: derīgs
        ("ab", False),        # tikai 2 rakstzīmes: par īsu
        ("bad-name", False),  # defise nav atļauta
        ("x" * 17, False),    # 17 rakstzīmes: par garu (maksimums ir 16)
    ],
)
def test_validate_nickname(name, expected):
    # 'is' pārbauda, ka rezultāts ir tieši True vai False
    assert validate_nickname(name) is expected


def test_sort_leaderboard_records_prefers_fastest_time_then_more_coins():
    # Testa dati: trim spēlētājiem ir vienāds laiks (35.0), bet dažāds monētu skaits
    records = [
        {"nickname": "Rex", "total_time": 40.0, "coins": 8},
        {"nickname": "Zoe", "total_time": 35.0, "coins": 7},
        {"nickname": "Ari", "total_time": 35.0, "coins": 10},
        {"nickname": "Mia", "total_time": 35.0, "coins": 10},
    ]

    ordered = sort_leaderboard_records(records)

    # Gaidāmā secība: vispirms mazākais laiks (35.0), un no tiem vairāk monētu ir augstāk.
    # Ari un Mia ir pilnīgi vienādi, tāpēc paliek sākotnējā secībā (Ari pirms Mia).
    # Zoe ir ar mazāk monētu, bet Rex ar lielāko laiku (40.0), tāpēc viņš ir pēdējais.
    assert [row["nickname"] for row in ordered] == ["Ari", "Mia", "Zoe", "Rex"]