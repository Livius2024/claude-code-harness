import sys
from pathlib import Path

STARTER = Path(__file__).resolve().parent.parent / "project-starter"
sys.path.insert(0, str(STARTER / "scripts"))
