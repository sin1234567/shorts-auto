# shorts-auto

YouTube Shorts を毎日自動生成して投稿するリポジトリです。ネタの選定、動画生成、YouTube 投稿、投稿済み履歴の更新までを一連で回します。

## 運用方針

- 本番基準は Linux / GitHub Actions です。
- Linux 本番では `open_jtalk` を正式採用します。
- 音質改善は TTS エンジン差し替えより先に、台本制約・自動整形・短チャンク分割で対応します。
- Windows の `edge-tts` はローカル補助経路です。本番品質の基準にはしません。
- コード、ワークフロー、ネタ設計、運用ルールを変えたときは、この README に同じターンで追記します。
- 2026-03-19: Git 無し運用では YouTube 確認を基準にし、アップロード既定は `private` とします。確認後に公開または予約公開へ回します。
- 2026-03-19: GitHub Actions の定期実行は停止しました。以後は手動実行またはローカルからの予約投入で管理します。

## 構成

```text
shorts-auto/
  .github/workflows/daily.yml
  data/
    facts.csv
    posted_facts.txt
  out/
    short.mp4
    metadata.json
    narration_tts.txt
    upload_status.json
  scripts/
    authorize_youtube.py
    make_video.py
    mark_posted.py
    upload_youtube.py
  tests/
  pytest.ini
  requirements.txt
```

## データ

[facts.csv](C:/Users/fillm/shorts-auto/data/facts.csv)
- UTF-8 の `title,body` CSV
- 1 行が 1 ネタです
- タイトルは近縁重複を避け、数字、誤解修正、理由のいずれかを前に出してフックを作ります
- 本文は単なる言い換えで終わらせず、仕組み、比較、誤解修正のどれかを 1 つ入れます
- 2026-03-18: `facts.csv` の修正は短文化ではなく内容強化を優先します。本文に仕組み・比較・誤解修正を足して、聞いたあとに一段深く理解できるネタへ寄せます
- 2026-03-18: 作業前に README へ今回やる修正方針を追記してから進めます

[posted_facts.txt](C:/Users/fillm/shorts-auto/data/posted_facts.txt)
- 投稿済みタイトルを 1 行ずつ記録します
- 再投稿防止に使います

## 生成仕様

- 動画サイズは `1080x1920`
- フレームレートは `30fps`
- 背景テーマは定義済み配色からランダム選択
- 動画尺は音声長ベースで決定
- 動画長は `audio_duration + 0.8秒`
- 最大動画長は `35秒`
- 先頭に `180ms` の無音を追加
- 後端の無音は弱めにトリムし、その後に余白を足して末尾切れを防ぎます
- 正規化後の音声は `48kHz mono`

## TTS 仕様

### 本番経路

- GitHub Actions 本番は `ubuntu-latest`
- 本番の音声生成は `open_jtalk`
- 長文一発読みは避け、短チャンクごとに合成して結合します

### ローカル補助経路

- Windows ローカルでは `edge-tts` を使用します
- こちらも短チャンクごとに合成して結合します
- ただし本番品質の判断基準は Linux 側です

### 台本制約

- 日本語
- 1 文は短く保つ
- `。！？、` を使って区切れる形にする
- 漢字を適度に残す
- 相づち単独を避ける
- 語尾を長く引っ張る言い回しを避ける
- 締め文は短くし、末尾に情報を詰め込みすぎない

推奨例:

```text
そうですね。
意外です。
これ、知ってましたか？
```

非推奨例:

```text
そうですね
そーーーうですね
うわーーー
```

### 自動整形ルール

TTS 前に、読み崩れの原因になりやすい表現は自動で抑制します。

- `ーーー` は使わない
- `〜` は使わない
- `...` と `・・・` は文末記号に寄せる
- 余計な空白は詰める
- 文末が欠けている場合は終端記号を補います

### チャンク分割ルール

- 優先分割は `。！？`
- 次点で `、`
- 1 チャンクは短めに保ちます
- 長すぎる文は複数チャンクに分けます
- 空チャンクは捨てます

## ローカル実行

依存導入:

```bash
pip install -r requirements.txt
```

動画生成:

```bash
python scripts/make_video.py
```

主な生成物:

- [short.mp4](C:/Users/fillm/shorts-auto/out/short.mp4)
- [metadata.json](C:/Users/fillm/shorts-auto/out/metadata.json)
- [narration_tts.txt](C:/Users/fillm/shorts-auto/out/narration_tts.txt)

YouTube 認証:

```bash
python scripts/authorize_youtube.py
```

アップロード:

```bash
python scripts/upload_youtube.py
```

公開設定の上書き:

```bash
$env:YOUTUBE_PRIVACY_STATUS = "unlisted"
python scripts/upload_youtube.py
```

予約公開:

```bash
$env:YOUTUBE_PRIVACY_STATUS = "private"
$env:YOUTUBE_PUBLISH_AT = "2026-03-20T12:00:00+09:00"
python scripts/upload_youtube.py
```

投稿済み履歴更新:

```bash
python scripts/mark_posted.py
```

## GitHub Actions

ワークフローは [daily.yml](C:/Users/fillm/shorts-auto/.github/workflows/daily.yml) です。

トリガー:

- `workflow_dispatch`
- `push` to `main`

実行内容:

1. Python をセットアップ
2. Ubuntu 上で `ffmpeg`, `open-jtalk`, Noto フォントをインストール
3. `python scripts/make_video.py`
4. `YOUTUBE_TOKEN_JSON` があれば YouTube 投稿
5. 投稿成功時のみ `posted_facts.txt` を更新して push

必要な GitHub Secret:

- `YOUTUBE_TOKEN_JSON`

## 投稿仕様

- `scripts/upload_youtube.py` の既定公開設定は `private`
- `YOUTUBE_PRIVACY_STATUS` で `private` / `unlisted` / `public` を上書きできます
- `YOUTUBE_PUBLISH_AT` を指定すると、`private` のまま予約公開時刻を設定できます
- 投稿成功時は `out/upload_status.json` に結果を書きます
- 投稿済みタイトルは [posted_facts.txt](C:/Users/fillm/shorts-auto/data/posted_facts.txt) に記録します
- Actions が `Record posted fact` を自動コミットします
- 2026-03-19: 予約公開の一括投入は YouTube 側の当日アップロード上限で途中停止することがあります。2026-03-20 から 2026-03-22 までは予約投入済みで、2026-03-23 分から再開します。
- 2026-03-19: GitHub Actions の `schedule` は削除済みです。自動日次投稿は止まっています。

## Git 無し運用ログ

### 2026-03-19 予約投入

- 方針: `private` で先に予約投入し、YouTube 上で確認しながら進める
- 実績: 10本投入を開始し、3本予約完了で YouTube の `uploadLimitExceeded` により停止

投入済み:

- 2026-03-20 12:00 JST: `1円玉は主にアルミニウムでできている`
- 2026-03-21 12:00 JST: `皮膚は紫外線から体を守る役目も持つ`
- 2026-03-22 12:00 JST: `月の模様は海ではなく広い平原`

再開位置:

- 次の予定は 2026-03-23 12:00 JST
- 次候補は [metadata.json](C:/Users/fillm/shorts-auto/out/metadata.json) に入っている `松ぼっくりの形は種類でかなり違う`
- 停止時の状態は [upload_status.json](C:/Users/fillm/shorts-auto/out/upload_status.json) の `blocked / uploadLimitExceeded`

再開コマンド:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/schedule_remaining_uploads.ps1 -StartAt "2026-03-23T12:00:00+09:00" -Count 7 -UseCurrentVideoFirst
```

## テスト

主要テスト:

```bash
pytest tests/test_make_video_duration.py
pytest tests/test_make_video_regressions.py
pytest tests/test_make_video_tts_hiragana.py
pytest tests/test_make_video_tts_split.py
pytest tests/test_upload_youtube.py
```

`pytest.ini` では Windows の一時ディレクトリ問題を避けるため、`--basetemp` をリポジトリ内に固定しています。
