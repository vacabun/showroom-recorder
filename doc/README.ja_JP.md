# showroom-recorder

SHOWROOM 配信の録画、アップロード、失敗タスクの手動再送に対応したスクリプトです。

[![zh_CN](https://img.shields.io/badge/language-zh__CN-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.zh_CN.md)
[![en_US](https://img.shields.io/badge/language-en__US-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.en_US.md)
[![ja_JP](https://img.shields.io/badge/language-ja__JP-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.ja_JP.md)

## インストール

```bash
pip install showroom-recorder
sudo apt install ffmpeg
```

## 設定

アプリはカレントディレクトリの `config.json` を読み込みます。リポジトリには `config.example.json` もあります。

一般的な設定手順：

1. `config.example.json` を `config.json` としてコピーする
2. 監視したい SHOWROOM のルーム key を `rooms` に入れる
3. Bilibili へ自動投稿したい場合は `biliup.rooms` にルーム key を追加する
4. WebDAV にアップロードしたい場合は `webdav.upload` を有効にして接続情報を設定する
5. 古い動画を自動削除したい場合は `cleanup_uploaded_videos_after_hours` に `48` などの正の値を設定する

SHOWROOM の配信 URL は次の形式です。

```text
https://www.showroom-live.com/ROOM_URL_KEY
```

最後の `ROOM_URL_KEY` を `rooms` に設定してください。

Bilibili へ自動投稿する場合は、`cookies.json` を実行ディレクトリに置き、対象ルームを `biliup.rooms` に追加してください。

最小構成例：

```json
{
    "interval": 10,
    "debug": false,
    "best_quality": true,
    "rooms": ["LOVE_MAIKA_SASAKI"],
    "biliup": {
        "rooms": ["LOVE_MAIKA_SASAKI"],
        "line": "AUTO"
    },
    "webdav": {
        "upload": false,
        "url": "",
        "username": "",
        "password": "",
        "delete_source_file": false
    },
    "cleanup_uploaded_videos_after_hours": 48
}
```

## 使い方

```bash
showroom-recorder -i LOVE_MAIKA_SASAKI
showroom-recorder
```

## アップロード動作

録画ファイルがアップロード対象になると、次のように処理されます。

- 失敗タスクは `upload_failures.jsonl` に保存される
- 成功タスクは `upload_successes.jsonl` に保存される
- 再試行可能なアップロードは内部で一定回数リトライされる
- 自動削除の対象は `videos/` 直下の `.mp4` のみ
- 自動削除はアップロード成功後にのみ動作する
- `cleanup_uploaded_videos_after_hours` を超えたファイルだけが削除候補になる
- そのファイルに必要な全アップロード先が成功してから削除される
- 失敗記録が残っているファイルは削除されない

## 手動再送

失敗したアップロードをすべて再送する：

```bash
showroom-recorder --retry-failed-uploads
```

特定のアップロード先だけ再送する：

```bash
showroom-recorder --retry-failed-uploads --retry-failed-uploads-target bilibili
showroom-recorder --retry-failed-uploads --retry-failed-uploads-target webdav
```

特定のファイルだけ再送する：

```bash
showroom-recorder --retry-failed-uploads --retry-failed-uploads-file videos/LOVE_MAIKA_SASAKI_20260328_120000.mp4
```

録画ファイルは `videos/` に保存されます。

自動削除設定例：

```json
{
    "cleanup_uploaded_videos_after_hours": 48
}
```

この値が `0` より大きい場合、アップロード成功後に `videos/` 直下の古い `.mp4` を削除します。ただし、そのファイルに必要な全アップロード先が成功していることが条件です。
