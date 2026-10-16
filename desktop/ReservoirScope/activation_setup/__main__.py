"""Entrypoint suitable for the bundled standalone interpreter's isolated mode."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from activation_setup.driver import main

main()
