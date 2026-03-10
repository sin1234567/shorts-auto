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
DURATION = 36
FPS = 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

THEMES = [
    {"bg": "0x0f172a", "card": "0x1e293bcc", "accent": "0xf59e0b"},
    {"bg": "0x111827", "card": "0x1f2937cc", "accent": "0x22c55e"},
    {"bg": "0x172554", "card": "0x1d4ed8cc", "accent": "0xf97316"},
]
HOOKS = [
    "知ってたら誰かに話したくなる雑学です。",
    "この話、意外と知らない人が多いです。",
    "たぶん一回聞くと忘れません。",
]
MIDDLES = [
    "ポイントだけ短く話します。",
    "まず結論からいきます。",
    "無駄なく一気にいきます。",
]
CLOSERS = [
    "こういう雑学、まだまだあります。",
    "次も一分で話せるネタを出します。",
    "知らなかったら保存しておいてください。",
]
TITLE_PATTERNS = [
    "知らない人が多い {title} #shorts",
    "一回聞くと忘れない {title} #shorts",
    "話したくなる雑学 {title} #shorts",
]


def escape_drawtext(value: str) -> str:
    return (
        value.replace("\\", r"\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
        .replace("%", r"\%")
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


def build_script(title: str, body: str) -> tuple[str, str, str]:
    intro = random.choice(HOOKS)
    middle = random.choice(MIDDLES)
    closer = random.choice(CLOSERS)
    script_title = f"今日の雑学: {title}"
    script_body = f"{intro} {middle} {body}"
    script_footer = closer
    return script_title, script_body, script_footer


facts = load_facts()
posted_titles = load_posted_titles()
unused_facts = [fact for fact in facts if fact["title"] not in posted_titles]

if not unused_facts:
    raise RuntimeError("No unused facts left. Add more rows to data/facts.csv.")

fact = random.choice(unused_facts)
title = fact["title"]
body = fact["body"]
theme = random.choice(THEMES)

print("selected:", title)

script_title, script_body, script_footer = build_script(title, body)

title_text = escape_drawtext(script_title)
body_text = escape_drawtext(script_body)
footer_text = escape_drawtext(script_footer)

filter_graph = (
    "format=yuv420p,"
    f"drawbox=x=50:y=100:w=980:h=1720:color={theme['card']}:t=fill,"
    f"drawbox=x=50:y=100:w=980:h=20:color={theme['accent']}:t=fill,"
    f"drawtext=fontfile='{FONT}':text='雑学スライム':"
    "fontcolor=white:fontsize=64:x=(w-text_w)/2:y=180,"
    f"drawtext=fontfile='{FONT}':text='{title_text}':"
    "fontcolor=white:fontsize=76:line_spacing=18:x=90:y=420:"
    "box=0,"
    f"drawtext=fontfile='{FONT}':text='{body_text}':"
    "fontcolor=0xf8fafc:fontsize=48:line_spacing=20:x=90:y=760:"
    "box=0,"
    f"drawtext=fontfile='{FONT}':text='{footer_text}':"
    "fontcolor=0xfcd34d:fontsize=42:line_spacing=16:x=90:y=1450,"
    "drawtext=fontfile='{FONT}':text='チャンネル登録と保存もどうぞ':"
    "fontcolor=0x94a3b8:fontsize=36:x=(w-text_w)/2:y=1750"
)

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

metadata = {
    "title": random.choice(TITLE_PATTERNS).format(title=title),
    "description": (
        f"{script_body}\n\n"
        f"{script_footer}\n\n"
        "毎日1本の雑学ショート\n"
        "#shorts #雑学 #豆知識"
    ),
    "tags": ["shorts", "雑学", "豆知識"],
    "source_title": title,
}

with open(OUT / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
