from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
BACKEND_DIR = SRC_DIR / "backend"
UTILS_DIR = SRC_DIR / "utils"
FRONTEND_DIR = SRC_DIR / "frontend"

for path in (SRC_DIR, BACKEND_DIR, UTILS_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = ROOT_DIR / "results"


def _first_existing_path(*candidates: Path) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


USC_CAMPUS_DIR = _first_existing_path(
    DATA_DIR / "usc_campus",
    PROCESSED_DIR / "usc_campus",
    RAW_DIR / "usc_campus",
)
ENV_FILE = _first_existing_path(
    ROOT_DIR / ".env",
    SRC_DIR / ".env",
    BACKEND_DIR / ".env",
)


def data_path(*parts: str) -> Path:
    return DATA_DIR.joinpath(*parts)


def raw_path(*parts: str) -> Path:
    return RAW_DIR.joinpath(*parts)


def processed_path(*parts: str) -> Path:
    return PROCESSED_DIR.joinpath(*parts)


def results_path(*parts: str) -> Path:
    return RESULTS_DIR.joinpath(*parts)


def usc_campus_path(*parts: str) -> Path:
    return USC_CAMPUS_DIR.joinpath(*parts)
