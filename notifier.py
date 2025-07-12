import os
import re
import sys
import requests
import json
from bs4 import BeautifulSoup
from logging import getLogger, StreamHandler, INFO

# AtCoderレーティング変動通知スクリプト
# ユーザーのレーティング変動を検出してDiscordに通知する

# ロガーの設定
logger = getLogger(__name__)
handler = StreamHandler(sys.stdout)
handler.setLevel(INFO)
logger.addHandler(handler)
logger.setLevel(INFO)

# --- 設定項目 ---
# GitHub Actionsの環境変数から取得
ATCODER_USER_ID = os.environ.get("ATCODER_USER_ID")
DISCORD_WEBHOOK_URLS_NOTIFIER = os.environ.get("DISCORD_WEBHOOK_URLS_NOTIFIER", "")

# --- 定数 ---
CONTESTS_API_URL = "https://kenkoooo.com/atcoder/resources/contests.json"
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


def get_latest_abc_contest() -> dict | None:
    """kenkoooo APIから最新のAtCoder Beginner Contestの情報を取得する"""
    try:
        res = requests.get(CONTESTS_API_URL)
        res.raise_for_status()
        contests = res.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"コンテスト情報の取得に失敗しました: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSONの解析に失敗しました: {e}")
        return None

    # AtCoder Beginner Contestのみを抽出し、開始時刻でソート（降順）
    abc_contests = [
        contest
        for contest in contests
        if contest["id"].startswith("abc") and contest["start_epoch_second"] > 0
    ]

    if not abc_contests:
        logger.info("AtCoder Beginner Contestが見つかりませんでした。")
        return None

    # 開始時刻でソートして最新のコンテストを取得
    abc_contests.sort(key=lambda x: x["start_epoch_second"], reverse=True)
    latest_abc = abc_contests[0]

    logger.info(f"最新のABC: {latest_abc['id']} ({latest_abc['title']})")

    return {
        "contest_id": latest_abc["id"],
        "title": latest_abc["title"],
        "start_epoch_second": latest_abc["start_epoch_second"],
        "duration_second": latest_abc["duration_second"],
        "rate_change": latest_abc.get("rate_change", "All"),
    }


def check_user_rating_change(contest_id: str) -> dict | None:
    """ユーザーの指定コンテストでのレーティング変動を確認する"""
    # 直接共有ページURLを構築してアクセスを試行
    share_url = f"https://atcoder.jp/users/{ATCODER_USER_ID}/history/share/{contest_id}"
    
    try:
        logger.info(f"共有ページにアクセス中: {share_url}")
        res = requests.get(share_url)
        
        # 404の場合はコンテストに参加していない
        if res.status_code == 404:
            logger.info(f"コンテスト {contest_id} に参加していません（404エラー）")
            return None
        
        res.raise_for_status()
        
        # 共有ページが存在する場合、履歴ページからレート変動を取得
        return get_rating_change_from_history(contest_id, share_url)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"共有ページへのアクセスに失敗しました: {e}")
        return None

def get_rating_change_from_history(contest_id: str, share_url: str) -> dict | None:
    """履歴ページから指定コンテストのレート変動を取得"""
    try:
        res = requests.get(ATCODER_HISTORY_URL)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        history_table = soup.find("table", {"id": "history"})
        if not history_table:
            logger.info("履歴テーブルが見つかりませんでした。")
            return None

        tbody = history_table.find("tbody")
        if not tbody:
            logger.info("履歴テーブルのtbodyが見つかりませんでした。")
            return None

        # 各行をチェックして指定されたコンテストを探す
        for row in tbody.find_all("tr"):
            columns = row.find_all("td")
            if len(columns) >= 7:
                # コンテスト名から一致するものを探す
                contest_cell = columns[1]
                contest_link = contest_cell.find("a")
                if contest_link and contest_id in contest_link.get("href", ""):
                    # レート変動を確認
                    try:
                        old_rating_text = columns[4].get_text().strip()
                        new_rating_text = columns[5].get_text().strip()

                        old_rating = (
                            int(old_rating_text) if old_rating_text != "-" else 0
                        )
                        new_rating = (
                            int(new_rating_text) if new_rating_text != "-" else 0
                        )
                        rating_change = new_rating - old_rating

                        logger.info(
                            f"レート変動: {old_rating} -> {new_rating} (差分: {rating_change})"
                        )

                        return {
                            "contest_id": contest_id,
                            "old_rating": old_rating,
                            "new_rating": new_rating,
                            "rating_change": rating_change,
                            "is_rated": rating_change != 0,
                            "share_url": share_url,
                        }
                    except (ValueError, IndexError) as e:
                        logger.error(f"レート解析エラー: {e}")
                        continue

        logger.info(f"履歴テーブルでコンテスト {contest_id} が見つかりませんでした。")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"履歴ページの取得に失敗しました: {e}")
        return None


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
    lines = [
        line.strip()
        for line in panel_body.get_text(separator="\n").splitlines()
        if line.strip()
    ]
    return "\n".join(lines)

def convert_grade_to_japanese(grade: str) -> str:
    """AtCoderの級・段を日本語に変換する（例: 8 Kyu -> 8級, 1 Dan -> 1段）"""
    if not grade:
        return grade
    
    # Kyuを級に変換
    grade = re.sub(r'(\d+)\s*Kyu', r'\1級', grade)
    # Danを段に変換
    grade = re.sub(r'(\d+)\s*Dan', r'\1段', grade)
    
    return grade

def parse_contest_result(raw_message: str, contest_info: dict, share_url: str) -> str:
    """共有ページのメッセージを解析して理想的なフォーマットに変換する"""
    lines = raw_message.split('\n')
    
    # 各情報を抽出
    contest_name = ""
    rank = ""
    performance = ""
    old_rating = ""
    new_rating = ""
    rating_change = ""
    old_grade = ""
    new_grade = ""
    is_highest = False
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line == "Contest Name" and i + 1 < len(lines):
            contest_name = lines[i + 1].strip()
            i += 2
        elif line == "Rank" and i + 2 < len(lines):
            rank_line = lines[i + 1].strip()
            # "4219th" から "4219位" に変換
            rank = re.sub(r'(\d+)(st|nd|rd|th)', r'\1位', rank_line)
            i += 3
        elif line == "Performance" and i + 1 < len(lines):
            performance = lines[i + 1].strip()
            i += 2
        elif line == "Rating Change" and i + 3 < len(lines):
            old_rating = lines[i + 1].strip()
            new_rating = lines[i + 3].strip()
            rating_change_line = lines[i + 4].strip() if i + 4 < len(lines) else ""
            # (+51) 形式から数値を抽出
            change_match = re.search(r'\(([\+\-]\d+)\)', rating_change_line)
            if change_match:
                rating_change = change_match.group(1)
            i += 5
        elif line == "Highest!" or "Highest" in line:
            is_highest = True
            i += 1
        elif line == "Grading" and i + 3 < len(lines):
            old_grade = convert_grade_to_japanese(lines[i + 1].strip())
            new_grade = convert_grade_to_japanese(lines[i + 3].strip())
            i += 4
        else:
            i += 1
    
    # 絵文字を選択（レーティング変動に基づく）
    emoji = ""
    if rating_change:
        change_value = int(rating_change.replace('+', ''))
        if change_value > 0:
            emoji = "🙂"
        elif change_value < 0:
            emoji = "😞"
        else:
            emoji = "😐"
    
    # メッセージを構築
    message_parts = []
    
    # 1行目：基本成績
    if contest_name and rank:
        message_parts.append(f"{ATCODER_USER_ID}さんの{contest_name}での成績：{rank}")
    
    # 2行目：パフォーマンス
    if performance:
        message_parts.append(f"パフォーマンス：{performance}相当")
    
    # 3行目：レーティング
    if old_rating and new_rating and rating_change:
        rating_line = f"レーティング：{old_rating}→{new_rating} ({rating_change}) {emoji}"
        message_parts.append(rating_line)
    
    # 4行目：級の変化とHighest
    grade_info = []
    if is_highest:
        grade_info.append("Highestを更新し")
    if new_grade:
        grade_info.append(f"{new_grade}になりました！")
    
    if grade_info:
        message_parts.append("".join(grade_info))
    
    # ハッシュタグとURL
    contest_hashtag = f"#{contest_info['contest_id'].upper()}"
    if contest_name:
        # コンテスト名から適切なハッシュタグを生成
        clean_contest_name = re.sub(r'[（）()]', '', contest_name)
        contest_hashtag = f"#{clean_contest_name}（{contest_info['contest_id'].upper()}）"
    
    share_url_with_lang = f"{share_url}?lang=ja"
    message_parts.append(f"#AtCoder {contest_hashtag} {share_url_with_lang}")
    
    return "\n".join(message_parts)


def parse_webhook_urls(webhook_urls_str: str) -> list[str]:
    """webhook URL文字列をパースして有効なURLのリストを返す"""
    if not webhook_urls_str:
        return []
    
    # カンマ、セミコロン、改行で分割
    urls = []
    for url in webhook_urls_str.replace(';', ',').replace('\n', ',').split(','):
        url = url.strip()
        if url and url.startswith('https://'):
            urls.append(url)
    
    return urls


def send_discord_notifications(message: str) -> bool:
    """複数のDiscord Webhookにレーティング変動通知を送信する"""
    webhook_urls = parse_webhook_urls(DISCORD_WEBHOOK_URLS_NOTIFIER)
    
    if not webhook_urls:
        logger.error("有効なDiscord webhook URLが設定されていません。")
        return False
    
    payload = {"content": message}
    success_count = 0
    
    for i, webhook_url in enumerate(webhook_urls, 1):
        try:
            res = requests.post(webhook_url, json=payload, timeout=10)
            res.raise_for_status()
            logger.info(f"Discord通知 {i}/{len(webhook_urls)} に成功しました。")
            success_count += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"Discord通知 {i}/{len(webhook_urls)} に失敗しました: {e}")
    
    if success_count > 0:
        logger.info(f"Discord通知: {success_count}/{len(webhook_urls)} 件が成功しました。")
        return True
    else:
        logger.error("すべてのDiscord通知が失敗しました。")
        return False


def main():
    """レーティング変動通知のメイン処理"""
    if not ATCODER_USER_ID or not DISCORD_WEBHOOK_URLS_NOTIFIER:
        logger.error(
            "環境変数 ATCODER_USER_ID または DISCORD_WEBHOOK_URLS_NOTIFIER が設定されていません。"
        )
        sys.exit(1)

    logger.info(f"ユーザー '{ATCODER_USER_ID}' のレート更新チェックを開始します。")

    # 1. 最新のAtCoder Beginner Contest情報を取得
    latest_abc = get_latest_abc_contest()
    if not latest_abc:
        logger.info("最新のABC情報が取得できませんでした。")
        sys.exit(0)

    latest_contest_id = latest_abc["contest_id"]
    logger.info(f"最新のABC: {latest_contest_id}")

    # 2. 最後に通知したコンテストと比較
    last_notified_id = get_last_notified_contest()
    if latest_contest_id == last_notified_id:
        logger.info("新しいコンテスト結果はありません。処理を終了します。")
        sys.exit(0)

    logger.info(f"新しいコンテスト結果をチェックします: {latest_contest_id}")

    # 3. ユーザーの該当コンテストでのレート変動を確認
    rating_info = check_user_rating_change(latest_contest_id)
    if not rating_info:
        logger.info(
            f"コンテスト {latest_contest_id} での参加情報が見つかりませんでした。"
        )
        # 状態を更新して次回チェックしないようにする
        save_last_notified_contest(latest_contest_id)
        sys.exit(0)

    # 4. 状態を更新する（重複通知を防ぐため）
    save_last_notified_contest(latest_contest_id)

    # 5. レート変動がない場合は通知しない
    if not rating_info["is_rated"]:
        logger.info("レート変動がなかったため、通知はスキップします。")
        sys.exit(0)

    logger.info(f"レート変動が検出されました: {rating_info['rating_change']}")

    # 6. 通知メッセージを生成
    if rating_info["share_url"]:
        raw_message = scrape_share_page_message(rating_info["share_url"])
        if raw_message:
            # 共有ページからメッセージを取得できた場合、理想的なフォーマットに変換
            final_message = parse_contest_result(raw_message, latest_abc, rating_info["share_url"])
        else:
            # 共有ページからメッセージを取得できなかった場合の代替メッセージ
            final_message = create_fallback_message(latest_abc, rating_info)
    else:
        # 共有URLがない場合の代替メッセージ
        final_message = create_fallback_message(latest_abc, rating_info)

    # 7. Discordに通知
    success = send_discord_notifications(final_message)
    if success:
        logger.info("処理が正常に完了しました。")
    else:
        logger.error("通知の送信に失敗しました。")
        sys.exit(1)


def create_fallback_message(contest_info: dict, rating_info: dict) -> str:
    """共有ページが利用できない場合の代替メッセージを生成"""
    rating_change = rating_info["rating_change"]
    change_text = f"+{rating_change}" if rating_change > 0 else str(rating_change)
    
    # 絵文字を選択
    emoji = ""
    if rating_change > 0:
        emoji = "🙂"
    elif rating_change < 0:
        emoji = "😞"
    else:
        emoji = "😐"
    
    # 理想的なフォーマットに近い形で生成
    message_parts = [
        f"{ATCODER_USER_ID}さんの{contest_info['title']}に参加しました！",
        f"レーティング：{rating_info['old_rating']}→{rating_info['new_rating']} ({change_text}) {emoji}",
        f"#AtCoder #{contest_info['contest_id'].upper()}"
    ]
    
    if rating_info.get("share_url"):
        share_url_with_lang = f"{rating_info['share_url']}?lang=ja"
        message_parts[-1] += f" {share_url_with_lang}"
    
    return "\n".join(message_parts)


if __name__ == "__main__":
    main()
