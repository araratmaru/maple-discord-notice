import json
import os
from urllib.parse import urljoin

import requests
from playwright.sync_api import sync_playwright


# ==========================================
# 設定
# ==========================================

WEBHOOK_URL = os.environ["https://discord.com/api/webhooks/1539720878655410297/HHaoJvXK2JxUbIo2roLkym9xll2_V9lxmTl66kwCnSKb7frE1xzmFi-GfipYNPpilUWE"]

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
# 公式サイトからお知らせ一覧を取得
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

                # 同じURLを重複登録しない
                if any(
                    notice["url"] == url
                    for notice in notices
                ):
                    continue

                notices.append({
                    "title": title,
                    "url": url
                })

            except Exception as e:

                print(
                    "記事取得エラー：",
                    e
                )

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
# Discord 新着通知
# ==========================================

def send_new_notice(notice):

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
                    "name":
                    "🆕 MapleStory 新着お知らせ"
                },

                "title": title,

                "url": url,

                "description":
                    f"{emoji} **{category}**\n\n"
                    "新しいお知らせが掲載されました。\n\n"
                    "🔗 タイトルをクリックすると"
                    "公式サイトを開けます。",

                "color": color,

                "footer": {
                    "text":
                    "MapleStory公式サイト 新着情報"
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
        f"🆕 新着通知：{title}"
    )


# ==========================================
# Discord 更新通知
# ==========================================

def send_update_notice(old_notice, new_notice):

    old_title = old_notice["title"]

    new_title = new_notice["title"]

    url = new_notice["url"]

    category = detect_category(new_title)

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
                    "name":
                    "🔄 MapleStory お知らせ更新"
                },

                "title": new_title,

                "url": url,

                "description":
                    f"{emoji} **{category}**\n\n"
                    "公式のお知らせが更新されました。\n\n"
                    f"**更新前**\n{old_title}\n\n"
                    f"**更新後**\n{new_title}\n\n"
                    "🔗 タイトルをクリックすると"
                    "公式サイトを開けます。",

                # 更新通知はオレンジ
                "color": 0xE67E22,

                "footer": {
                    "text":
                    "MapleStory公式サイト 更新情報"
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
        "🔄 更新を検出しました："
    )

    print(
        f"   {old_title}"
    )

    print(
        "   ↓"
    )

    print(
        f"   {new_title}"
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

            history = json.load(f)

    except Exception:

        return []

    # --------------------------------------
    # 古いURLだけの形式だった場合
    # --------------------------------------

    if history and isinstance(history[0], str):

        print(
            "古い履歴形式を検出しました。"
        )

        print(
            "新しい形式へ移行します。"
        )

        return [
            {
                "url": url,
                "title": None
            }
            for url in history
        ]

    return history


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

    print(
        "=============================="
    )

    print(
        "🍁 メイプル公式お知らせ確認開始"
    )

    print(
        "=============================="
    )

    notices = get_notices()

    print(
        f"{len(notices)}件のお知らせを取得しました"
    )

    history = load_history()


    # ======================================
    # 履歴が完全に空の場合
    # ======================================

    if not history:

        print(
            "初回起動です。"
        )

        print(
            "現在の記事を履歴へ登録します。"
        )

        save_history(notices)

        print(
            "登録完了。"
        )

        print(
            "今回はDiscordへ投稿しません。"
        )

        return


    # ======================================
    # URLをキーにした辞書を作成
    # ======================================

    history_dict = {

        item["url"]: item

        for item in history

    }


    new_count = 0

    update_count = 0


    # ======================================
    # 現在の記事をチェック
    # ======================================

    for notice in reversed(notices):

        url = notice["url"]

        title = notice["title"]


        # ----------------------------------
        # 新しいURL
        # ----------------------------------

        if url not in history_dict:

            send_new_notice(
                notice
            )

            history.append(
                notice
            )

            history_dict[url] = notice

            new_count += 1

            continue


        # ----------------------------------
        # 既存URL
        # ----------------------------------

        old_notice = history_dict[url]

        old_title = old_notice.get(
            "title"
        )


        # 古い履歴形式から移行した直後
        if old_title is None:

            old_notice["title"] = title

            continue


        # ----------------------------------
        # タイトル変更を検出
        # ----------------------------------

        if old_title != title:

            send_update_notice(
                old_notice,
                notice
            )

            old_notice["title"] = title

            update_count += 1


    # ======================================
    # 履歴保存
    # ======================================

    save_history(history)


    print()

    print(
        "確認完了"
    )

    print(
        f"🆕 新着：{new_count}件"
    )

    print(
        f"🔄 更新：{update_count}件"
    )


if __name__ == "__main__":

    main()
