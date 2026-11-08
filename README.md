# LINE WORKS WOFF ミニアプリ エディター

LINE WORKS の WOFF (LINE WORKS Front-end Framework) アプリを、ブラウザーだけで作って試すための教材です。

**エディター: https://iwaohig.github.io/lineworks-woff-workshop/**

## できること

- アプリの名前・アイコン・テーマ色、トークに送るボタンなどを、フォームで選んで作る
- 部品 (依頼フォーム / QR でチェックイン / 当番ルーレット / 今日のひとこと) を足す
- 「コードで編集」で、出来上がる HTML を直接書き換える
- スマホの枠の中でプレビューし、送った文を隣のトークルームで確かめる (プレビューでは WOFF SDK の代わりに見本の `woff` を使います)
- WOFF ID を入れて、HTML / CSS / JavaScript が 1 つにまとまった `index.html` をダウンロードする

画面の「今日のお題」に沿って進めると、ひととおり試せます。

## 作ったアプリを LINE WORKS で開くまで

Colab のノートブック: **[woff_workshop.ipynb を Colab で開く](https://colab.research.google.com/github/iwaohig/lineworks-woff-workshop/blob/main/colab/woff_workshop.ipynb)**

1. [Developer Console](https://dev.worksmobile.com/jp/) で WOFF アプリを登録し、WOFF ID を受け取る
   (Endpoint URL は仮の URL で構いません。あとで書き換えても WOFF ID は変わりません。QR を使うなら Scan QR を ON)
2. エディターで作り、WOFF ID を入れて `index.html` をダウンロードする
3. Colab のノートブックで `index.html` をアップロードし、トンネルで `https://` の URL を作る
4. その URL を WOFF アプリの Endpoint URL に設定する
5. LINE WORKS のトークに WOFF URL (`https://woff.worksmobile.com/woff/{WOFF ID}`) を送り、タップして開く

ノートブックは `colab/build_nb.py` から作っています (`python colab/build_nb.py`)。
参考: [LINE WORKS WOFF アプリを Google Colab を使って簡単に試す](https://qiita.com/iwaohig/items/030273863d41d67b2b6a)

## 注意

- `woff.sendMessage()` でトークに送れるのは、モバイルアプリのトークルームから開いたときだけです。Client App に `bot` か `bot.message` の Scope が要ります
- 外部ブラウザーで開くとログインが必要です ([参考](https://qiita.com/iwaohig/items/186863fcf7e443b90713))
- Colab のトンネルの URL は一時的なものです。止めると変わるので、続けて使うなら GitHub Pages などに置いてください ([参考](https://qiita.com/iwaohig/items/57e201a6dbaa72cae61f))

## ライセンス

MIT License。勉強会や社内の教材として自由に使ってください。
