import csv
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import unicodedata
import uuid
from pathlib import Path

from pykakasi import kakasi

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "facts.csv"
POSTED = ROOT / "data" / "posted_facts.txt"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

WIDTH = 1080
HEIGHT = 1920
FPS = 30
IS_WINDOWS = os.name == "nt"
FONT = "C:/Windows/Fonts/NotoSansJP-Regular.ttf" if IS_WINDOWS else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
VOICE_DICT = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
VOICE_MODEL = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
VOICE_SPEED = "1.00"
LEADING_SILENCE_MS = 180
TRAILING_BUFFER_SEC = 0.8
EDGE_TTS_RATE = "+12%"
MAX_NARRATION_CHARS = 20

CATEGORY_KEYWORDS = {
    "動物": [
        "タコ", "コアラ", "キリン", "イルカ", "ミツバチ", "カタツムリ", "ワニ", "パンダ",
        "フクロウ", "ラクダ", "ラッコ", "カバ", "ナマケモノ", "ペンギン", "シロクマ", "サメ",
        "クラゲ", "ヒトデ", "カメレオン", "ハリネズミ", "モグラ", "カンガルー", "シマウマ",
        "チーター", "フラミンゴ", "アホウドリ", "カワウソ", "カエル", "カニ", "タツノオトシゴ",
        "ホタル", "アリクイ", "ゾウ", "クジャク", "サンゴ", "ウミガメ", "キツツキ", "カモノハシ",
        "シロアリ", "アザラシ", "ペリカン", "ミミズ", "トンボ",
    ],
    "植物": ["バナナ", "サボテン", "竹", "ひまわり", "イチゴ", "松ぼっくり", "樹木", "キノコ", "ワサビ", "玉ねぎ"],
    "宇宙": ["木星", "金星", "土星", "海王星", "月", "火星", "水星", "冥王星", "太陽", "流れ星", "北極星", "ブラックホール", "オーロラ"],
    "人体": ["皮膚", "爪", "髪", "人の骨", "心臓", "脳", "鼻", "舌", "血液", "筋肉", "まばたき", "くしゃみ", "睡眠", "髪の毛", "汗", "骨", "赤血球", "胃酸", "顔"],
    "地球": ["水", "ダイヤモンド", "稲妻", "音", "虹", "1円玉", "青信号", "地球", "富士山", "氷山", "砂漠", "火山灰", "地震", "朝焼け", "雲", "海", "雷", "風"],
    "科学": ["インク", "鉛筆", "鏡", "シャボン玉", "電子レンジ", "冷蔵庫", "ガラス", "紙飛行機", "磁石", "塩", "泡", "世界地図"],
}

THEMES = [
    {"bg": "0x0f172a", "card": "0x1e293bcc", "accent": "0xf59e0b"},
    {"bg": "0x111827", "card": "0x1f2937cc", "accent": "0x22c55e"},
    {"bg": "0x172554", "card": "0x1d4ed8cc", "accent": "0xf97316"},
]

HOOK_PATTERNS = [
    "今日は、",
    "今回は、",
    "ひとつだけ言うと、",
]
OPENERS = [
    "今日は一分で聞ける雑学を一つだけ、できるだけ分かりやすく話します。",
    "今回は短いのに会話のネタになりやすい雑学を、一つだけしっかり話します。",
    "この話は知っていると誰かに言いたくなるので、短く整理して紹介します。",
]
ANALYSIS_LINES = [
    "理由まで分かると覚えやすいです。",
    "ここを知ると見方が変わります。",
    "仕組みまで分かると印象に残ります。",
]
ENDINGS = [
    "覚えておくと面白いです。",
    "知っていると見方が変わります。",
    "これだけでも十分ネタになります。",
]
TITLE_PATTERNS = [
    "意外と知られていない {title} #shorts",
    "一分でわかる雑学 {title} #shorts",
    "知ってると話したくなる {title} #shorts",
]
SUMMARY_PATTERNS = [
    "{title}は一言で終わらない話です。",
    "{title}は理由まで知ると面白いです。",
]
HEADER_PATTERNS = [
    "雑学ショート",
    "1分で雑学",
    "今日の豆知識",
]
FOOTER_PATTERNS = [
    "1分で聞ける雑学ショート",
    "保存してあとで話せる雑学",
    "短く覚える豆知識",
]
SUBFOOTER_PATTERNS = [
    "雑学チャンネル",
    "毎日1本更新",
    "聞き流し雑学",
]
TAG_SETS = [
    ["shorts", "雑学", "豆知識"],
    ["shorts", "雑学", "会話ネタ"],
    ["shorts", "豆知識", "学び"],
]

CATEGORY_OPENERS = {
    "動物": ["今日は動物の体や行動に関する面白い話を取り上げます。", "今回は生き物の雑学を一つだけ、分かりやすく話します。"],
    "植物": ["今日は植物の見方が少し変わる雑学を一つ紹介します。", "身近な植物でも仕組みを知ると印象が変わります。"],
    "宇宙": ["今回は宇宙のスケールを感じやすい雑学を一つだけ話します。", "宇宙の話は短くても一気に視点が広がります。"],
    "人体": ["今日は人の体について、意外と知られていない基本を一つ話します。", "人体の雑学は身近だからこそ覚えやすいです。"],
    "地球": ["今回は地球や自然現象の見え方が変わる雑学を取り上げます。", "毎日見ている自然の中にも意外な仕組みがあります。"],
    "科学": ["今日は身近な現象を科学っぽく見直せる雑学を一つ話します。", "理屈が分かると一気に面白くなるタイプの雑学です。"],
}
CATEGORY_ANALYSIS = {
    "動物": ["体のつくりと暮らし方がつながっていると覚えやすいです。", "動物の雑学は行動の理由まで知ると印象が残ります。"],
    "植物": ["見た目だけでなく仕組みまで押さえると記憶に残ります。", "植物の話は身近なのに意外性が強いです。"],
    "宇宙": ["数字や距離の感覚まで想像すると、一気にスケールが伝わります。", "宇宙の雑学は日常と離れているぶん印象が強いです。"],
    "人体": ["自分の体の話なので、その場でイメージしやすいのが強みです。", "人体の雑学は今日から見方を変えられるのが面白いです。"],
    "地球": ["自然現象の理由が分かると、普段の景色の見え方まで変わります。", "地球の話は知識だけでなく観察の視点も増やしてくれます。"],
    "科学": ["身近な道具や現象に理屈があると分かると印象がかなり変わります。", "科学の雑学は実生活に結びつくので覚えやすいです。"],
}
CATEGORY_TAGS = {
    "動物": ["shorts", "雑学", "動物"],
    "植物": ["shorts", "雑学", "植物"],
    "宇宙": ["shorts", "雑学", "宇宙"],
    "人体": ["shorts", "雑学", "人体"],
    "地球": ["shorts", "雑学", "自然"],
    "科学": ["shorts", "雑学", "科学"],
}


def escape_path(value: str) -> str:
    return value.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def resolve_binary(name: str) -> str:
    resolved = shutil.which(name)
    if resolved:
        return resolved
    if not IS_WINDOWS:
        return name

    local_appdata = os.environ.get("LOCALAPPDATA")
    if not local_appdata:
        return name

    link_path = Path(local_appdata) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
    try:
        if link_path.exists():
            return str(link_path)
    except PermissionError:
        pass

    packages_root = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
    patterns = [
        f"**/{name}.exe",
        f"**/bin/{name}.exe",
    ]
    for pattern in patterns:
        try:
            candidates = packages_root.glob(pattern)
        except PermissionError:
            continue
        for candidate in candidates:
            try:
                if candidate.is_file():
                    return str(candidate)
            except PermissionError:
                continue
    return name


FFMPEG = resolve_binary("ffmpeg")
FFPROBE = resolve_binary("ffprobe")
KAKASI = kakasi()


def load_facts() -> list[dict[str, str]]:
    with open(DATA, encoding="utf-8") as f:
        return [
            {"title": row["title"].strip(), "body": row["body"].strip()}
            for row in csv.DictReader(f)
            if row.get("title") and row.get("body")
        ]


def load_posted_history() -> list[str]:
    if not POSTED.exists():
        return []
    with open(POSTED, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_posted_titles() -> set[str]:
    return set(load_posted_history())


def infer_category(title: str, body: str) -> str:
    text = f"{title} {body}"
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "科学"


def normalize_similarity_text(text: str) -> str:
    return "".join(char.lower() for char in text if char.isalnum())


def char_ngrams(text: str, size: int = 2) -> set[str]:
    normalized = normalize_similarity_text(text)
    if not normalized:
        return set()
    if len(normalized) <= size:
        return {normalized}
    return {normalized[index : index + size] for index in range(len(normalized) - size + 1)}


def similarity_score(left: str, right: str) -> float:
    left_ngrams = char_ngrams(left)
    right_ngrams = char_ngrams(right)
    if not left_ngrams or not right_ngrams:
        return 0.0
    return len(left_ngrams & right_ngrams) / len(left_ngrams | right_ngrams)


def remove_similar_lines(lines: list[str], threshold: float = 0.72) -> list[str]:
    unique_lines: list[str] = []
    for line in lines:
        if not line.strip():
            continue
        if any(similarity_score(line, existing) >= threshold for existing in unique_lines):
            continue
        unique_lines.append(line)
    return unique_lines


def choose_fact(
    facts: list[dict[str, str]],
    posted_titles: set[str],
    posted_history: list[str],
) -> dict[str, str]:
    enriched = [{**fact, "category": infer_category(fact["title"], fact["body"])} for fact in facts]
    forced_title = os.environ.get("FACT_TITLE", "").strip()
    if forced_title:
        for fact in enriched:
            if fact["title"] == forced_title:
                if fact["title"] in posted_titles:
                    raise RuntimeError(f"FACT_TITLE is already posted: {forced_title}")
                return fact
        raise RuntimeError(f"FACT_TITLE not found in facts.csv: {forced_title}")

    unused = [fact for fact in enriched if fact["title"] not in posted_titles]
    if not unused:
        raise RuntimeError("No unused facts left. Add more rows to data/facts.csv.")

    posted_counts = {key: 0 for key in CATEGORY_KEYWORDS}
    for fact in enriched:
        if fact["title"] in posted_titles:
            posted_counts[fact["category"]] = posted_counts.get(fact["category"], 0) + 1

    min_count = min(posted_counts.get(fact["category"], 0) for fact in unused)
    candidates = [fact for fact in unused if posted_counts.get(fact["category"], 0) == min_count]
    recent_titles = posted_history[-8:]
    if not recent_titles:
        return random.choice(candidates)

    scored_candidates = []
    for fact in candidates:
        similarity = max(similarity_score(fact["title"], recent_title) for recent_title in recent_titles)
        scored_candidates.append((similarity, random.random(), fact))
    scored_candidates.sort(key=lambda item: (item[0], item[1]))
    return scored_candidates[0][2]


def wrap_text(text: str, width: int = 16) -> str:
    lines: list[str] = []
    remaining = text.strip()
    break_tokens = ("という", "ので", "から", "ため", "けれど", "ですが", "でも", "では", "には", "とは", "を", "が", "に", "で", "と", "は")

    while remaining:
        if len(remaining) <= width:
            lines.append(remaining)
            break

        split_index = -1
        for mark in ("、", "。", " ", ","):
            mark_index = remaining.rfind(mark, 0, width + 1)
            if mark_index > split_index:
                split_index = mark_index + 1

        if split_index <= 0:
            for token in break_tokens:
                token_index = remaining.rfind(token, 0, width + 1)
                if token_index > 1 and token_index > split_index:
                    split_index = token_index

        if split_index <= 0:
            split_index = width

        line = remaining[:split_index].strip()
        if not line:
            break
        lines.append(line)
        remaining = remaining[split_index:].strip()
    return "\n".join(lines)


def write_display_text(path: Path, text: str) -> None:
    path.write_text(normalize_display_text(text), encoding="utf-8", newline="\n")


def build_text_filters(
    stem: str,
    text: str,
    font_path: str,
    *,
    fontcolor: str,
    fontsize: int,
    x_expr: str,
    y_start: int,
    line_gap: int,
    enable: str | None = None,
    extra: str = "",
) -> list[str]:
    filters: list[str] = []
    lines = [line for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        line_file = OUT / f"{stem}_{index + 1}.txt"
        write_display_text(line_file, line)
        line_path = escape_path(str(line_file))
        parts = [
            f"drawtext=fontfile='{font_path}':textfile='{line_path}':fontcolor={fontcolor}:fontsize={fontsize}",
        ]
        if extra:
            parts.append(extra)
        parts.append(f"x={x_expr}")
        parts.append(f"y={y_start + index * line_gap}")
        if enable:
            parts.append(f"enable='{enable}'")
        filters.append(":".join(parts))
    return filters


def normalize_narration_line(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    normalized = " ".join(normalized.split())
    normalized = re.sub(r"[~〜]+", "", normalized)
    normalized = re.sub(r"ー{2,}", "ー", normalized)
    normalized = re.sub(r"(?:\.{3,}|…{2,}|・{3,})", "。", normalized)

    filler_replacements = {
        "\u305d\u3046\u3067\u3059\u306d": "\u305d\u3046\u3067\u3059\u306d\u3002\u610f\u5916\u3067\u3059\u3002",
        "\u306a\u308b\u307b\u3069": "\u306a\u308b\u307b\u3069\u3002\u9762\u767d\u3044\u3067\u3059\u3002",
        "\u305f\u3057\u304b\u306b": "\u305f\u3057\u304b\u306b\u3002\u6c17\u306b\u306a\u308a\u307e\u3059\u3002",
    }
    normalized = filler_replacements.get(normalized, normalized)

    normalized = normalized.strip("、。！？ ")
    if not normalized:
        return ""
    if normalized[-1] not in "。！？":
        normalized += "。"
    return normalized


def split_narration_line(text: str, max_chars: int = MAX_NARRATION_CHARS) -> list[str]:
    normalized = normalize_narration_line(text)
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]

    segments: list[str] = []
    current = ""
    pending_break = False
    soft_break_words = (
        "\u3067\u3082",
        "\u305d\u3057\u3066",
        "\u305f\u3060",
        "\u5b9f\u306f",
        "\u3064\u307e\u308a",
        "\u306a\u306e\u3067",
    )

    for char in normalized:
        current += char
        if char in "。！？、":
            pending_break = True

        if len(current) < max_chars:
            if pending_break and len(current) >= max(8, max_chars // 2):
                segments.append(current.strip())
                current = ""
                pending_break = False
            continue

        split_index = -1
        for word in soft_break_words:
            word_index = current.rfind(word)
            if 0 < word_index > split_index:
                split_index = word_index
        if split_index > 0:
            head = current[:split_index].strip("、。！？ ")
            tail = current[split_index:].strip()
            if head:
                if head[-1] not in "。！？":
                    head += "。"
                segments.append(head)
            current = tail
        else:
            cut = current.rstrip("、")
            if cut:
                segments.append(cut if cut[-1] in "。！？" else f"{cut}。")
            current = ""
        pending_break = False

    tail = current.strip()
    if tail:
        if tail[-1] not in "。！？":
            tail += "。"
        segments.append(tail)
    return [segment for segment in segments if segment]


def build_narration_lines(title: str, body: str, category: str) -> list[str]:
    body_lines = [segment for segment in re.split(r"(?<=[。！？])", normalize_narration_line(body)) if segment.strip()]
    detail_line = body_lines[1].strip() if len(body_lines) > 1 else ""
    analysis_line = random.choice(CATEGORY_ANALYSIS.get(category, ANALYSIS_LINES))
    base_lines = [
        build_hook_line(title),
        body_lines[0].strip() if body_lines else normalize_narration_line(body),
        detail_line or analysis_line,
        "" if detail_line else analysis_line,
        random.choice(ENDINGS),
    ]
    normalized_lines = [normalize_narration_line(line) for line in base_lines]
    return remove_similar_lines([line for line in normalized_lines if line])


def build_script(title: str, body: str, category: str) -> list[str]:
    hook = build_hook_line(title)
    body_lines = [segment.strip() for segment in re.split(r"(?<=[。！？])", normalize_narration_line(body)) if segment.strip()]
    closing = build_closing_line(title, category)
    lines: list[str] = []
    lines.extend(split_narration_line(hook))
    if body_lines:
        lines.extend(split_narration_line(body_lines[0]))
    if len(body_lines) > 1:
        lines.extend(split_narration_line(body_lines[1]))
    lines.extend(split_narration_line(closing))
    return remove_similar_lines(lines)


def build_narration_text(title: str, body: str, category: str) -> str:
    return sanitize_tts_text("".join(build_narration_lines(title, body, category)))


def build_hook_line(title: str) -> str:
    opener = random.choice(HOOK_PATTERNS)
    cleaned_title = title.strip("。 ")
    if any(token in cleaned_title for token in ("ではない", "違う", "勝手に", "ただの")):
        return f"{cleaned_title}。"
    short_topic = cleaned_title
    for marker in ("は", "が"):
        if marker in cleaned_title:
            short_topic = cleaned_title.split(marker, 1)[0]
            break
    short_topic = short_topic.strip("、。 ")
    if 0 < len(short_topic) <= 14:
        return f"{opener}{short_topic}の話です。"
    return f"{opener}{cleaned_title}という話です。"


def build_closing_line(title: str, category: str) -> str:
    if any(token in title for token in ("ではない", "違う", "ただの", "勝手に")):
        return "思い込みと違うところが面白いです。"
    category_lines = CATEGORY_ANALYSIS.get(category, ANALYSIS_LINES)
    short_line = random.choice(category_lines)
    short_line = short_line.replace("日常の見え方に結びつくと", "").replace("今日から", "").strip()
    return short_line or random.choice(ENDINGS)


def has_kanji(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def to_tts_text(text: str) -> str:
    parts: list[str] = []
    for item in KAKASI.convert(text):
        original = item["orig"]
        hira = item["hira"]
        if has_kanji(original) and len(original) <= 2:
            parts.append(hira)
        else:
            parts.append(original)
    return "".join(parts)


def normalize_display_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).replace("\ufffd", "")
    return "".join(char for char in normalized if char == "\n" or unicodedata.category(char)[0] != "C")


def sanitize_tts_text(text: str) -> str:
    normalized = " ".join(text.split())
    normalized = normalized.replace("。 ", "。")
    normalized = normalized.replace("! ", "。")
    normalized = normalized.replace("！", "。")
    normalized = normalized.replace("? ", "。")
    normalized = normalized.replace("？", "。")
    while "。。" in normalized:
        normalized = normalized.replace("。。", "。")
    while "、、" in normalized:
        normalized = normalized.replace("、、", "、")
    normalized = normalized.strip("、。 ")
    if normalized:
        return f"{normalized}。"
    return normalized


def split_tts_sentences(text: str) -> list[str]:
    normalized = sanitize_tts_text(text)
    if not normalized:
        return []

    sentence_units: list[str] = []
    current = ""
    for char in normalized:
        current += char
        if char in "。！？":
            chunk = current.strip()
            if chunk:
                sentence_units.append(chunk)
            current = ""
    tail = current.strip()
    if tail:
        sentence_units.append(tail)

    soft_break_words = ("でも", "そして", "ただ", "実は", "つまり", "なので", "ですが", "ため", "から")
    chunks: list[str] = []
    for sentence in sentence_units:
        remaining = sentence.strip()
        while remaining:
            if len(remaining) <= 26:
                chunks.append(remaining)
                break

            split_index = -1
            for mark in "、":
                mark_index = remaining.rfind(mark, 0, 26)
                if mark_index > split_index:
                    split_index = mark_index + 1

            if split_index <= 0:
                for word in soft_break_words:
                    word_index = remaining.rfind(word, 0, 26)
                    if word_index > 0 and word_index + len(word) > split_index:
                        split_index = word_index + len(word)

            if split_index <= 0:
                split_index = -1
                for word in soft_break_words:
                    word_index = remaining.find(word, 26)
                    if 26 < word_index <= 40:
                        split_index = word_index
                        break

            if split_index <= 0:
                chunks.append(remaining)
                break

            chunk = remaining[:split_index].strip()
            if not chunk:
                break
            chunks.append(chunk)
            remaining = remaining[split_index:].strip()

    return [chunk for chunk in chunks if chunk]


def synthesize_voice_linux(text: str, out_path: Path) -> None:
    sentences = split_tts_sentences(text)
    if not sentences:
        raise RuntimeError("No text available for Linux TTS synthesis.")

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        concat_list = tmp_dir / "concat.txt"
        concat_lines: list[str] = []

        for index, sentence in enumerate(sentences, start=1):
            part_path = tmp_dir / f"part_{index:03d}.wav"
            subprocess.run(
                [
                    "open_jtalk",
                    "-x",
                    VOICE_DICT,
                    "-m",
                    VOICE_MODEL,
                    "-r",
                    VOICE_SPEED,
                    "-ow",
                    str(part_path),
                ],
                input=sentence.encode("utf-8"),
                check=True,
            )
            concat_lines.append(f"file '{part_path.as_posix()}'")

        concat_list.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(out_path),
            ],
            check=True,
        )


def synthesize_voice_windows(text: str, out_path: Path) -> None:
    sentences = split_tts_sentences(text)
    if not sentences:
        raise RuntimeError("No text available for Windows TTS synthesis.")

    tmp_dir = OUT / f"_work_{uuid.uuid4().hex}"
    tmp_dir.mkdir(parents=True, exist_ok=False)
    try:
        concat_list = tmp_dir / "concat.txt"
        concat_lines: list[str] = []

        for index, sentence in enumerate(sentences, start=1):
            part_path = tmp_dir / f"part_{index:03d}.mp3"
            subprocess.run(
                [
                    "python",
                    "-m",
                    "edge_tts",
                    "--voice",
                    "ja-JP-NanamiNeural",
                    "--rate",
                    EDGE_TTS_RATE,
                    "--text",
                    sentence,
                    "--write-media",
                    str(part_path),
                ],
                check=True,
            )
            concat_lines.append(f"file '{part_path.as_posix()}'")

        concat_list.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(out_path),
            ],
            check=True,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def synthesize_voice(text: str, out_path: Path) -> None:
    if IS_WINDOWS:
        synthesize_voice_windows(text, out_path)
        return

    synthesize_voice_linux(text, out_path)


def normalize_voice(in_audio: Path, out_wav: Path) -> None:
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(in_audio),
            "-vn",
            "-af",
            "aformat=sample_fmts=s16:sample_rates=48000:channel_layouts=mono",
            "-c:a",
            "pcm_s16le",
            str(out_wav),
        ],
        check=True,
    )


def add_leading_silence(in_wav: Path, out_wav: Path, delay_ms: int = LEADING_SILENCE_MS) -> None:
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(in_wav),
            "-af",
            f"adelay={delay_ms}",
            "-c:a",
            "pcm_s16le",
            str(out_wav),
        ],
        check=True,
    )


def trim_trailing_silence(in_wav: Path, out_wav: Path) -> None:
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(in_wav),
            "-af",
            "areverse,silenceremove=start_periods=1:start_duration=0.55:start_threshold=-42dB,areverse",
            "-c:a",
            "pcm_s16le",
            str(out_wav),
        ],
        check=True,
    )


def add_trailing_silence(in_wav: Path, out_wav: Path, pad_sec: float = 0.75) -> None:
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(in_wav),
            "-af",
            f"apad=pad_dur={pad_sec}",
            "-c:a",
            "pcm_s16le",
            str(out_wav),
        ],
        check=True,
    )


def get_media_duration(path: Path) -> float:
    result = subprocess.run(
        [
            FFPROBE,
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


def calculate_video_duration(audio_duration: float) -> float:
    return min(35.0, audio_duration + TRAILING_BUFFER_SEC)


def get_audio_stream_info(path: Path) -> dict[str, str]:
    result = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        raise RuntimeError(f"No audio stream found in {path}")
    return streams[0]


facts = load_facts()
posted_history = load_posted_history()
posted_titles = load_posted_titles()
fact = choose_fact(facts, posted_titles, posted_history)
title = fact["title"]
body = fact["body"]
category = fact["category"]
theme = random.choice(THEMES)
sections = build_script(title, body, category)
if IS_WINDOWS:
    sections = [title, body]
narration_text = build_narration_text(title, body, category)
tts_text = sanitize_tts_text(to_tts_text(narration_text))
tts_input_text = sanitize_tts_text(narration_text) if IS_WINDOWS else tts_text

print("selected:", title)

raw_voice_wav = OUT / "voice_raw.wav"
raw_voice_mp3 = OUT / "voice_raw.mp3"
voice_wav = OUT / "voice.wav"
voice_padded_wav = OUT / "voice_padded.wav"
voice_trimmed_wav = OUT / "voice_trimmed.wav"
voice_final_wav = OUT / "voice_final.wav"
synthesize_voice(tts_input_text, raw_voice_mp3 if IS_WINDOWS else raw_voice_wav)
normalize_voice(raw_voice_mp3 if IS_WINDOWS else raw_voice_wav, voice_wav)
add_leading_silence(voice_wav, voice_padded_wav)
trim_trailing_silence(voice_padded_wav, voice_trimmed_wav)
add_trailing_silence(voice_trimmed_wav, voice_final_wav)
audio_info = get_audio_stream_info(voice_final_wav)
if audio_info.get("sample_rate") != "48000" or audio_info.get("channels") != 1:
    raise RuntimeError(f"Unexpected normalized audio format: {audio_info}")
audio_duration = get_media_duration(voice_final_wav)
video_duration = calculate_video_duration(audio_duration)

header_file = OUT / "header.txt"
title_file = OUT / "title.txt"
footer_file = OUT / "footer.txt"
subfooter_file = OUT / "subfooter.txt"
narration_tts_file = OUT / "narration_tts.txt"

write_display_text(header_file, random.choice(HEADER_PATTERNS))
write_display_text(title_file, wrap_text(title, 12))
write_display_text(footer_file, random.choice(FOOTER_PATTERNS))
write_display_text(subfooter_file, random.choice(SUBFOOTER_PATTERNS))
write_display_text(narration_tts_file, tts_input_text)

header_path = escape_path(str(header_file))
footer_path = escape_path(str(footer_file))
subfooter_path = escape_path(str(subfooter_file))
font_path = escape_path(FONT)

section_filters = []
start_time = min(2.2, max(0.9, video_duration * 0.1))
usable_time = max(2.4, video_duration - start_time - TRAILING_BUFFER_SEC)
segment = usable_time / len(sections)

for index, section in enumerate(sections):
    start = start_time + index * segment
    end = start_time + (index + 1) * segment - 0.25
    condensed = wrap_text(section, 14).splitlines()[:3]
    section_filters.extend(
        build_text_filters(
            f"section_{index + 1}",
            "\n".join(condensed),
            font_path,
            fontcolor="0xf8fafc",
            fontsize=44,
            x_expr="90",
            y_start=980,
            line_gap=58,
            enable=f"between(t,{start:.2f},{end:.2f})",
            extra="line_spacing=14",
        )
    )

subtitle_filters = []
subtitle_chunks = split_tts_sentences(tts_input_text)
subtitle_start = LEADING_SILENCE_MS / 1000
subtitle_duration = max(1.2, audio_duration - subtitle_start)
subtitle_segment = subtitle_duration / max(1, len(subtitle_chunks))

for index, chunk in enumerate(subtitle_chunks):
    subtitle_text = "\n".join(wrap_text(chunk, 16).splitlines()[:2])
    start = subtitle_start + index * subtitle_segment
    end = min(video_duration - 0.1, subtitle_start + (index + 1) * subtitle_segment)
    subtitle_filters.append(
        f"drawbox=x=70:y=1390:w=940:h=250:color=0x020617c8:t=fill:enable='between(t,{start:.2f},{end:.2f})'"
    )
    subtitle_filters.append(
        f"drawbox=x=70:y=1390:w=940:h=4:color={theme['accent']}:t=fill:enable='between(t,{start:.2f},{end:.2f})'"
    )
    subtitle_filters.extend(
        build_text_filters(
            f"subtitle_{index + 1:02d}",
            subtitle_text,
            font_path,
            fontcolor="white",
            fontsize=58,
            x_expr="(w-text_w)/2",
            y_start=1466,
            line_gap=78,
            enable=f"between(t,{start:.2f},{end:.2f})",
            extra="line_spacing=20:borderw=2.5:bordercolor=0x020617",
        )
    )

filter_parts = [
    "format=yuv420p",
    f"drawbox=x=50:y=100:w=980:h=1720:color={theme['card']}:t=fill",
    f"drawbox=x=50:y=100:w=980:h=20:color={theme['accent']}:t=fill",
    f"drawtext=fontfile='{font_path}':textfile='{header_path}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=180",
    *build_text_filters(
        "title",
        wrap_text(title, 12),
        font_path,
        fontcolor="white",
        fontsize=74,
        x_expr="90",
        y_start=360,
        line_gap=92,
        extra="line_spacing=18",
    ),
    *section_filters,
    *subtitle_filters,
    f"drawtext=fontfile='{font_path}':textfile='{footer_path}':fontcolor=0xfcd34d:fontsize=36:x=(w-text_w)/2:y=1680",
    f"drawtext=fontfile='{font_path}':textfile='{subfooter_path}':fontcolor=0x94a3b8:fontsize=32:x=(w-text_w)/2:y=1760",
]
filter_graph = ",".join(filter_parts)

subprocess.run(
    [
        FFMPEG,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={theme['bg']}:s={WIDTH}x{HEIGHT}:r={FPS}:d={video_duration}",
        "-i",
        str(voice_final_wav),
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
        "-t",
        f"{video_duration:.2f}",
        str(OUT / "short.mp4"),
    ],
    check=True,
)

metadata = {
    "title": random.choice(TITLE_PATTERNS).format(title=title),
    "description": f"{narration_text}\n\n毎日1本の雑学ショート\n#" + " #".join(CATEGORY_TAGS.get(category, random.choice(TAG_SETS))),
    "tags": CATEGORY_TAGS.get(category, random.choice(TAG_SETS)),
    "source_title": title,
    "category": category,
}

with open(OUT / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print("preview audio:", voice_trimmed_wav)
print("preview text:", narration_tts_file)
