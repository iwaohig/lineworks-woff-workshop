# WOFF ミニアプリを Google Colab から公開するノートブックを作る
# 使い方: python build_nb.py  → woff_workshop.ipynb
import json
from pathlib import Path

OUT = Path(__file__).with_name("woff_workshop.ipynb")
EDITOR = "https://iwaohig.github.io/lineworks-woff-workshop/"
cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)})


def code(text):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": text.strip("\n").splitlines(keepends=True)})


md(f"""
# WOFF ミニアプリを Colab から公開して、トークから開く

[エディター]({EDITOR}) で作った `index.html` を、この Colab から公開します。
スマホの LINE WORKS のトークから開いて、ボタンを押すとトークに送られるところまで試します。

上のセルから順に実行していきます (各セルの左の ▶ を押す)。

| 章 | 内容 |
|---|---|
| 0 | 準備 |
| 1 | `index.html` をアップロードする |
| 2 | 公開する (配信とトンネル) |
| 3 | Endpoint URL を設定する (Developer Console) |
| 4 | トークから開く |
| 5 | QR コードの見本を出す (QR の部品を使うとき) |
| 6 | Bot のリッチメニューから開く |
| 7 | 作り直したファイルに差し替える |
| 8 | 終わったら止める |

## 始める前に

1. 画面の上の **「ドライブにコピー」** を押し、コピーのほうで作業します。
2. **WOFF ID を先に受け取っておきます。** Developer Console のアプリの画面で、WOFF アプリを「登録」します。
   - Endpoint URL は、いったん `https://example.com` のような仮の URL で構いません (2 章で出る URL に、あとで書き換えます)
   - QR の部品を使うときは **Scan QR を ON** にします
   - 書き換えても WOFF ID は変わりません
3. [エディター]({EDITOR}) で作り、WOFF ID を入れて `index.html` をダウンロードしておきます。

> 最初のセルを実行すると「このノートブックは Google が作成したものではありません」と出ます。
> GitHub から開いたノートブックには必ず出る確認です。**「このまま実行」** を押します。
""")

md("""
## 0. 準備

ライブラリを入れて、4-2 (Bot からボタンを送る) と 6 (リッチメニュー) で使う、Bot の認証情報を読みます。
**Bot を使わないなら、シークレットは要りません。** 未設定のままで 1 章に進めます。
前回 (第2回) のノートブックで入れたシークレットと同じ名前です。

Bot を使うときは、左の鍵のアイコン (シークレット) に次の 6 つを入れ、それぞれ「ノートブックからのアクセス」を ON にします。
値はノートブックには保存されません。入れる間は画面共有を止めてください。

| 名前 | 入れるもの |
|---|---|
| `LW_CLIENT_ID` | Client ID |
| `LW_CLIENT_SECRET` | Client Secret |
| `LW_SERVICE_ACCOUNT` | Service Account |
| `LW_PRIVATE_KEY` | 秘密鍵ファイル (.key) の中身をすべて |
| `LW_BOT_ID` | Bot ID (数字) |
| `LW_MY_ID` | 自分のログイン ID (ボタンの送り先) |
""")

code(r'''
# @title 0. 準備
!pip -q install qrcode pyjwt cryptography japanize-matplotlib

import json, os, queue, re, subprocess, threading, time
from pathlib import Path
import requests

WORKDIR = (Path("/content/woff") if Path("/content").exists() else Path("woff")).resolve()
WORKDIR.mkdir(parents=True, exist_ok=True)
PORT = 8000
NAMES = ["LW_CLIENT_ID", "LW_CLIENT_SECRET", "LW_SERVICE_ACCOUNT", "LW_PRIVATE_KEY", "LW_BOT_ID", "LW_MY_ID"]

conf = {}
try:
    from google.colab import userdata
    for n in NAMES:
        try:
            conf[n] = (userdata.get(n) or "").strip()
        except Exception:
            conf[n] = ""
except ImportError:  # Colab 以外 (手元での確認用) は環境変数から読む
    conf = {n: os.environ.get(n, "").strip() for n in NAMES}
conf["LW_PRIVATE_KEY"] = conf["LW_PRIVATE_KEY"].replace("\\n", "\n")


class Stop(Exception):
    """前のセルがまだ済んでいないとき。長いエラー表示を出さず、やり直す場所だけ出す"""


def need(name, hint):
    if globals().get(name) is None:
        raise Stop(hint)


try:  # Colab では Stop のときに案内の 1 行だけを出す
    get_ipython().set_custom_exc((Stop,), lambda shell, etype, value, tb, tb_offset=None: print("⚠", value))
except NameError:
    pass

BOT_READY = all(conf[n] for n in NAMES) or None
API = "https://www.worksapis.com/v1.0"


def bot_token(scope="bot"):
    """Service Account 認証で Bot 用のアクセストークンを作る (第2回の 1-1・1-2 と同じ)"""
    import jwt
    now = int(time.time())
    assertion = jwt.encode({"iss": conf["LW_CLIENT_ID"], "sub": conf["LW_SERVICE_ACCOUNT"], "iat": now, "exp": now + 600},
                           conf["LW_PRIVATE_KEY"], algorithm="RS256")
    r = requests.post("https://auth.worksmobile.com/oauth2/v2.0/token", data={
        "assertion": assertion, "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": conf["LW_CLIENT_ID"], "client_secret": conf["LW_CLIENT_SECRET"], "scope": scope,
    }, timeout=30)
    if r.status_code != 200:
        raise Stop(f"トークンを作れませんでした ({r.status_code})。シークレットの値を確かめてください: {r.text[:200]}")
    return r.json()["access_token"]


print("準備ができました。")
print("Bot の認証情報:", "6 つとも入っています (4-2・6 が使えます)" if BOT_READY else "未設定 (4-1 の方法で開きます。6 は使えません)")
''')

md("""
## 1. `index.html` をアップロードする

実行するとセルの下に **「ファイルを選択」** が出るので、エディターでダウンロードした `index.html` を選びます。
WOFF ID が入っているかと、WOFF SDK を読み込んでいるかを確かめます。
""")

code(r'''
# @title 1. index.html をアップロードする
need("WORKDIR", "先に 0 を実行してください")
try:
    from google.colab import files
    up = files.upload()
    if not up:
        raise Stop("ファイルが選ばれませんでした。1 をもう一度実行してください")
    name, data = next(iter(up.items()))
except ImportError:  # Colab 以外 (手元での確認用) は環境変数のパスから読む
    name = os.environ["WOFF_HTML"]
    data = Path(name).read_bytes()

html = data.decode("utf-8")
(WORKDIR / "index.html").write_text(html, encoding="utf-8")

m = re.search(r'const WOFF_ID = "([^"]*)"', html)
WOFF_ID = m.group(1) if m and m.group(1) else None
has_sdk = "static.worksmobile.net/static/wm/woff/" in html
print("ファイル  :", name, f"({len(data):,} バイト)")
print("WOFF ID   :", WOFF_ID or "空です")
print("WOFF SDK  :", "読み込んでいます" if has_sdk else "見つかりません")
if not WOFF_ID:
    raise Stop("WOFF ID が空です。エディターの ④ 仕上げで WOFF ID を入れてダウンロードし直し、1 をやり直してください")
if not has_sdk:
    raise Stop("WOFF SDK の script タグがありません。コードで消していないか確かめてください")
print("\n1 は OK です。2-1 に進んでください (差し替えのときは 2 章は不要です)")
''')

md("""
## 2. 公開する

1. Colab の中で `index.html` を配信する (2-1)
2. Cloudflare のトンネルで、インターネットから開ける `https://` の URL を作る (2-2)

> トンネルの URL は、Colab を止めたり 2-2 をやり直したりすると変わります。そのたびに 3 章の Endpoint URL を直してください。
> 勉強会の間だけ使う一時的な公開です。続けて使うなら、GitHub Pages などの置き場所に置きます。
""")

code(r'''
# @title 2-1. index.html を配信する
from flask import Flask, send_from_directory
import logging

need("WOFF_ID", "先に 1 を実行して、WOFF ID が入った index.html をアップロードしてください")
app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)


@app.get("/")
def index():
    r = send_from_directory(WORKDIR, "index.html")
    r.headers["Cache-Control"] = "no-store"  # 差し替えたら、開き直すだけで新しいほうが出るように
    return r


def alive() -> bool:
    try:
        return requests.get(f"http://localhost:{PORT}/", timeout=3).status_code == 200
    except requests.ConnectionError:
        return False


if alive():
    print("もう配信しています (ファイルを差し替えたときは、2-1 を実行し直す必要はありません)")
else:
    threading.Thread(target=lambda: app.run(port=PORT, use_reloader=False), daemon=True).start()
    time.sleep(1)
    print(f"配信を始めました (port {PORT})" if alive() else "配信を始められませんでした。ランタイムを再起動して 0 からやり直してください")
''')

code(r'''
# @title 2-2. トンネルを作って、Endpoint URL を表示する
need("app", "先に 2-1 を実行してください")
CLOUDFLARED = "2026.10.4"  # 版を固定する (latest だと、当日に新しい版が出て動きが変わることがある)
!wget -q -nc https://github.com/cloudflare/cloudflared/releases/download/{CLOUDFLARED}/cloudflared-linux-amd64 -O cloudflared-{CLOUDFLARED} && chmod +x cloudflared-{CLOUDFLARED}

if globals().get("tunnel") is not None and tunnel.poll() is None:  # やり直したときは前のトンネルを止める
    tunnel.terminate()
    print("前のトンネルを止めました (URL が変わるので、3 章もやり直します)")
tunnel = subprocess.Popen([f"./cloudflared-{CLOUDFLARED}", "tunnel", "--url", f"http://localhost:{PORT}", "--no-autoupdate"],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
lines = queue.Queue()
threading.Thread(target=lambda: [lines.put(l) for l in tunnel.stdout], daemon=True).start()

public, log, deadline = None, [], time.time() + 60
while public is None and time.time() < deadline and (tunnel.poll() is None or not lines.empty()):
    try:
        line = lines.get(timeout=1)
    except queue.Empty:
        continue
    log.append(line)
    m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
    if m:
        public = m.group(0)

ENDPOINT_URL = public + "/" if public else None
if not ENDPOINT_URL:
    print("トンネルの URL が取れませんでした。少し待ってから 2-2 をもう一度実行してください\n")
    print("".join(log[-10:]))
else:
    print("Endpoint URL:", ENDPOINT_URL)
    print("\nこの URL をコピーして、3 章の手順で WOFF アプリの Endpoint URL に設定してください")
    # できたばかりの URL は、つながるまで少しかかることがある。30 秒まで確かめる
    ready, until = False, time.time() + 30
    while not ready and time.time() < until:
        try:
            ready = requests.get(ENDPOINT_URL, timeout=5).status_code == 200
        except requests.RequestException:
            time.sleep(3)
    print("\nつながりました" if ready else "\n(まだつながっていないかもしれません。30 秒ほど待ってから開いてください)")
''')

md("""
## 3. Endpoint URL を設定する (Developer Console)

1. Developer Console でアプリを開き、「WOFF アプリ」の一覧で自分の WOFF の **「変更」** を押す
2. **Endpoint URL** を、2-2 で表示された URL に書き換えて **「保存」**
3. WOFF ID はそのままです (書き換える必要はありません)

> WOFF URL (`https://woff.worksmobile.com/woff/{WOFF ID}`) を開くと、LINE WORKS がここで設定した Endpoint URL に案内します。
""")

md("""
## 4. トークから開く

**トークルームから開いたときだけ**、ボタンでトークに送れます (`woff.sendMessage`。モバイルアプリのみ)。
PC 版やブラウザ版から開くと外部ブラウザで開き、送信は使えません。

- **4-1**: WOFF URL を表示します。スマホの LINE WORKS で、自分か仲間のいるトークに貼って送り、タップして開きます
- **4-2**: Bot から自分に「開く」ボタンを送ります (0 のシークレットが要ります)
""")

code(r'''
# @title 4-1. WOFF URL を表示する
need("WOFF_ID", "先に 1 を実行してください")
WOFF_URL = f"https://woff.worksmobile.com/woff/{WOFF_ID}"
print("WOFF URL:", WOFF_URL)
print("\nスマホの LINE WORKS で、トークにこの URL を貼って送り、タップして開いてください")
''')

code(r'''
# @title 4-2. Bot から自分に「開く」ボタンを送る
LABEL = "ミニアプリを開く"  # @param {type:"string"}
need("WOFF_ID", "先に 1 を実行してください")
need("BOT_READY", "Bot の認証情報が未設定です。0 の表のシークレットを入れて 0 を実行し直すか、4-1 の方法で開いてください")
token = bot_token()

body = {"content": {"type": "button_template", "contentText": "作ったミニアプリを開きます",
                    "actions": [{"type": "uri", "label": LABEL, "uri": f"https://woff.worksmobile.com/woff/{WOFF_ID}"}]}}
r = requests.post(f"{API}/bots/{conf['LW_BOT_ID']}/users/{conf['LW_MY_ID']}/messages",
                  headers={"Authorization": f"Bearer {token}"}, json=body, timeout=30)
print("送信:", r.status_code, "(201 なら成功。スマホの Bot とのトークを見てください)" if r.status_code == 201 else r.text[:300])
''')

md("""
## 5. QR コードの見本を出す (QR の部品を使うとき)

スマホで「QR を読み取る」を押し、この画面の QR コードを読み取ります。
中身の文字は自由に変えられます (例: 教室の名前、備品の番号)。
""")

code(r'''
# @title 5. QR コードを出す
TEXT = "渋谷教室"  # @param {type:"string"}
import qrcode
from IPython.display import display
display(qrcode.make(TEXT, box_size=10, border=4))
''')

md("""
## 6. Bot のリッチメニューから開く

Bot のトークの下に出る、画像のボタンのメニュー (リッチメニュー) を作り、その 1 つで WOFF を開きます。
リッチメニューは管理画面からは作れず、API で登録します。**0 のシークレット (Bot の認証情報) が要ります。**

1. メニューの画像を作る (6-1。ボタンの文字を変えられます)
2. メニューを登録し、画像を付けて、既定にする (6-2)
3. スマホで Bot とのトークを開き、下のメニューの「左のボタン」で WOFF が開くか確かめる

> 画像が出るのはモバイル版だけです。PC 版・ブラウザ版では文字のボタンになります。
> リッチメニューを作ると、Bot の固定メニューは出なくなります。元に戻すときは 6-3 を実行します。
""")

code(r'''
# @title 6-1. メニューの画像を作る (2500×843)
LEFT = "ミニアプリ"  # @param {type:"string"}
CENTER = "使い方"  # @param {type:"string"}
RIGHT = "こんにちは"  # @param {type:"string"}
import importlib.util
from PIL import Image, ImageDraw, ImageFont
from IPython.display import display

spec = importlib.util.find_spec("japanize_matplotlib")
FONT_PATH = str(Path(spec.submodule_search_locations[0]) / "fonts" / "ipaexg.ttf")  # 日本語のフォント (IPAex ゴシック)
W, H = 2500, 843
COLS = [(0, 833), (833, 834), (1667, 833)]  # 3 つのボタンの x と幅
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
font = ImageFont.truetype(FONT_PATH, 110)
small = ImageFont.truetype(FONT_PATH, 56)
for (x, w), label, sub, color in zip(COLS, [LEFT, CENTER, RIGHT], ["WOFF を開く", "ページを開く", "トークに送る"],
                                     ["#00C85F", "#202936", "#5B6475"]):
    d.rounded_rectangle([x + 30, 30, x + w - 30, H - 30], radius=60, fill=color)
    tw = d.textlength(label, font=font)
    d.text((x + (w - tw) / 2, H / 2 - 120), label, font=font, fill="white")
    sw = d.textlength(sub, font=small)
    d.text((x + (w - sw) / 2, H / 2 + 60), sub, font=small, fill="white")
MENU_PNG = WORKDIR / "richmenu.png"
img.save(MENU_PNG)
display(img.resize((W // 4, H // 4)))
print("画像を作りました:", MENU_PNG.name, f"({MENU_PNG.stat().st_size:,} バイト。1 MB 以下ならよい)")
''')

code(r'''
# @title 6-2. メニューを登録して、既定にする
HELP_URL = "https://iwaohig.github.io/lineworks-woff-workshop/"  # @param {type:"string"}
need("MENU_PNG", "先に 6-1 を実行してください")
need("WOFF_ID", "先に 1 を実行してください")
need("BOT_READY", "Bot の認証情報が未設定です。0 の表のシークレットを入れて、0 を実行し直してください")
token = bot_token()
H_ = {"Authorization": f"Bearer {token}"}
BOT = conf["LW_BOT_ID"]

# ① メニューを作る: ボタンの位置 (bounds) と、押したときの動き (action)
menu = {"richmenuName": "勉強会のメニュー", "size": {"width": 2500, "height": 843}, "areas": [
    {"bounds": {"x": x, "y": 0, "width": w, "height": 843}, "action": act}
    for (x, w), act in zip(COLS, [
        {"type": "uri", "label": LEFT, "uri": f"https://woff.worksmobile.com/woff/{WOFF_ID}"},
        {"type": "uri", "label": CENTER, "uri": HELP_URL},
        {"type": "message", "label": RIGHT, "text": RIGHT}])]}
r = requests.post(f"{API}/bots/{BOT}/richmenus", headers=H_, json=menu, timeout=30)
print("① メニューを作る     :", r.status_code)
if r.status_code not in (200, 201):
    raise Stop(f"メニューを作れませんでした: {r.text[:300]}")
RICHMENU_ID = str(r.json()["richmenuId"])

# ② 画像をアップロードする (アップロード先の URL を受け取ってから送る)
r = requests.post(f"{API}/bots/{BOT}/attachments", headers=H_, json={"fileName": "richmenu.png"}, timeout=30)
up = r.json()
r = requests.post(up["uploadUrl"], headers=H_, files={"Filedata": ("richmenu.png", MENU_PNG.read_bytes(), "image/png")},
                  data={"resourceName": "richmenu.png"}, timeout=120)
print("② 画像をアップロード :", r.status_code)

# ③ メニューに画像を付ける → ④ 既定にする (Bot を使う全員に出る)
r = requests.post(f"{API}/bots/{BOT}/richmenus/{RICHMENU_ID}/image", headers=H_, json={"fileId": up["fileId"]}, timeout=30)
print("③ 画像を付ける       :", r.status_code)
r = requests.post(f"{API}/bots/{BOT}/richmenus/{RICHMENU_ID}/set-default", headers=H_, timeout=30)
print("④ 既定にする         :", r.status_code)
print()
print("スマホで Bot とのトークを開き直すと、下にメニューが出ます (richmenuId:", RICHMENU_ID + ")")
''')

code(r'''
# @title 6-3. 作ったメニューを消す (元に戻すとき)
need("RICHMENU_ID", "6-2 で作ったメニューがありません (ランタイムが切れたときは、Bot のメニューは残っています)")
token = bot_token()
r = requests.delete(f"{API}/bots/{conf['LW_BOT_ID']}/richmenus/{RICHMENU_ID}", headers={"Authorization": f"Bearer {token}"}, timeout=30)
print("メニューを消しました" if r.status_code == 204 else f"消せませんでした: {r.status_code} {r.text[:200]}")
RICHMENU_ID = None
''')

md("""
## 7. 作り直したファイルに差し替える

エディターで直して `index.html` をダウンロードし直したら、**1 だけ**を実行し直します。
配信もトンネルもそのままなので、Endpoint URL は変わりません。スマホで WOFF を閉じて、開き直してください。
""")

md("""
## 8. 終わったら止める

トンネルを止めると、Endpoint URL は開けなくなります。
続けて使うなら、`index.html` を GitHub Pages などの置き場所に置き、Endpoint URL をそちらに書き換えます。
""")

code(r'''
# @title 8. トンネルを止める
if globals().get("tunnel") is not None and tunnel.poll() is None:
    tunnel.terminate()
    print("トンネルを止めました")
else:
    print("トンネルは動いていません")
''')

nb = {"cells": cells, "metadata": {"colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"},
                                   "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 0}
OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved", OUT, len(cells), "cells")
