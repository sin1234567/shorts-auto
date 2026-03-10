from pathlib import Path


def main() -> None:
    video = Path(__file__).resolve().parent.parent / "out" / "short.mp4"
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")

    print("Upload step is not configured yet.")
    print(f"Prepared video: {video}")


if __name__ == "__main__":
    main()
