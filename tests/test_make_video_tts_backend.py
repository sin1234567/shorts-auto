import ast
import os
from pathlib import Path


def load_get_tts_backend():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "make_video.py"
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "get_tts_backend"]
    namespace = {"__builtins__": __builtins__, "os": os}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source_path), "exec"), namespace)
    return namespace["get_tts_backend"]


def test_get_tts_backend_defaults_to_edge_tts(monkeypatch):
    monkeypatch.delenv("TTS_BACKEND", raising=False)
    get_tts_backend = load_get_tts_backend()

    assert get_tts_backend() == "edge-tts"


def test_get_tts_backend_accepts_open_jtalk_alias(monkeypatch):
    monkeypatch.setenv("TTS_BACKEND", "open_jtalk")
    get_tts_backend = load_get_tts_backend()

    assert get_tts_backend() == "open-jtalk"


def test_get_tts_backend_rejects_unknown_values(monkeypatch):
    monkeypatch.setenv("TTS_BACKEND", "nope")
    get_tts_backend = load_get_tts_backend()

    try:
        get_tts_backend()
    except RuntimeError as exc:
        assert "Unsupported TTS_BACKEND" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for unsupported TTS_BACKEND")
