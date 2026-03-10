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
DURATION = 20
FPS = 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


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


facts = load_facts()
posted_titles = load_posted_titles()
unused_facts = [fact for fact in facts if fact["title"] not in posted_titles]

if not unused_facts:
    raise RuntimeError("No unused facts left. Add more rows to data/facts.csv.")

fact = random.choice(unused_facts)
title = fact["title"]
body = fact["body"]

print("selected:", title)

title_text = escape_drawtext(title)
body_text = escape_drawtext(body)

filter_graph = (
    "format=yuv420p,"
    "drawbox=x=60:y=120:w=960:h=1680:color=0x1e293bcc:t=fill,"
    "drawbox=x=60:y=120:w=960:h=18:color=0xf59e0b:t=fill,"
    f"drawtext=fontfile='{FONT}':text='豆知識':"
    "fontcolor=white:fontsize=72:x=(w-text_w)/2:y=220,"
    f"drawtext=fontfile='{FONT}':text='{title_text}':"
    "fontcolor=white:fontsize=96:line_spacing=20:x=(w-text_w)/2:y=760,"
    f"drawtext=fontfile='{FONT}':text='{body_text}':"
    "fontcolor=0xfdba74:fontsize=54:line_spacing=16:x=(w-text_w)/2:y=1080,"
    "drawtext=fontfile='{FONT}':text='雑学スライム':"
    "fontcolor=0x94a3b8:fontsize=42:x=(w-text_w)/2:y=1720"
)

subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x0f172a:s={WIDTH}x{HEIGHT}:d={DURATION}",
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
    "title": f"知らない人が多い {title} #shorts",
    "description": f"{body}\n\n毎日1本の雑学ショート\n#shorts #雑学 #豆知識",
    "tags": ["shorts", "雑学", "豆知識"],
    "source_title": title,
}

with open(OUT / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
