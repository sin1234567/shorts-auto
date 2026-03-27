import json
import importlib.util
import sys
from pathlib import Path

from googleapiclient.errors import HttpError, ResumableUploadError


def load_upload_youtube_module():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "upload_youtube.py"
    sys.path.insert(0, str(source_path.parent))
    spec = importlib.util.spec_from_file_location("upload_youtube", source_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_write_status_writes_expected_json(tmp_path, monkeypatch):
    upload_youtube = load_upload_youtube_module()
    status_file = tmp_path / "upload_status.json"
    monkeypatch.setattr(upload_youtube, "STATUS", status_file)

    upload_youtube.write_status("uploaded", video_id="abc123")

    assert json.loads(status_file.read_text(encoding="utf-8")) == {
        "status": "uploaded",
        "video_id": "abc123",
    }


def test_is_upload_limit_error_returns_true_for_limit_errors():
    upload_youtube = load_upload_youtube_module()
    http_exc = HttpError(
        resp=type("Resp", (), {"status": 403, "reason": "Forbidden"})(),
        content=b'{"error":{"message":"uploadLimitExceeded"}}',
    )
    resumable_exc = ResumableUploadError(
        resp=type("Resp", (), {"status": 403, "reason": "Forbidden"})(),
        content=b'{"error":{"message":"The user has exceeded the number of videos they may upload."}}',
    )

    assert upload_youtube.is_upload_limit_error(http_exc) is True
    assert upload_youtube.is_upload_limit_error(resumable_exc) is True


def test_is_upload_limit_error_returns_false_for_unrelated_exceptions():
    upload_youtube = load_upload_youtube_module()
    http_exc = HttpError(
        resp=type("Resp", (), {"status": 500, "reason": "Server Error"})(),
        content=b'{"error":{"message":"backendError"}}',
    )

    assert upload_youtube.is_upload_limit_error(RuntimeError("nope")) is False
    assert upload_youtube.is_upload_limit_error(http_exc) is False
