import json
import os
from urllib.parse import urljoin

import requests
from playwright.sync_api import sync_playwright


# ==========================================
# 設定
# ==========================================

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

MAPLE_URL = "https://maplestory.nexon.co.jp/notice/all/"

HISTORY_FILE = "maple_history.json"


# ==========================================
# カテゴリごとの色
# ==========================================

CATEGORY_COLORS = {
    "イベント": 0x57F287,
    "メンテナンス": 0xED4245,
    "アップデート": 0x5865F2,
    "ショップ": 0x9B59B6,
    "お知らせ": 0xF1C40F,
}


CATEGORY_EMOJI = {
    "イベント": "🎉",
    "メンテナンス": "🛠️",
    "アップデート": "🔵",
    "ショップ": "🛒",
    "お知らせ": "📢",
}


# ==========================================
# お知らせ一覧を取得
# ==========================================

def get_notices():

    notices = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        print("メイプル公式サイトを確認中...")

        page.goto(
            MAPLE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(5000)

        links = page.locator('a[href*="/notice/view/"]')

        count = links.count()

        for i in range(count):

            try:

                link = links.nth(i)

                title = link.inner_text().strip()

                href = link.get_attribute("href")

                if not title or not href:
                    continue

                url = urljoin(MAPLE_URL, href)

                if any(n["url"] == url for n in notices):
                    continue

                notices.append({
                    "title": title,
                    "url": url
                })

            except Exception:
                pass

        browser.close()

    return notices


# ==========================================
# カテゴリ判定
# ==========================================

def detect_category(title):

    categories = [
        "メンテナンス",
        "アップデート",
        "イベント",
        "ショップ"
    ]

    for category in categories:

        if category in title:
            return category

    return "お知らせ"


# ==========================================
# Discordへ送信
# ==========================================

def send_discord(notice):

    title = notice["title"]
    url = notice["url"]

    category = detect_category(title)

    color = CATEGORY_COLORS.get(
        category,
        0x95A5A6
    )

    emoji = CATEGORY_EMOJI.get(
        category,
        "🍁"
    )

    data = {

        "username": "メイプル公式情報",

        "embeds": [
            {
                "author": {
                    "name": "MapleStory 公式お知らせ"
                },

                "title": title,

                "url": url,

                "description":
                    f"{emoji} **{category}**\n\n"
                    f"🔗 タイトルをクリックすると公式サイトを開けます。",

                "color": color,

                "footer": {
                    "text": "MapleStory公式サイト 新着情報"
                }
            }
        ]
    }

    response = requests.post(
        WEBHOOK_URL,
        json=data,
        timeout=30
    )

    response.raise_for_status()

    print(
        f"Discordへ投稿しました：{title}"
    )


# ==========================================
# 履歴読み込み
# ==========================================

def load_history():

    if not os.path.exists(HISTORY_FILE):
        return []

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return []


# ==========================================
# 履歴保存
# ==========================================

def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )


# ==========================================
# メイン
# ==========================================

def main():

    print("==============================")
    print("メイプル公式お知らせ確認開始")
    print("==============================")

    notices = get_notices()

    print(
        f"{len(notices)}件のお知らせを取得しました"
    )

    history = load_history()

    # ======================================
    # 初回
    # ======================================

    if not history:

        print("初回起動です。")

        print(
            "現在の記事を履歴に登録します。"
        )

        history = [
            notice["url"]
            for notice in notices
        ]

        save_history(history)

        print(
            "登録完了。今回はDiscordへ投稿しません。"
        )

        return


    # ======================================
    # 新着確認
    # ======================================

    new_notices = [

        notice

        for notice in notices

        if notice["url"] not in history

    ]


    if not new_notices:

        print(
            "新しいお知らせはありません。"
        )

        return


    print(
        f"{len(new_notices)}件の新着を発見しました。"
    )


    # 古いものから投稿

    for notice in reversed(new_notices):

        send_discord(notice)

        history.append(
            notice["url"]
        )


    save_history(history)


if __name__ == "__main__":

    main()
