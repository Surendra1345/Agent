import os
import sys
from pathlib import Path

# Dummy settings so modules import without a real DB or API key.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://u:p@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
