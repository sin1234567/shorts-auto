import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
VIDEO = OUT / "short.mp4"
METADATA = OUT / "metadata.json"


def main() -> None:
    if not VIDEO.exists():
        raise FileNotFoundError(f"Video not found: {VIDEO}")

    token_file = Path(os.environ.get("YOUTUBE_TOKEN_FILE", ROOT / "secrets" / "token.json"))
    if not token_file.exists():
        raise FileNotFoundError(f"Token file not found: {token_file}")

    with open(METADATA, encoding="utf-8") as f:
        metadata = json.load(f)

    credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials.valid:
        raise RuntimeError("YouTube credentials are invalid. Recreate token.json with offline access.")

    youtube = build("youtube", "v3", credentials=credentials)
    tags = metadata.get("tags", [])

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": metadata["title"],
                "description": metadata.get("description", ""),
                "tags": tags,
                "categoryId": os.environ.get("YOUTUBE_CATEGORY_ID", "22"),
            },
            "status": {
                "privacyStatus": os.environ.get("YOUTUBE_PRIVACY_STATUS", "public"),
                "selfDeclaredMadeForKids": False,
            },
        },
        media_body=MediaFileUpload(str(VIDEO), chunksize=-1, resumable=True),
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    print(f"Upload complete: https://www.youtube.com/watch?v={response['id']}")


if __name__ == "__main__":
    main()
