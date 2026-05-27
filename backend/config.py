import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# DATA_DIR: set to a Railway Volume mount path in production (e.g. /data),
# falls back to backend/storage/ for local development.
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "storage")))
STORAGE_DIR = DATA_DIR
ORIGINALS_DIR = STORAGE_DIR / "originals"
OPTIMIZED_DIR = STORAGE_DIR / "optimized"

# Template assets are bundled inside backend/assets/
ASSETS_DIR = BASE_DIR / "assets"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{STORAGE_DIR}/reports.db",
)

DECKBLATT_PATH  = Path(os.getenv("DECKBLATT_PATH",  str(ASSETS_DIR / "Deckblatt.pdf")))
DISCLAIMER_PATH = Path(os.getenv("DISCLAIMER_PATH", str(ASSETS_DIR / "Disclaimer.pdf")))
LOGO_SOURCE_PDF = Path(os.getenv("LOGO_SOURCE_PDF", str(ASSETS_DIR / "Report_Multi-Print.pdf")))
LOGO_JPG_PATH   = Path(os.getenv("LOGO_JPG_PATH",   str(ASSETS_DIR / "ProfinalSolar_Logo_RGB.jpg")))

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:4173",
).split(",")
