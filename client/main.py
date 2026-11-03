"""Spēles klienta palaišanas punkts."""

import sys
from pathlib import Path
import runpy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Atrod spēles kodu, izmantojot šī faila atrašanās vietu.
game_file = PROJECT_ROOT / "game" / "phase_shift.py"
if not game_file.exists():
    sys.exit(f"Spēles fails nav atrasts: {game_file}")

runpy.run_path(str(game_file), run_name="__main__")
