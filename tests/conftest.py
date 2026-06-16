import shutil
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / "tests_tmp"
TMP_ROOT.mkdir(exist_ok=True)


@pytest.fixture
def tmp_path():
    path = TMP_ROOT / f"tmp_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
