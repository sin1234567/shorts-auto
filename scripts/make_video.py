import csv
import json
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "facts.csv"
POSTED = ROOT / "data" / "posted_facts.txt"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
DURATION = 60
FPS = 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

THEMES = [
    {"bg": "0x0f172a", "card": "0x1e293bcc", "accent": "0xf59e0b"},
    {"bg": "0x111827", "card": "0x1f2937cc", "accent": "0x22c55e"},
    {"bg": "0x172554", "card": "0x1d4ed8cc", "accent": "0xf97316"},
]
HOOKS = [
    "今日は一分で話せる雑学を一つだけ紹介します。",
    "この話は知っていると誰かに話したくなるタイプです。",
    "意外と知られていませんが、かなり印象に残る話です。",
]
DETAILS = [
    "まず結論から言うと、",
    "最初にポイントだけ言うと、",
    "先にいちばん大事なところから言うと、",
]
REACTIONS = [
    "こういう話は知識として覚えやすいです。",
    "短いのに印象が強いので会話のネタにもなります。",
    "一回聞くと忘れにくい雑学の典型です。",
]
ENDINGS = [
    "こういう短く話せる雑学を毎日増やしていきます。",
    "次も一分で見られる雑学を出します。",
    "面白かったら次の雑学も見てください。",
]
TITLE_PATTERNS = [
    "知らない人が多い {title} #shorts",
    "一回聞くと覚える {title} #shorts",
    "話したくなる雑学 {title} #shorts",
]


def escape_drawtext(value: str) -> str:
    return (
        value.replace("\\", r"\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
        .replace("%", r"\%")
        .replace("\n", r"\n")
    )


def load_facts() -> list[dict[str, str]]:
    with open(DATA, encoding="utf-8") as f:
        return [
            {"title": row["title"].strip(), "body": row["body"].strip()}
            for row in csv.DictReader(f)
            if row.get("title") and row.get("body")
        ]


def load_posted_titles() -> set[str]:
    if not POSTED.exists():
        return set()

    with open(POSTED, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def wrap_text(text: str, width: int = 16) -> str:
    lines: list[str] = []
    current = ""
    for char in text:
        current += char
        if len(current) >= width and char not in "、。,. ":
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return "\n".join(lines)


def build_sections(title: str, body: str) -> list[str]:
    first = f"{random.choice(HOOKS)}\n今日のテーマは『{title}』です。"
    second = f"{random.choice(DETAILS)}{body}"
    third = (
        f"{title}は短い一文だけだと軽く見えますが、"
        f"{random.choice(REACTIONS)}"
    )
    fourth = (
        f"つまり今回のポイントは『{title}』です。\n"
        f"{random.choice(ENDINGS)}"
    )
    return [wrap_text(part) for part in [first, second, third, fourth]]


facts = load_facts()
posted_titles = load_posted_titles()
unused_facts = [fact for fact in facts if fact["title"] not in posted_titles]

if not unused_facts:
    raise RuntimeError("No unused facts left. Add more rows to data/facts.csv.")

fact = random.choice(unused_facts)
title = fact["title"]
body = fact["body"]
theme = random.choice(THEMES)
sections = build_sections(title, body)

print("selected:", title)

header_text = escape_drawtext("雑学スライム")
title_text = escape_drawtext(f"今日の雑学\n{title}")
section_filters = []
section_times = [(4, 15), (16, 29), (30, 43), (44, 57)]

for index, section in enumerate(sections):
    start, end = section_times[index]
    escaped = escape_drawtext(section)
    y = 720 if index < 2 else 760
    section_filters.append(
        f"drawtext=fontfile='{FONT}':text='{escaped}':"
        "fontcolor=0xf8fafc:fontsize=46:line_spacing=18:"
        f"x=90:y={y}:enable='between(t,{start},{end})'"
    )

filter_parts = [
    "format=yuv420p",
    f"drawbox=x=50:y=100:w=980:h=1720:color={theme['card']}:t=fill",
    f"drawbox=x=50:y=100:w=980:h=20:color={theme['accent']}:t=fill",
    f"drawtext=fontfile='{FONT}':text='{header_text}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=180",
    f"drawtext=fontfile='{FONT}':text='{title_text}':fontcolor=white:fontsize=74:line_spacing=18:x=90:y=360",
    *section_filters,
    "drawtext=fontfile='{FONT}':text='1分で見られる雑学ショート':fontcolor=0xfcd34d:fontsize=38:x=(w-text_w)/2:y=1680",
    "drawtext=fontfile='{FONT}':text='保存してあとで見返せます':fontcolor=0x94a3b8:fontsize=34:x=(w-text_w)/2:y=1760",
]
filter_graph = ",".join(filter_parts)

subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={theme['bg']}:s={WIDTH}x{HEIGHT}:d={DURATION}",
        "-vf",
        filter_graph,
        "-r",
        str(FPS),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(OUT / "short.mp4"),
    ],
    check=True,
)

script_body = "\n".join(sections)
metadata = {
    "title": random.choice(TITLE_PATTERNS).format(title=title),
    "description": (
        f"{script_body}\n\n"
        "毎日1本の雑学ショート\n"
        "#shorts #雑学 #豆知識"
    ),
    "tags": ["shorts", "雑学", "豆知識"],
    "source_title": title,
}

with open(OUT / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
