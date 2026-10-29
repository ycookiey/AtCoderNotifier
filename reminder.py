import os
import sys
import requests
import re
from bs4 import BeautifulSoup
from logging import getLogger, StreamHandler, INFO
from datetime import datetime, timezone, timedelta

logger = getLogger(__name__)
handler = StreamHandler(sys.stdout)
handler.setLevel(INFO)
logger.addHandler(handler)
logger.setLevel(INFO)

# --- 設定項目 ---
DISCORD_WEBHOOK_URLS_REMINDER = os.environ.get("DISCORD_WEBHOOK_URLS_REMINDER", "")

# --- 定数 ---
ATCODER_CONTESTS_URL = "https://atcoder.jp/contests/"


def get_latest_abc_contest() -> dict | None:
    """AtCoderコンテスト一覧ページから最新のABCコンテストの情報を取得する"""
    try:
        res = requests.get(ATCODER_CONTESTS_URL, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.content, 'html.parser')
        
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
                contest_link = cells[1].find('a')
                if contest_link:
                    contest_name = contest_link.get_text(strip=True)
                    contest_url = contest_link.get('href')
                    
                    if re.search(r'AtCoder Beginner Contest \d+|ABC\d+', contest_name, re.IGNORECASE):
                        date_cell = cells[0].get_text(strip=True)
                        contest_id = contest_url.split('/')[-1] if contest_url else None
                        
                        start_epoch = parse_contest_date_to_epoch(date_cell)
                        
                        logger.info(f"最新のABC: {contest_id} ({contest_name})")
                        
                        return {
                            "contest_id": contest_id,
                            "title": contest_name,
                            "start_epoch_second": start_epoch,
                            "duration_second": 6000,  # 一覧のページから時間を読まないので、ABCの標準の100分とする
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
        # パターン1: "2025-07-12(土) 21:00" の形式をパース
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})\([^)]+\)\s+(\d{1,2}):(\d{2})', date_str)
        if date_match:
            date_part = date_match.group(1)
            hour = int(date_match.group(2))
            minute = int(date_match.group(3))
            
            jst = timezone(timedelta(hours=9))
            contest_datetime = datetime.strptime(f"{date_part} {hour:02d}:{minute:02d}", '%Y-%m-%d %H:%M')
            contest_datetime = contest_datetime.replace(tzinfo=jst)
            
            return int(contest_datetime.timestamp())
        
        # パターン2: "2025-07-12 21:00:00+0900" の形式をパース
        iso_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2}):\d{2}[+-]\d{4}', date_str)
        if iso_match:
            date_part = iso_match.group(1)
            hour = int(iso_match.group(2))
            minute = int(iso_match.group(3))
            
            jst = timezone(timedelta(hours=9))
            contest_datetime = datetime.strptime(f"{date_part} {hour:02d}:{minute:02d}", '%Y-%m-%d %H:%M')
            contest_datetime = contest_datetime.replace(tzinfo=jst)
            
            return int(contest_datetime.timestamp())
            
    except Exception as e:
        logger.warning(f"日時のパースに失敗しました: {date_str}, エラー: {e}")
        
    return 0


def format_contest_time_discord(start_epoch: int, duration: int) -> str:
    """コンテスト開始時刻と終了時刻をDiscordタイムスタンプ形式でフォーマット"""
    if start_epoch == 0:
        return "開催時間未定"
    
    end_epoch = start_epoch + duration
    
    # Discordタイムスタンプ形式: <t:epoch:f> (full format)
    return f"<t:{start_epoch}:f> - <t:{end_epoch}:t>"

def format_contest_time(start_epoch: int, duration: int) -> str:
    """コンテスト開始時刻と終了時刻を日本時間でフォーマット"""
    if start_epoch == 0:
        return "開催時間未定"
    
    jst = timezone(timedelta(hours=9))
    
    start_time = datetime.fromtimestamp(start_epoch, tz=jst)
    end_time = start_time + timedelta(seconds=duration)
    
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    weekday = weekdays[start_time.weekday()]
    
    return f"{start_time.strftime('%Y/%m/%d')}({weekday}) {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"


def format_date_string_discord(date_str: str) -> str:
    """AtCoderから取得した日時文字列をDiscordタイムスタンプ形式に変換"""
    try:
        # パターン1: "2025-07-12(土) 21:00" 形式
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})\(([^)]+)\)\s+(\d{1,2}):(\d{2})', date_str)
        if date_match:
            date_part = date_match.group(1)
            hour = int(date_match.group(3))
            minute = int(date_match.group(4))
            
            jst = timezone(timedelta(hours=9))
            year, month, day = map(int, date_part.split('-'))
            contest_start = datetime(year, month, day, hour, minute, tzinfo=jst)
            contest_end = contest_start + timedelta(minutes=100)
            
            start_epoch = int(contest_start.timestamp())
            end_epoch = int(contest_end.timestamp())
            
            return f"<t:{start_epoch}:f> - <t:{end_epoch}:t>"
        
        # パターン2: "2025-07-12 21:00:00+0900" 形式
        iso_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2}):\d{2}[+-]\d{4}', date_str)
        if iso_match:
            date_part = iso_match.group(1)
            hour = int(iso_match.group(2))
            minute = int(iso_match.group(3))
            
            jst = timezone(timedelta(hours=9))
            year, month, day = map(int, date_part.split('-'))
            contest_start = datetime(year, month, day, hour, minute, tzinfo=jst)
            contest_end = contest_start + timedelta(minutes=100)
            
            start_epoch = int(contest_start.timestamp())
            end_epoch = int(contest_end.timestamp())
            
            return f"<t:{start_epoch}:f> - <t:{end_epoch}:t>"
            
    except Exception as e:
        logger.warning(f"Discordタイムスタンプの生成に失敗: {date_str}, エラー: {e}")
    
    # Discordのタイムスタンプにできないときは、日時の文字列で表す
    return format_date_string(date_str)

def format_date_string(date_str: str) -> str:
    """AtCoderから取得した日時文字列を見やすい形式に変換"""
    try:
        # パターン1: "2025-07-12(土) 21:00" 形式
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})\(([^)]+)\)\s+(\d{1,2}):(\d{2})', date_str)
        if date_match:
            date_part = date_match.group(1).replace('-', '/')
            day_of_week = date_match.group(2)
            hour = date_match.group(3)
            minute = date_match.group(4)
            
            start_time_str = f"{date_part}({day_of_week}) {hour}:{minute}"
            
            start_hour = int(hour)
            start_minute = int(minute)
            total_minutes = start_hour * 60 + start_minute + 100
            end_hour = (total_minutes // 60) % 24
            end_minute = total_minutes % 60
            
            end_time_str = f"{end_hour:02d}:{end_minute:02d}"
            
            return f"{start_time_str} - {end_time_str}"
        
        # パターン2: "2025-07-12 21:00:00+0900" 形式
        iso_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}):(\d{2}):\d{2}[+-]\d{4}', date_str)
        if iso_match:
            date_part = iso_match.group(1).replace('-', '/')
            hour = iso_match.group(2)
            minute = iso_match.group(3)
            
            from datetime import datetime
            year, month, day = map(int, iso_match.group(1).split('-'))
            weekdays = ['月', '火', '水', '木', '金', '土', '日']
            day_of_week = weekdays[datetime(year, month, day).weekday()]
            
            start_time_str = f"{date_part}({day_of_week}) {hour}:{minute}"
            
            start_hour = int(hour)
            start_minute = int(minute)
            total_minutes = start_hour * 60 + start_minute + 100
            end_hour = (total_minutes // 60) % 24
            end_minute = total_minutes % 60
            
            end_time_str = f"{end_hour:02d}:{end_minute:02d}"
            
            return f"{start_time_str} - {end_time_str}"
            
    except Exception as e:
        logger.warning(f"日時文字列のフォーマットに失敗しました: {date_str}, エラー: {e}")
    
    return date_str


def create_reminder_message(contest_info: dict, message_type: str) -> str:
    """リマインダーメッセージを生成"""
    contest_name = contest_info["title"]
    contest_id = contest_info["contest_id"]
    contest_url = contest_info.get("contest_url", f"https://atcoder.jp/contests/{contest_id}")
    
    problem_links = []
    for problem in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
        problem_url = f"https://atcoder.jp/contests/{contest_id}/tasks/{contest_id}_{problem}"
        problem_links.append(f"[{problem.upper()}]({problem_url})")
    problems_text = " ".join(problem_links)
    
    if contest_info.get("date_str"):
        contest_time = format_date_string_discord(contest_info["date_str"])
    else:
        contest_time = format_contest_time_discord(
            contest_info["start_epoch_second"], 
            contest_info["duration_second"]
        )
    
    if message_type == "morning":
        message = f"🌅 おはようございます！今日は{contest_name}が開催されます！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    elif message_type == "evening":
        message = f"🌙 お疲れ様です！{contest_name}が開催中または間もなく開始です！\n📅 開催時間: {contest_time}\n🔗 {contest_url}\n📝 問題: {problems_text}"
    else:
        message = f"📢 {contest_name}のリマインドです！\n📅 開催時間: {contest_time}\n🔗 {contest_url}"
    
    return message


def parse_webhook_urls(webhook_urls_str: str) -> list[str]:
    """webhook URL文字列をパースして有効なURLのリストを返す"""
    if not webhook_urls_str:
        return []
    
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
    
    jst = timezone(timedelta(hours=9))
    current_hour = datetime.now(jst).hour
    
    if current_hour == 10:
        return "morning"
    elif current_hour == 20:
        return "evening"
    else:
        return "default"


def is_contest_today(contest_info: dict) -> bool:
    """コンテストが今日開催されるかチェック"""
    if not contest_info or contest_info.get("start_epoch_second", 0) == 0:
        return False
    
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).date()
    contest_date = datetime.fromtimestamp(contest_info["start_epoch_second"], tz=jst).date()
    
    return today == contest_date


def main():
    """メイン処理"""
    logger.info("ABC コンテストリマインダーを開始します。")
    
    contest_info = get_latest_abc_contest()
    if not contest_info:
        logger.info("最新のABC情報が取得できませんでした。")
        sys.exit(0)
    
    if not is_contest_today(contest_info):
        logger.info(f"コンテスト {contest_info['title']} は今日開催されません。")
        sys.exit(0)
    
    message_type = get_current_message_type()
    
    message = create_reminder_message(contest_info, message_type)
    
    success = send_discord_notifications(message)
    
    if success:
        logger.info("リマインダー処理が正常に完了しました。")
    else:
        logger.error("リマインダー処理中にエラーが発生しました。")
        sys.exit(1)


if __name__ == "__main__":
    main()