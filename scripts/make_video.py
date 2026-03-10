import csv
import json
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "facts.csv"
VIDEO = ROOT / "assets" / "slime.mp4"
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)

facts = []

with open(DATA, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        facts.append(row)

fact = random.choice(facts)
text = fact["title"]
body = fact["body"]

print("selected:", text)

subprocess.run(
    [
        "ffmpeg",
        "-stream_loop",
        "-1",
        "-i",
        str(VIDEO),
        "-t",
        "20",
        "-vf",
        "scale=1080:1920",
        "-c:v",
        "libx264",
        str(OUT / "short.mp4"),
    ],
    check=True,
)

metadata = {
    "title": f"{text} #shorts",
    "description": body,
    "tags": ["shorts", "雑学"],
}

with open(OUT / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
