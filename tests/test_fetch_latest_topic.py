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
    assert "研究段階なのか" in fact["body"]
    assert "Example Newsの報道です" in fact["narration_body"]


def test_is_usable_rejects_old_or_blocked_items():
    latest = load_latest_module()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = datetime.now(timezone.utc)
    old = cutoff - timedelta(seconds=1)

    assert latest.is_usable(latest.NewsItem("科学の新発見", "https://example.com", recent, ""), cutoff)
    assert not latest.is_usable(latest.NewsItem("科学の新発見", "https://example.com", old, ""), cutoff)
    assert not latest.is_usable(latest.NewsItem("事故で研究施設が停止", "https://example.com", recent, ""), cutoff)


def test_is_usable_rejects_low_information_market_headline():
    latest = load_latest_module()
    recent = datetime.now(timezone.utc)
    cutoff = recent - timedelta(hours=24)

    assert not latest.is_usable(
        latest.NewsItem("7日の動意株>ウチヤマHD", "https://example.com", recent, "Yahoo!ファイナンス"),
        cutoff,
    )
    assert not latest.is_usable(
        latest.NewsItem("AI教材の新機能を発表", "https://example.com", recent, "PR TIMES"),
        cutoff,
    )


def test_information_score_prefers_concrete_headline():
    latest = load_latest_module()
    now = datetime.now(timezone.utc)
    vague = latest.NewsItem("AIの最新動向まとめ", "https://example.com/1", now, "Example")
    concrete = latest.NewsItem("AIロボットを2030年度に実用化、1台で壁塗りと塗装", "https://example.com/2", now, "Example")

    assert latest.information_score(concrete) > latest.information_score(vague)


def test_build_fact_uses_source_and_original_context_without_article_copy():
    latest = load_latest_module()
    item = latest.NewsItem(
        "AIロボットを2030年度に実用化",
        "https://example.com/news",
        datetime.now(timezone.utc),
        "Example News",
    )

    fact = latest.build_fact(item)

    assert fact["narration_title"] == "エーアイロボットを2030年度に実用化"
    assert fact["narration_body"].startswith("Example Newsの報道です。")
    assert "利用条件" in fact["narration_body"]
