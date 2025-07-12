import os
import sys
import requests
import json
from logging import getLogger, StreamHandler, INFO
from datetime import datetime

# ロガーの設定
logger = getLogger(__name__)
handler = StreamHandler(sys.stdout)
handler.setLevel(INFO)
logger.addHandler(handler)
logger.setLevel(INFO)

# --- 設定項目 ---
# GitHub Actionsの環境変数から取得
DISCORD_WEBHOOK_URL_REMINDER = os.environ.get("DISCORD_WEBHOOK_URL_REMINDER")

# --- 定数 ---
CONTESTS_API_URL = "https://kenkoooo.com/atcoder/resources/contests.json"


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


def format_contest_time(start_epoch: int, duration: int) -> str:
    """コンテスト開始時刻と終了時刻を日本時間でフォーマット"""
    from datetime import datetime, timedelta, timezone
    
    # JST timezone
    jst = timezone(timedelta(hours=9))
    
    start_time = datetime.fromtimestamp(start_epoch, tz=jst)
    end_time = start_time + timedelta(seconds=duration)
    
    return f"{start_time.strftime('%Y/%m/%d %H:%M')} - {end_time.strftime('%H:%M')} JST"


def create_reminder_message(contest_info: dict, message_type: str) -> str:
    """リマインダーメッセージを生成"""
    contest_name = contest_info["title"]
    contest_id = contest_info["contest_id"]
    contest_url = f"https://atcoder.jp/contests/{contest_id}"
    contest_time = format_contest_time(
        contest_info["start_epoch_second"], 
        contest_info["duration_second"]
    )
    
    if message_type == "morning":
        message = f"🌅 おはようございます！今日は{contest_name}が開催されます！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    elif message_type == "afternoon":
        message = f"☀️ こんにちは！{contest_name}の開催まであと少しです！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    elif message_type == "evening":
        message = f"🌙 お疲れ様です！{contest_name}が開催中または間もなく開始です！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    else:
        message = f"📢 {contest_name}のリマインドです！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    
    return message


def send_discord_notification(message: str):
    """Discord Webhookに通知を送信する"""
    if not DISCORD_WEBHOOK_URL_REMINDER:
        logger.error("DISCORD_WEBHOOK_URL_REMINDER が設定されていません。")
        return False
    
    payload = {"content": message}
    try:
        res = requests.post(DISCORD_WEBHOOK_URL_REMINDER, json=payload, timeout=10)
        res.raise_for_status()
        logger.info("Discordへの通知に成功しました。")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Discordへの通知に失敗しました: {e}")
        return False


def get_current_message_type() -> str:
    """現在の時刻に基づいてメッセージタイプを決定"""
    from datetime import datetime, timezone, timedelta
    
    # JST
    jst = timezone(timedelta(hours=9))
    current_hour = datetime.now(jst).hour
    
    if current_hour == 12:
        return "morning"
    elif current_hour == 16:
        return "afternoon"
    elif current_hour == 20:
        return "evening"
    else:
        return "default"


def main():
    """メイン処理"""
    logger.info("ABC コンテストリマインダーを開始します。")
    
    # 最新のABCコンテスト情報を取得
    contest_info = get_latest_abc_contest()
    if not contest_info:
        logger.info("最新のABC情報が取得できませんでした。")
        sys.exit(0)
    
    # メッセージタイプを決定
    message_type = get_current_message_type()
    
    # リマインダーメッセージを生成
    message = create_reminder_message(contest_info, message_type)
    
    # Discord通知を送信
    success = send_discord_notification(message)
    
    if success:
        logger.info("リマインダー処理が正常に完了しました。")
    else:
        logger.error("リマインダー処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == "__main__":
    main()