import os
import re
import sys
import requests
import json
from bs4 import BeautifulSoup
from logging import getLogger, StreamHandler, INFO

# ロガーの設定
logger = getLogger(__name__)
handler = StreamHandler(sys.stdout)
handler.setLevel(INFO)
logger.addHandler(handler)
logger.setLevel(INFO)

# --- 設定項目 ---
# GitHub Actionsの環境変数から取得
ATCODER_USER_ID = os.environ.get("ATCODER_USER_ID")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# --- 定数 ---
ATCODER_HISTORY_URL = f"https://atcoder.jp/users/{ATCODER_USER_ID}/history"
STATE_FILE = "last_contest.txt"  # 最後に通知したコンテスト情報を保存するファイル

def get_last_notified_contest() -> str | None:
    """キャッシュファイルから最後に通知したコンテストIDを読み込む"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_notified_contest(contest_id: str):
    """最新のコンテストIDをキャッシュファイルに書き込む"""
    with open(STATE_FILE, "w") as f:
        f.write(contest_id)
    logger.info(f"状態を更新しました: {contest_id}")

def get_latest_contest_from_history() -> dict | None:
    """AtCoderの履歴ページから最新のコンテスト情報を取得する"""
    try:
        res = requests.get(ATCODER_HISTORY_URL)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"履歴ページの取得に失敗しました: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    history_table = soup.find("table", {"id": "history"})
    if not history_table:
        logger.info("コンテスト履歴が見つかりませんでした。")
        return None
    
    # 最新の履歴は最初の行にある
    latest_row = history_table.find("tbody").find("tr")
    if not latest_row:
        logger.info("コンテスト履歴のデータ行が見つかりませんでした。")
        return None
        
    columns = latest_row.find_all("td")
    
    # レートに変動があったか確認する
    # 'New Rating' - 'Old Rating' != 0
    try:
        # 「-」の場合はUnratedなので0として扱う
        old_rating = int(columns[4].text) if columns[4].text != "-" else 0
        new_rating = int(columns[5].text) if columns[5].text != "-" else 0
        is_rated = old_rating != new_rating
    except (ValueError, IndexError):
        is_rated = False

    # 共有ページのURLからコンテストIDを抽出
    share_link = columns[6].find("a")
    if not share_link or "href" not in share_link.attrs:
        return None
        
    contest_id_match = re.search(r"/history/share/([^?]+)", share_link["href"])
    if not contest_id_match:
        return None

    return {
        "contest_id": contest_id_match.group(1),
        "share_url": f"https://atcoder.jp{share_link['href']}",
        "is_rated": is_rated,
    }

def scrape_share_page_message(share_url: str) -> str | None:
    """共有ページから通知用のメッセージ本文を抽出する"""
    try:
        res = requests.get(share_url)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"共有ページの取得に失敗しました: {e}")
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    panel_body = soup.find("div", class_="panel-body")
    if not panel_body:
        return None
        
    # get_textでテキストを抽出し、余分な空白を整理
    lines = [line.strip() for line in panel_body.get_text(separator="\n").splitlines() if line.strip()]
    return "\n".join(lines)


def send_discord_notification(message: str):
    """Discord Webhookに通知を送信する"""
    payload = {
        "content": message
    }
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        res.raise_for_status()
        logger.info("Discordへの通知に成功しました。")
    except requests.exceptions.RequestException as e:
        logger.error(f"Discordへの通知に失敗しました: {e}")


def main():
    """メイン処理"""
    if not ATCODER_USER_ID or not DISCORD_WEBHOOK_URL:
        logger.error("環境変数 ATCODER_USER_ID または DISCORD_WEBHOOK_URL が設定されていません。")
        sys.exit(1)

    logger.info(f"ユーザー '{ATCODER_USER_ID}' のレート更新チェックを開始します。")

    # 1. 最新のコンテスト情報を取得
    latest_contest = get_latest_contest_from_history()
    if not latest_contest:
        logger.info("処理対象のコンテストがありませんでした。")
        sys.exit(0)
    
    latest_contest_id = latest_contest["contest_id"]
    
    # 2. 最後に通知したコンテストと比較
    last_notified_id = get_last_notified_contest()
    if latest_contest_id == last_notified_id:
        logger.info("新しいコンテスト結果はありません。処理を終了します。")
        sys.exit(0)

    logger.info(f"新しいコンテスト結果が見つかりました: {latest_contest_id}")

    # 3. 状態を先に更新する（重複通知を確実に防ぐため）
    save_last_notified_contest(latest_contest_id)

    # 4. レート変動がない場合は通知しない
    if not latest_contest["is_rated"]:
        logger.info("レート変動がなかったため、通知はスキップします。")
        sys.exit(0)

    # 5. 通知メッセージを生成
    message_body = scrape_share_page_message(latest_contest["share_url"])
    if not message_body:
        logger.error("共有ページからメッセージ本文を抽出できませんでした。")
        sys.exit(1)

    # コンテストIDからハッシュタグを生成（例: abc413 -> #ABC413）
    contest_hashtag_name = latest_contest_id.upper()
    
    # 最終的なメッセージを組み立て
    final_message = (
        f"{message_body}\n"
        f"#AtCoder #{contest_hashtag_name} {latest_contest['share_url']}"
    )

    # 6. Discordに通知
    send_discord_notification(final_message)
    logger.info("処理が正常に完了しました。")

if __name__ == "__main__":
    main()