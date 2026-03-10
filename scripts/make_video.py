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
FPS = 30
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
VOICE_DICT = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
VOICE_MODEL = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"

THEMES = [
    {"bg": "0x0f172a", "card": "0x1e293bcc", "accent": "0xf59e0b"},
    {"bg": "0x111827", "card": "0x1f2937cc", "accent": "0x22c55e"},
    {"bg": "0x172554", "card": "0x1d4ed8cc", "accent": "0xf97316"},
]
OPENERS = [
    "今日は一分で聞ける雑学を一つだけ、できるだけ分かりやすく話します。",
    "今回は短いのに会話のネタになりやすい雑学を、一つだけしっかり話します。",
    "この話は知っていると誰かに話したくなるので、最後まで聞いてみてください。",
]
BRIDGES = [
    "ここで大事なのは、ただ珍しいだけではなく、理由まで知ると覚えやすいことです。",
    "一文だけで終わる話に見えますが、背景を知ると印象がかなり変わります。",
    "短い雑学でも、意味が分かると急に記憶に残りやすくなります。",
]
ENDINGS = [
    "こんな感じで、一分で覚えられる雑学を毎日一本ずつ出していきます。",
    "面白かったら保存して、あとで誰かに話してみてください。",
    "次も短く話せる雑学を出すので、気になる人はまた見てください。",
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


def build_script(title: str, body: str) -> list[str]:
    return [
        f"{random.choice(OPENERS)} 今日のテーマは、{title}です。",
        f"まず結論から言うと、{body}",
        f"{random.choice(BRIDGES)} だから、この雑学は短いのに強く印象に残ります。",
        f"もう一度まとめると、{title}という話でした。{random.choice(ENDINGS)}",
    ]


def synthesize_voice(text: str, out_wav: Path) -> None:
    subprocess.run(
        [
            "open_jtalk",
            "-x",
            VOICE_DICT,
            "-m",
            VOICE_MODEL,
            "-r",
            "0.92",
            "-ow",
            str(out_wav),
        ],
        input=text.encode("utf-8"),
        check=True,
    )


def get_media_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


facts = load_facts()
posted_titles = load_posted_titles()
unused_facts = [fact for fact in facts if fact["title"] not in posted_titles]

if not unused_facts:
    raise RuntimeError("No unused facts left. Add more rows to data/facts.csv.")

fact = random.choice(unused_facts)
title = fact["title"]
body = fact["body"]
theme = random.choice(THEMES)
sections = build_script(title, body)
narration_text = " ".join(sections)

print("selected:", title)

voice_wav = OUT / "voice.wav"
synthesize_voice(narration_text, voice_wav)
audio_duration = get_media_duration(voice_wav)
video_duration = max(55.0, min(59.0, audio_duration + 1.2))

header_text = escape_drawtext("雑学スライム")
title_text = escape_drawtext(wrap_text(f"今日の雑学\n{title}", 12))

section_filters = []
start_time = 5.0
usable_time = max(40.0, video_duration - 10.0)
segment = usable_time / len(sections)

for index, section in enumerate(sections):
    start = start_time + index * segment
    end = start_time + (index + 1) * segment - 0.5
    escaped = escape_drawtext(wrap_text(section, 17))
    y = 760
    section_filters.append(
        f"drawtext=fontfile='{FONT}':text='{escaped}':"
        "fontcolor=0xf8fafc:fontsize=46:line_spacing=18:"
        f"x=90:y={y}:enable='between(t,{start:.2f},{end:.2f})'"
    )

filter_parts = [
    "format=yuv420p",
    f"drawbox=x=50:y=100:w=980:h=1720:color={theme['card']}:t=fill",
    f"drawbox=x=50:y=100:w=980:h=20:color={theme['accent']}:t=fill",
    f"drawtext=fontfile='{FONT}':text='{header_text}':fontcolor=white:fontsize=64:x=(w-text_w)/2:y=180",
    f"drawtext=fontfile='{FONT}':text='{title_text}':fontcolor=white:fontsize=72:line_spacing=20:x=90:y=360",
    *section_filters,
    "drawtext=fontfile='{FONT}':text='1分で聞ける雑学ショート':fontcolor=0xfcd34d:fontsize=38:x=(w-text_w)/2:y=1680",
    "drawtext=fontfile='{FONT}':text='雑学スライム':fontcolor=0x94a3b8:fontsize=34:x=(w-text_w)/2:y=1760",
]
filter_graph = ",".join(filter_parts)

subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={theme['bg']}:s={WIDTH}x{HEIGHT}:d={video_duration}",
        "-i",
        str(voice_wav),
        "-vf",
        filter_graph,
        "-r",
        str(FPS),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        str(OUT / "short.mp4"),
    ],
    check=True,
)

metadata = {
    "title": random.choice(TITLE_PATTERNS).format(title=title),
    "description": (
        f"{narration_text}\n\n"
        "毎日1本の雑学ショート\n"
        "#shorts #雑学 #豆知識"
    ),
    "tags": ["shorts", "雑学", "豆知識"],
    "source_title": title,
}

with open(OUT / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
