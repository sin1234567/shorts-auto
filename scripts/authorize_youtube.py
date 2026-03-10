from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
ROOT = Path(__file__).resolve().parent.parent
SECRETS_DIR = ROOT / "secrets"
CLIENT_SECRET = SECRETS_DIR / "client_secret.json"
TOKEN_FILE = SECRETS_DIR / "token.json"


def main() -> None:
    if not CLIENT_SECRET.exists():
        raise FileNotFoundError(f"Client secret not found: {CLIENT_SECRET}")

    SECRETS_DIR.mkdir(exist_ok=True)

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(credentials.to_json())

    print(f"Saved token: {TOKEN_FILE}")


if __name__ == "__main__":
    main()
