import importlib.util
import json
from pathlib import Path


def load_make_video_module():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "make_video.py"
    spec = importlib.util.spec_from_file_location("make_video", source_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_load_latest_fact_when_enabled(tmp_path, monkeypatch):
    make_video = load_make_video_module()
    latest = tmp_path / "latest_fact.json"
    latest.write_text(
        json.dumps(
            {
                "title": "今日話題の「AI新技術」はここを見ると分かりやすい",
                "body": "今日のニュースではAI新技術が話題です。仕組みを見ると理解しやすいです。",
                "category": "科学",
                "narration_title": "今日話題のエーアイ新技術",
                "narration_body": "今日は、エーアイ新技術の話です。仕組みを見ると分かりやすいです。",
                "source_url": "https://example.com/news",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("USE_LATEST_TOPIC", "1")
    monkeypatch.setenv("LATEST_TOPIC_JSON", str(latest))

    fact = make_video.load_latest_fact(set())

    assert fact is not None
    assert fact["title"].startswith("今日話題の「AI新技術」")
    assert fact["category"] == "科学"
    assert fact["narration_title"] == "今日話題のエーアイ新技術"
    assert fact["source_url"] == "https://example.com/news"


def test_load_latest_fact_falls_back_when_disabled_or_posted(tmp_path, monkeypatch):
    make_video = load_make_video_module()
    latest = tmp_path / "latest_fact.json"
    latest.write_text(
        json.dumps(
            {
                "title": "今日話題の「気象研究」はここを見ると分かりやすい",
                "body": "今日のニュースでは気象研究が話題です。仕組みを見ると理解しやすいです。",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("LATEST_TOPIC_JSON", str(latest))
    monkeypatch.delenv("USE_LATEST_TOPIC", raising=False)
    assert make_video.load_latest_fact(set()) is None

    monkeypatch.setenv("USE_LATEST_TOPIC", "1")
    assert make_video.load_latest_fact({"今日話題の「気象研究」はここを見ると分かりやすい"}) is None
