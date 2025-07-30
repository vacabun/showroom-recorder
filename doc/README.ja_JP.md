# showroom-recorder
SHOWROOMビデオを録画するためのスクリプト

[![zh_CN](https://img.shields.io/badge/language-zh__CN-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.zh_CN.md)
[![en_US](https://img.shields.io/badge/language-en__US-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.en_US.md)
[![ja_JP](https://img.shields.io/badge/language-ja__JP-green.svg)](https://github.com/vacabun/showroom-recorder/blob/main/doc/README.ja_JP.md)

## インストール方法
1. python3をインストールしてください。

2. python環境をインストールしてください。

``` shell
pip install showroom-recorder
```

3. ffmpegをインストールしてください。

``` shell
sudo apt install ffmpeg
```

## 使用方法
メンバールーム名を引数としてスクリプトを実行します：

``` shell
showroom-recorder -i LOVE_MAIKA_SASAKI
```

または、`config.json`ファイルを編集してパラメータなしでスクリプトを直接実行し、初回実行時に自動的に設定ファイルが作成されます。

> showroom ライブ配信アドレス: "https://www.showroom-live.com/ROOM_URL_KEY"

> 最後の部分のルーム名をコピーして、`rooms`に貼り付けてください。

``` shell
showroom-recorder
```

録画されたビデオは`videos`フォルダーに保存されます。
