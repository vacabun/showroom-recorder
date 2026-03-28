# showroom-recorder
SHOWROOM 配信を録画するためのスクリプトです。

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

SHOWROOM の配信 URL は次の形式です。

```text
https://www.showroom-live.com/ROOM_URL_KEY
```

最後の `ROOM_URL_KEY` を `rooms` に設定してください。

Bilibili へ自動投稿する場合は、`cookies.json` を実行ディレクトリに置き、対象ルームを `biliup.rooms` に追加してください。

## 使い方

```bash
showroom-recorder -i LOVE_MAIKA_SASAKI
showroom-recorder
```

録画ファイルは `videos/` に保存されます。
