"""Keep integration tests isolated from the developer's configured database."""

import os
import tempfile
from pathlib import Path


_TEST_DATABASE_DIR = tempfile.TemporaryDirectory(prefix="campussync-tests-")
_TEST_DATABASE_PATH = Path(_TEST_DATABASE_DIR.name, "campussync-test.db").as_posix()

# conftest.py is loaded before test modules import the app and create its engine.
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DATABASE_PATH}"
os.environ["JWT_SECRET"] = "campussync_test_only_secret_with_more_than_32_chars"


def pytest_sessionfinish(session, exitstatus):
    try:
        from backend.app.database import engine

        engine.dispose()
    finally:
        _TEST_DATABASE_DIR.cleanup()
