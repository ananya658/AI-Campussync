"""Vercel entrypoint for the FastAPI backend service."""

import sys
from pathlib import Path
from types import ModuleType


# The Vercel service root is `backend/`, while the application keeps its
# existing `backend.app.*` imports. Expose this service root as that package.
backend_package = ModuleType("backend")
backend_package.__path__ = [str(Path(__file__).resolve().parent)]
sys.modules.setdefault("backend", backend_package)

from backend.app.main import app  # noqa: E402

