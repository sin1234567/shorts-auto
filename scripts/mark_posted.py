import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
METADATA = ROOT / "out" / "metadata.json"
POSTED = ROOT / "data" / "posted_facts.txt"


def main() -> None:
    with open(METADATA, encoding="utf-8") as f:
        metadata = json.load(f)

    title = metadata["source_title"].strip()
    POSTED.parent.mkdir(exist_ok=True)

    existing = set()
    if POSTED.exists():
        with open(POSTED, encoding="utf-8") as f:
            existing = {line.strip() for line in f if line.strip()}

    if title in existing:
        print(f"Already recorded: {title}")
        return

    with open(POSTED, "a", encoding="utf-8") as f:
        f.write(title + "\n")

    print(f"Recorded posted fact: {title}")


if __name__ == "__main__":
    main()
