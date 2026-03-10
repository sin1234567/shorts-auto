# shorts-auto 引き継ぎメモ

## リポジトリ

- GitHub: `sin1234567/shorts-auto`
- ローカル: `C:\Users\fillm\shorts-auto`

## 現在の構成

### ワークフロー

`/.github/workflows/daily.yml`

処理の流れ:

```text
facts.csv
  ↓
make_video.py
  ↓
open_jtalk 音声生成
  ↓
縦動画生成 (ffmpeg)
  ↓
upload_youtube.py
  ↓
YouTube unlisted 投稿
  ↓
mark_posted.py
  ↓
posted_facts.txt 更新
```

## ディレクトリ構成

```text
shorts-auto
│
├ scripts
│  ├ make_video.py
│  ├ upload_youtube.py
│  └ mark_posted.py
│
├ data
│  ├ facts.csv
│  └ posted_facts.txt
│
├ out
│
└ .github/workflows
   └ daily.yml
```

## 動画仕様

- 縦動画
- 約1分
- 日本語音声 (`open_jtalk`)
- 日本語テキスト
- YouTube `unlisted` 投稿

## 重複防止

投稿済みネタは `data/posted_facts.txt` に保存します。  
次回は `facts.csv` から未使用ネタだけを選びます。

## 文字化け対策

`drawtext` への日本語直書きは使わず、`textfile=` 方式に変更済みです。

## GitHub Actions 修正点

履歴 push エラー対策として以下を追加済みです。

```yaml
permissions:
  contents: write
```

push は次の形に変更済みです。

```bash
git push origin HEAD:${GITHUB_REF_NAME}
```

## ローカルセットアップ

1. `pip install -r requirements.txt`
2. `secrets/client_secret.json` を配置
3. `python scripts/authorize_youtube.py`
4. 生成された `secrets/token.json` の中身を GitHub Secrets の `YOUTUBE_TOKEN_JSON` に登録

## 明日やること

GitHub の `Actions` から `Run workflow` を実行して、次を確認します。

1. `build` が完走するか
2. 日本語文字化けが直ったか
3. YouTube 投稿が成功するか

## 再開するときの合言葉

```text
shorts-auto の続き
引き継ぎメモの状態から再開
```
