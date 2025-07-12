import os
import sys
import requests
import re
from bs4 import BeautifulSoup
from logging import getLogger, StreamHandler, INFO
from datetime import datetime, timezone, timedelta

# ロガーの設定
logger = getLogger(__name__)
handler = StreamHandler(sys.stdout)
handler.setLevel(INFO)
logger.addHandler(handler)
logger.setLevel(INFO)

# --- 設定項目 ---
# GitHub Actionsの環境変数から取得
DISCORD_WEBHOOK_URLS_REMINDER = os.environ.get("DISCORD_WEBHOOK_URLS_REMINDER", "")

# --- 定数 ---
ATCODER_CONTESTS_URL = "https://atcoder.jp/contests/"


def get_latest_abc_contest() -> dict | None:
    """AtCoderコンテスト一覧ページから最新のABCコンテストの情報を取得する"""
    try:
        res = requests.get(ATCODER_CONTESTS_URL, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # 開催予定のコンテストテーブルを探す
        upcoming_table = soup.find('div', id='contest-table-upcoming')
        if not upcoming_table:
            logger.error("開催予定のコンテストテーブルが見つかりませんでした。")
            return None
            
        table = upcoming_table.find('table')
        if not table:
            logger.error("コンテストテーブルが見つかりませんでした。")
            return None
        
        tbody = table.find('tbody')
        if not tbody:
            logger.error("テーブルボディが見つかりませんでした。")
            return None
            
        rows = tbody.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                # コンテスト名のリンクを取得
                contest_link = cells[1].find('a')
                if contest_link:
                    contest_name = contest_link.get_text(strip=True)
                    contest_url = contest_link.get('href')
                    
                    # ABCコンテストかチェック
                    if re.search(r'AtCoder Beginner Contest \d+|ABC\d+', contest_name, re.IGNORECASE):
                        # 日時を取得
                        date_cell = cells[0].get_text(strip=True)
                        contest_id = contest_url.split('/')[-1] if contest_url else None
                        
                        # 日時をパースしてepoch時間に変換
                        start_epoch = parse_contest_date_to_epoch(date_cell)
                        
                        logger.info(f"最新のABC: {contest_id} ({contest_name})")
                        
                        return {
                            "contest_id": contest_id,
                            "title": contest_name,
                            "start_epoch_second": start_epoch,
                            "duration_second": 6000,  # 100分 = 6000秒（デフォルト）
                            "date_str": date_cell,
                            "contest_url": f"https://atcoder.jp{contest_url}" if contest_url else None
                        }
        
        logger.info("開催予定のABCコンテストが見つかりませんでした。")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"コンテスト情報の取得に失敗しました: {e}")
        return None
    except Exception as e:
        logger.error(f"コンテスト情報の解析に失敗しました: {e}")
        return None


def parse_contest_date_to_epoch(date_str: str) -> int:
    """コンテスト日時文字列をepoch時間に変換"""
    try:
        # 例: "2025-07-12(土) 21:00" の形式をパース
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})\([^)]+\)\s+(\d{1,2}):(\d{2})', date_str)
        if date_match:
            date_part = date_match.group(1)
            hour = int(date_match.group(2))
            minute = int(date_match.group(3))
            
            # JST timezone
            jst = timezone(timedelta(hours=9))
            contest_datetime = datetime.strptime(f"{date_part} {hour:02d}:{minute:02d}", '%Y-%m-%d %H:%M')
            contest_datetime = contest_datetime.replace(tzinfo=jst)
            
            return int(contest_datetime.timestamp())
    except Exception as e:
        logger.warning(f"日時のパースに失敗しました: {date_str}, エラー: {e}")
        
    return 0


def format_contest_time(start_epoch: int, duration: int) -> str:
    """コンテスト開始時刻と終了時刻を日本時間でフォーマット"""
    if start_epoch == 0:
        return "開催時間未定"
    
    # JST timezone
    jst = timezone(timedelta(hours=9))
    
    start_time = datetime.fromtimestamp(start_epoch, tz=jst)
    end_time = start_time + timedelta(seconds=duration)
    
    # 曜日を追加
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    weekday = weekdays[start_time.weekday()]
    
    return f"{start_time.strftime('%Y/%m/%d')}({weekday}) {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"


def format_date_string(date_str: str) -> str:
    """AtCoderから取得した日時文字列を見やすい形式に変換"""
    try:
        # 例: "2025-07-12(土) 21:00" → "2025/07/12(土) 21:00 - 22:40 JST"
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})\(([^)]+)\)\s+(\d{1,2}):(\d{2})', date_str)
        if date_match:
            date_part = date_match.group(1).replace('-', '/')
            day_of_week = date_match.group(2)
            hour = date_match.group(3)
            minute = date_match.group(4)
            
            # 開始時刻
            start_time_str = f"{date_part}({day_of_week}) {hour}:{minute}"
            
            # 終了時刻を計算（100分後）
            start_hour = int(hour)
            start_minute = int(minute)
            total_minutes = start_hour * 60 + start_minute + 100  # 100分後
            end_hour = (total_minutes // 60) % 24
            end_minute = total_minutes % 60
            
            end_time_str = f"{end_hour:02d}:{end_minute:02d}"
            
            return f"{start_time_str} - {end_time_str}"
    except Exception as e:
        logger.warning(f"日時文字列のフォーマットに失敗しました: {date_str}, エラー: {e}")
    
    # フォーマットに失敗した場合は元の文字列を返す
    return date_str


def create_reminder_message(contest_info: dict, message_type: str) -> str:
    """リマインダーメッセージを生成"""
    contest_name = contest_info["title"]
    contest_id = contest_info["contest_id"]
    contest_url = contest_info.get("contest_url", f"https://atcoder.jp/contests/{contest_id}")
    
    # 開催時間を見やすい形式でフォーマット
    if contest_info.get("date_str"):
        # スクレイピングで取得した生の文字列を使用
        contest_time = format_date_string(contest_info["date_str"])
    else:
        # epoch時間から変換
        contest_time = format_contest_time(
            contest_info["start_epoch_second"], 
            contest_info["duration_second"]
        )
    
    if message_type == "morning":
        message = f"🌅 おはようございます！今日は{contest_name}が開催されます！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    elif message_type == "evening":
        message = f"🌙 お疲れ様です！{contest_name}が開催中または間もなく開始です！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    else:
        message = f"📢 {contest_name}のリマインドです！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    
    return message


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
    """複数のDiscord Webhookにリマインダー通知を送信する"""
    webhook_urls = parse_webhook_urls(DISCORD_WEBHOOK_URLS_REMINDER)
    
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


def get_current_message_type() -> str:
    """現在の時刻に基づいてメッセージタイプを決定"""
    from datetime import datetime, timezone, timedelta
    
    # JST
    jst = timezone(timedelta(hours=9))
    current_hour = datetime.now(jst).hour
    
    if current_hour == 12:
        return "morning"
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
    success = send_discord_notifications(message)
    
    if success:
        logger.info("リマインダー処理が正常に完了しました。")
    else:
        logger.error("リマインダー処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == "__main__":
    main()