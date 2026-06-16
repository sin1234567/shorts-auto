import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
LATEST_FACT = OUT / "latest_fact.json"

DEFAULT_QUERY = "科学 OR 宇宙 OR 健康 OR 医療 OR 気象 OR AI OR 新技術 OR 生活 when:1d"
RSS_BASE = "https://news.google.com/rss/search"

BLOCKED_KEYWORDS = [
    "逮捕",
    "容疑",
    "殺人",
    "死亡",
    "死去",
    "訃報",
    "事故",
    "火災",
    "戦争",
    "攻撃",
    "避難",
    "選挙",
    "首相",
    "大統領",
    "不倫",
    "炎上",
    "謝罪",
]

CATEGORY_KEYWORDS = {
    "人体": ["健康", "医療", "睡眠", "脳", "心臓", "血液", "筋肉", "目", "耳", "皮膚"],
    "宇宙": ["宇宙", "月", "火星", "太陽", "衛星", "ロケット", "天体", "NASA", "JAXA"],
    "地球": ["気象", "台風", "大雨", "猛暑", "地震", "火山", "海", "気温", "雲", "雨"],
    "科学": ["科学", "研究", "AI", "新技術", "電池", "ロボット", "半導体", "量子", "発見"],
}


@dataclass
class NewsItem:
    title: str
    link: str
    published_at: datetime
    source: str


def clean_headline(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s+-\s+[^-]+$", "", title).strip()
    return title.strip("「」『』")


def short_topic(headline: str) -> str:
    topic = re.split(r"[、。:：|｜]", headline, maxsplit=1)[0].strip()
    topic = re.sub(r"【[^】]+】", "", topic).strip()
    if "」" in topic:
        topic = topic.split("」", 1)[0]
    if "』" in topic:
        topic = topic.split("』", 1)[0]
    topic = topic.replace("「", "").replace("『", "").strip()
    topic = re.split(r"\s+", topic, maxsplit=1)[0].strip()
    if len(topic) > 24:
        topic = topic[:24].rstrip()
    return topic or headline[:28]


def tts_topic(topic: str, category: str) -> str:
    text = topic
    replacements = {
        "AI": "エーアイ",
        "SNS": "エスエヌエス",
        "NASA": "ナサ",
        "JAXA": "ジャクサ",
        "iPhone": "アイフォン",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    text = re.sub(r"[A-Za-z0-9]+", "", text)
    text = re.sub(r"[「」『』（）()]", "", text)
    text = re.sub(r"(が|は)?ここを見ると分かりやすい$", "", text)
    text = text.strip("、。 ")
    if len(text) > 16:
        if "エーアイ" in text or category == "科学":
            return "エーアイと新技術"
        if category == "宇宙":
            return "宇宙の新しい話題"
        if category == "人体":
            return "健康に関する話題"
        if category == "地球":
            return "気象に関する話題"
        return "今日の新しい話題"
    return text or "今日の新しい話題"


def infer_category(text: str) -> str:
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in text.lower() for keyword in keywords):
            return category
    return "科学"


def parse_pub_date(value: str) -> datetime:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_rss(xml_text: str) -> list[NewsItem]:
    root = ET.fromstring(xml_text)
    items: list[NewsItem] = []
    for node in root.findall(".//item"):
        raw_title = node.findtext("title", default="")
        link = node.findtext("link", default="")
        pub_date = node.findtext("pubDate", default="")
        source_node = node.find("{*}source")
        source = source_node.text.strip() if source_node is not None and source_node.text else ""
        title = clean_headline(raw_title)
        if not title or not link:
            continue
        items.append(
            NewsItem(
                title=title,
                link=link.strip(),
                published_at=parse_pub_date(pub_date),
                source=source,
            )
        )
    return items


def is_usable(item: NewsItem, cutoff: datetime) -> bool:
    if item.published_at < cutoff:
        return False
    text = f"{item.title} {item.source}"
    return not any(keyword in text for keyword in BLOCKED_KEYWORDS)


def build_feed_url(query: str) -> str:
    params = {
        "q": query,
        "hl": "ja",
        "gl": "JP",
        "ceid": "JP:ja",
    }
    return f"{RSS_BASE}?{urllib.parse.urlencode(params)}"


def fetch_rss(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "shorts-auto/1.0 (+https://github.com/sin1234567/shorts-auto)",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")


def build_fact(item: NewsItem) -> dict[str, str]:
    topic = short_topic(item.title)
    category = infer_category(item.title)
    spoken_topic = tts_topic(topic, category)
    title = f"今日話題の「{topic}」はここを見ると分かりやすい"
    body = (
        f"今日のニュースでは「{item.title}」が話題です。"
        "新しい話題は結論だけでなく、何が変わったのか、どんな仕組みが関係するのかを見ると理解しやすくなります。"
        "数字や公式発表も合わせて確認すると、話の流れをつかみやすいです。"
    )
    narration_title = spoken_topic
    narration_body = (
        "ニュースは見出しだけで判断せず、何が変わったのかを見ると分かりやすいです。"
        "仕組みと公式発表を合わせて確認すると、話の流れをつかみやすくなります。"
    )
    return {
        "title": title,
        "body": body,
        "category": category,
        "narration_title": narration_title,
        "narration_body": narration_body,
        "source_title": item.title,
        "source_url": item.link,
        "source_name": item.source,
        "published_at": item.published_at.isoformat(),
    }


def main() -> int:
    OUT.mkdir(exist_ok=True)
    query = os.environ.get("LATEST_TOPIC_QUERY", DEFAULT_QUERY).strip() or DEFAULT_QUERY
    max_age_hours = int(os.environ.get("LATEST_TOPIC_MAX_AGE_HOURS", "24"))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    url = os.environ.get("LATEST_TOPIC_RSS_URL", "").strip() or build_feed_url(query)

    try:
        xml_text = fetch_rss(url)
        items = parse_rss(xml_text)
    except Exception as exc:
        LATEST_FACT.unlink(missing_ok=True)
        print(f"latest topic fetch skipped: {exc}", file=sys.stderr)
        return 0

    candidates = [item for item in items if is_usable(item, cutoff)]
    candidates.sort(key=lambda item: item.published_at, reverse=True)
    if not candidates:
        LATEST_FACT.unlink(missing_ok=True)
        print("latest topic fetch skipped: no usable recent item")
        return 0

    fact = build_fact(candidates[0])
    with open(LATEST_FACT, "w", encoding="utf-8") as f:
        json.dump(fact, f, ensure_ascii=False, indent=2)

    print(f"latest topic selected: {fact['title']}")
    print(f"source: {fact['source_title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
