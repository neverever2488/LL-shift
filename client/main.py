"""Spēles klienta palaišanas punkts."""

import sys
from pathlib import Path
import runpy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Atrod spēles kodu, izmantojot šī faila atrašanās vietu.
game_file = PROJECT_ROOT / "game" / "main.py"
runpy.run_path(str(game_file), run_name="__main__")
