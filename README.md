# shorts-auto

## Local setup

1. Install dependencies:
   `pip install -r requirements.txt`
2. Create `secrets/client_secret.json` from your Google Cloud OAuth desktop app.
3. Generate `secrets/token.json`:
   `python scripts/authorize_youtube.py`

## GitHub Actions secrets

Set this repository secret:

- `YOUTUBE_TOKEN_JSON`: paste the full contents of `secrets/token.json`

After that, run the `Daily Shorts Upload` workflow from the Actions tab.
