import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_latest_module():
    source_path = Path(__file__).resolve().parents[1] / "scripts" / "fetch_latest_topic.py"
    spec = importlib.util.spec_from_file_location("fetch_latest_topic", source_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_parse_rss_and_build_fact():
    latest = load_latest_module()
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <item>
          <title>AI新技術が医療画像の確認を助ける - Example News</title>
          <link>https://example.com/news</link>
          <pubDate>Tue, 16 Jun 2026 01:00:00 GMT</pubDate>
          <source>Example News</source>
        </item>
      </channel>
    </rss>
    """

    items = latest.parse_rss(xml)
    fact = latest.build_fact(items[0])

    assert items[0].title == "AI新技術が医療画像の確認を助ける"
    assert fact["category"] == "人体"
    assert fact["source_url"] == "https://example.com/news"
    assert "今日話題の" in fact["title"]
    assert "エーアイ" in fact["narration_title"]
    assert "公式発表" in fact["body"]


def test_is_usable_rejects_old_or_blocked_items():
    latest = load_latest_module()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = datetime.now(timezone.utc)
    old = cutoff - timedelta(seconds=1)

    assert latest.is_usable(latest.NewsItem("科学の新発見", "https://example.com", recent, ""), cutoff)
    assert not latest.is_usable(latest.NewsItem("科学の新発見", "https://example.com", old, ""), cutoff)
    assert not latest.is_usable(latest.NewsItem("事故で研究施設が停止", "https://example.com", recent, ""), cutoff)
