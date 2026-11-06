"""Palīgfunkcijas spēlei: segvārda pārbaude un rezultātu kārtošana."""

# re: regulārās izteiksmes, ar kurām pārbauda, no kādām rakstzīmēm sastāv teksts
import re


def validate_nickname(value):
    """Atļauj 3-16 rakstzīmes: latīņu burtus, ciparus un pasvītru."""
    # Ja segvārda nav vispār, tas nav derīgs
    if value is None:
        return False
    # Noņem liekos atstarpes sākumā un beigās
    cleaned = value.strip()
    # Garumam jābūt no 3 līdz 16 rakstzīmēm
    if not 3 <= len(cleaned) <= 16:
        return False
    # Atļauti tikai latīņu burti (A-Z, a-z), cipari (0-9) un pasvītra (_)
    return bool(re.fullmatch(r"[A-Za-z0-9_]+", cleaned))


def sort_leaderboard_records(records):
    """Kārto pēc mazākā kopējā laika, tad pēc lielākā monētu skaita."""
    # Pašlaik šo funkciju spēle neizmanto: kārtošanu veic serveris (API) ar SQL.
    return sorted(
        records,
        key=lambda row: (
            float(row.get("total_time", 0)),   # vispirms mazāks laiks ir labāks
            -int(row.get("coins", 0)),         # ja laiks vienāds, vairāk monētu ir labāk (mīnuss apgriež secību)
        ),
    )