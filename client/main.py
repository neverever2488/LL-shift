"""Spēles klienta palaišanas punkts."""

from pathlib import Path
import runpy


# Atrod spēles kodu, izmantojot šī faila atrašanās vietu.
game_file = Path(__file__).resolve().parent.parent / "game" / "main.py"
runpy.run_path(str(game_file), run_name="__main__")
