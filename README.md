# shorts-auto

YouTube Shorts を毎日自動生成して投稿するリポジトリです。ネタの選定、動画生成、YouTube 投稿、投稿済み履歴の更新までを一連で回します。

補足:

- ロング動画版は別リポジトリ `C:/Users/fillm/long-video-auto` で管理します
- この README は Shorts 運用のみを対象にします

## 運用方針

- 本番基準は Linux / GitHub Actions です。
- Linux 本番では `open_jtalk` を正式採用します。
- 音質改善は TTS エンジン差し替えより先に、台本制約・自動整形・短チャンク分割で対応します。
- Windows の `edge-tts` はローカル補助経路です。本番品質の基準にはしません。
- コード、ワークフロー、ネタ設計、運用ルールを変えたときは、この README に同じターンで追記します。
- 2026-03-19: Git 無し運用では YouTube 確認を基準にし、アップロード既定は `private` とします。確認後に公開または予約公開へ回します。
- 2026-03-19: GitHub Actions の定期実行を再度有効化しました。ローカルの手動・予約投入と併用します。
- 2026-03-27: 直近の再生数分析では `身近な物 + 意外な事実` が強かったため、比較用に同系統の新ネタを3本追加しました。公開時刻は `12:00 JST` で固定し、しばらくはテーマと尺の差を優先して見ます。
- 2026-04-01: テスト実行は `tests/` に限定し、Windows では `tests_tmp/` を使って一時ディレクトリ権限の不安定さを避けます。`upload_status.json` は失敗時も `source_title` と公開設定を残すようにしました。

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
- 検証用に特定ネタを出したいときは `FACT_TITLE` 環境変数で `facts.csv` のタイトルを直接指定できます

[posted_facts.txt](C:/Users/fillm/shorts-auto/data/posted_facts.txt)
- 投稿済みタイトルを 1 行ずつ記録します
- 再投稿防止に使います

## 生成仕様

- 動画サイズは `1080x1920`
- フレームレートは `30fps`
- 背景テーマは定義済み配色からランダム選択
- 動画尺は音声長ベースで決定
- 動画長は `audio_duration + 0.35秒`
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

特定ネタを指定して生成:

```powershell
$env:FACT_TITLE = "消しゴムのかすはただのゴミではない"
python scripts/make_video.py
```

YouTube へ手動アップロードした場合:

```bash
python scripts/upload_youtube.py
```

- 成功時は `data/posted_facts.txt` に自動で記録されます
- GitHub Actions 側と共有したいときは次でコミットできます

```bash
python scripts/commit_posted_history.py
```

主な生成物:

- [short.mp4](C:/Users/fillm/shorts-auto/out/short.mp4)
- [metadata.json](C:/Users/fillm/shorts-auto/out/metadata.json)
- [narration_tts.txt](C:/Users/fillm/shorts-auto/out/narration_tts.txt)

YouTube 認証:

```bash
python scripts/authorize_youtube.py
```

トークン失効時の再認証:

```bash
python scripts/authorize_youtube.py
```

- `scripts/upload_youtube.py` 実行時に `invalid_grant` が出た場合は、`out/upload_status.json` に `failed / tokenRevoked` を書きます
- この状態では事前通知は来ない前提で、アップロード失敗時に再認証して復旧します

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
- `schedule`

実行内容:

1. Python をセットアップ
2. Ubuntu 上で `ffmpeg`, `open-jtalk`, Noto フォントをインストール
3. `python scripts/make_video.py`
4. `YOUTUBE_TOKEN_JSON` があれば YouTube 投稿
5. `out/upload_status.json` と `out/metadata.json` を artifact として保存
6. 投稿成功時のみ `posted_facts.txt` を更新して push

必要な GitHub Secret:

- `YOUTUBE_TOKEN_JSON`

失敗時の確認:

- Actions の `Summarize upload result` で `status` と `reason` を確認します
- `Upload to YouTube` が失敗しても `Read upload status` は実行され、job の末尾で `Upload failed: reason=...` を明示します
- `status=blocked` かつ `reason=uploadLimitExceeded` の場合は YouTube 側の当日上限として扱い、workflow 自体は失敗させません
- `reason=tokenRevoked` の場合は `python scripts/authorize_youtube.py` を実行して、更新された `secrets/token.json` を GitHub Secret `YOUTUBE_TOKEN_JSON` に再登録します
- `daily-shorts-diagnostics` artifact に `out/upload_status.json` と `out/metadata.json` が残ります

## 投稿仕様

- `scripts/upload_youtube.py` の既定公開設定は `private`
- `YOUTUBE_PRIVACY_STATUS` で `private` / `unlisted` / `public` を上書きできます
- `YOUTUBE_PUBLISH_AT` を指定すると、`private` のまま予約公開時刻を設定できます
- 投稿成功時は `out/upload_status.json` に結果を書きます
- 投稿済みタイトルは [posted_facts.txt](C:/Users/fillm/shorts-auto/data/posted_facts.txt) に記録します
- Actions が `Record posted fact` を自動コミットします
- 2026-03-19: 予約公開の一括投入は YouTube 側の当日アップロード上限で途中停止することがあります。2026-03-20 から 2026-03-22 までは予約投入済みで、2026-03-23 分から再開します。
- 2026-03-19: GitHub Actions の `schedule` は再度有効です。日次自動投稿とローカル手動運用を併用します。

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

### 2026-03-19 ローカル改善と確認

- ローカル確認は行わず、YouTube 上の限定公開/非公開動画を確認基準にした
- `scripts/make_video.py` に以下の改善を入れた
  - `ffmpeg` 解決時の Windows `PermissionError` 回避
  - 一時ディレクトリ処理の Windows 安定化
  - 強制的な文字数切りを弱め、句読点優先の TTS 分割に変更
  - フック文を短く自然な口語に寄せた
  - 字幕帯と字幕描画を追加し、複数行は行ごとに個別描画へ変更
  - 改行由来の四角文字対策として字幕テキストを LF 固定で出力
  - 末尾に短い無音を追加して語尾切れを軽減
  - 本文の 2 文目も拾いやすくして、話の薄さを改善

確認用にアップロードした動画:

- `https://www.youtube.com/watch?v=4KT6s2WdM3w`
- `https://www.youtube.com/watch?v=Fzsle26UzII`
- `https://www.youtube.com/watch?v=FEg75ZmkKh4`
- `https://www.youtube.com/watch?v=sYDayNZDXuo`

### 2026-03-27 Shorts運用メモ

- `消しゴムのかすはただのゴミではない` を生成してアップロード完了
- 動画URL: `https://www.youtube.com/watch?v=rySnXm9xb-A`
- `data/posted_facts.txt` に投稿済みとして記録
- GitHub `main` へ push 済み
- GitHub Actions と投稿済み履歴を共有できる状態へ修正

今回判明したこと:

- Shorts が止まっていた原因は、少なくとも今回確認した時点では `uploadLimitExceeded` ではなく YouTube トークン失効
- 実エラーは `invalid_grant: Token has been expired or revoked.`
- `scripts/authorize_youtube.py` で再認証後、アップロードは正常復旧

入れた修正:

- `scripts/upload_youtube.py`
  - アップロード成功時に `posted_facts.txt` を自動更新
  - `upload_status.json` に `source_title` を保存
  - `invalid_grant` を検知したら `failed / tokenRevoked` を書く
- `scripts/mark_posted.py`
  - `record_posted_fact()` を切り出して再利用可能に変更
- `scripts/make_video.py`
  - `FACT_TITLE` で特定ネタを指定して生成可能に変更
- `scripts/commit_posted_history.py`
  - 投稿履歴だけを Git commit しやすくする補助スクリプトを追加
- `README.md`
  - 特定ネタ生成手順
  - 手動アップロード時の投稿履歴共有手順
  - トークン失効時の再認証手順
  を追記

Git反映:

- GitHub push 済み
- 反映済みコミット:
  - `596950a` 投稿履歴共有と手動アップロード追跡
  - `f199a34` トークン失効検知

現在の確認状態:

- `out/upload_status.json`: `uploaded`
- `data/posted_facts.txt`: `消しゴムのかすはただのゴミではない` を記録済み
- YouTube URL確認済み
- GitHub `origin/main` 反映済み

次候補:

1. `500円玉は昔と今で素材が違う`
2. `ホッチキスの針は勝手に曲がるわけではない`

運用メモ:

- 今後はアップロード後に必ず以下を確認する
  - `out/upload_status.json`
  - `data/posted_facts.txt`
  - YouTube URL
  - `git push` 済みか
- `invalid_grant` が出た場合は事前通知ではなく失敗時発覚とみなす
- その場合は `python scripts/authorize_youtube.py` を実行して再認証する

### 2026-03-27 GitHub Actions 復旧

- GitHub Actions の `Upload to YouTube` 失敗は、repo secret `YOUTUBE_TOKEN_JSON` が古いままだったことが原因
- ローカルで `scripts/authorize_youtube.py` を実行して更新した `token.json` を、GitHub secret `YOUTUBE_TOKEN_JSON` に反映
- その後の run `23635340799` は `success`
- これでローカルと GitHub Actions の両方で YouTube アップロードが復旧

確認メモ:

- 失敗 step が `Upload to YouTube` のときは、まず `YOUTUBE_TOKEN_JSON` の失効を疑う
- ローカルで再認証して成功したら、GitHub 側の secret も同じ内容で更新する
- 復旧確認は Actions run の `conclusion=success` まで見る

補足:

- `Fzsle26UzII` は改善前の確認用
- 以後の動画は、四角文字、音声途切れ、話の薄さを順に詰めた確認用
- 長尺版は `C:/Users/fillm/long-video-auto` に分離したため、この README では Shorts 運用だけを管理する

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
