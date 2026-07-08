import json
import os
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError, ResumableUploadError
from googleapiclient.http import MediaFileUpload

from mark_posted import record_posted_fact

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
VIDEO = OUT / "short.mp4"
METADATA = OUT / "metadata.json"
STATUS = OUT / "upload_status.json"


def write_status(status: str, **payload: str) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps({"status": status, **payload}, ensure_ascii=False, indent=2), encoding="utf-8")


def is_upload_limit_error(exc: Exception) -> bool:
    if isinstance(exc, (HttpError, ResumableUploadError)):
        message = str(exc)
        return "uploadLimitExceeded" in message or "exceeded the number of videos" in message
    return False


def is_token_revoked_error(exc: Exception) -> bool:
    if not isinstance(exc, RefreshError):
        return False
    message = str(exc)
    return "invalid_grant" in message and ("expired or revoked" in message or "revoked" in message)


def sanitize_youtube_text(value: object) -> str:
    """Return text accepted by YouTube's title/description fields."""
    text = str(value).replace("<", "＜").replace(">", "＞")
    return "".join(char for char in text if char in "\n\r\t" or ord(char) >= 32)


def main() -> None:
    if STATUS.exists():
        STATUS.unlink()

    metadata: dict[str, object] = {}
    if not VIDEO.exists():
        write_status("failed", reason="videoNotFound")
        raise FileNotFoundError(f"Video not found: {VIDEO}")

    token_file = Path(os.environ.get("YOUTUBE_TOKEN_FILE", ROOT / "secrets" / "token.json"))
    if not token_file.exists():
        write_status("failed", reason="tokenFileNotFound", token_file=str(token_file))
        raise FileNotFoundError(f"Token file not found: {token_file}")

    with open(METADATA, encoding="utf-8") as f:
        metadata = json.load(f)

    source_title = str(metadata.get("source_title", ""))

    credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    try:
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
    except Exception as exc:
        if is_token_revoked_error(exc):
            write_status("failed", reason="tokenRevoked", source_title=source_title)
            raise RuntimeError(
                "YouTube token refresh failed: token expired or revoked. Run scripts/authorize_youtube.py."
            ) from exc
        write_status("failed", reason=type(exc).__name__, source_title=source_title)
        raise

    if not credentials.valid:
        write_status("failed", reason="invalidCredentials", source_title=source_title)
        raise RuntimeError("YouTube credentials are invalid. Recreate token.json with offline access.")

    youtube = build("youtube", "v3", credentials=credentials)
    tags = metadata.get("tags", [])
    privacy_status = os.environ.get("YOUTUBE_PRIVACY_STATUS", "private")
    publish_at = os.environ.get("YOUTUBE_PUBLISH_AT", "").strip()

    status_payload = {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": False,
    }
    if publish_at:
        if privacy_status != "private":
            write_status(
                "failed",
                reason="publishAtRequiresPrivate",
                source_title=source_title,
                privacyStatus=privacy_status,
                publishAt=publish_at,
            )
            raise RuntimeError("YOUTUBE_PUBLISH_AT requires YOUTUBE_PRIVACY_STATUS=private.")
        status_payload["publishAt"] = publish_at

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": sanitize_youtube_text(metadata["title"]),
                "description": sanitize_youtube_text(metadata.get("description", "")),
                "tags": tags,
                "categoryId": os.environ.get("YOUTUBE_CATEGORY_ID", "22"),
            },
            "status": status_payload,
        },
        media_body=MediaFileUpload(str(VIDEO), chunksize=-1, resumable=True),
    )

    response = None
    try:
        while response is None:
            _, response = request.next_chunk()
    except Exception as exc:
        if is_upload_limit_error(exc):
            write_status(
                "blocked",
                reason="uploadLimitExceeded",
                source_title=source_title,
                privacyStatus=privacy_status,
                publishAt=publish_at,
            )
            print("Upload skipped: YouTube upload limit exceeded for this account/channel.")
            return
        write_status(
            "failed",
            reason=type(exc).__name__,
            source_title=source_title,
            privacyStatus=privacy_status,
            publishAt=publish_at,
        )
        raise

    write_status(
        "uploaded",
        video_id=response["id"],
        source_title=source_title,
        privacyStatus=privacy_status,
        publishAt=publish_at,
    )
    record_posted_fact(source_title)
    print(f"Upload complete: https://www.youtube.com/watch?v={response['id']}")


if __name__ == "__main__":
    main()
