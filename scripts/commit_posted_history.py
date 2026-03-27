import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
METADATA = ROOT / "out" / "metadata.json"
POSTED = ROOT / "data" / "posted_facts.txt"


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def main() -> None:
    if not POSTED.exists():
        raise FileNotFoundError(f"Posted history not found: {POSTED}")
    if not METADATA.exists():
        raise FileNotFoundError(f"Metadata not found: {METADATA}")

    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    source_title = metadata.get("source_title", "").strip() or "posted fact"

    run_git("add", "data/posted_facts.txt")
    status = run_git("diff", "--cached", "--name-only").stdout.strip()
    if not status:
        print("No staged posted history changes.")
        return

    run_git("commit", "-m", f"Record posted fact: {source_title}")
    print("Committed posted history. Push with: git -C C:\\Users\\fillm\\shorts-auto push")


if __name__ == "__main__":
    main()
