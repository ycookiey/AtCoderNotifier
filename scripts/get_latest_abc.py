#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import sys

def get_latest_abc():
    """AtCoderのコンテスト一覧から最新のABCコンテストを取得"""
    url = "https://atcoder.jp/contests/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 開催予定のコンテストテーブルを探す
        upcoming_table = soup.find('div', id='contest-table-upcoming')
        if not upcoming_table:
            print("Error: Could not find upcoming contests table", file=sys.stderr)
            return None
            
        table = upcoming_table.find('table')
        if not table:
            print("Error: Could not find table in upcoming contests", file=sys.stderr)
            return None
        
        rows = table.find('tbody').find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                # コンテスト名のリンクを取得
                contest_link = cells[1].find('a')
                if contest_link:
                    contest_name = contest_link.get_text(strip=True)
                    contest_url = contest_link.get('href')
                    
                    # ABCコンテストかチェック（AtCoder Beginner Contest XXX の形式）
                    if re.search(r'AtCoder Beginner Contest \d+|ABC\d+', contest_name, re.IGNORECASE):
                        # 日時を取得
                        date_cell = cells[0].get_text(strip=True)
                        
                        # コンテスト情報を返す
                        return {
                            'name': contest_name,
                            'url': f"https://atcoder.jp{contest_url}",
                            'date': date_cell,
                            'contest_id': contest_url.split('/')[-1] if contest_url else None
                        }
        
        print("No upcoming ABC contest found", file=sys.stderr)
        return None
        
    except requests.RequestException as e:
        print(f"Error fetching contests page: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error parsing contests page: {e}", file=sys.stderr)
        return None

def parse_contest_date(date_str):
    """コンテスト日時文字列をパース"""
    # 例: "2025-07-12(土) 21:00" の形式を想定
    try:
        # 日付部分を抽出
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
        if date_match:
            date_part = date_match.group(1)
            contest_date = datetime.strptime(date_part, '%Y-%m-%d')
            return contest_date
    except:
        pass
    return None

def is_weekend(date_obj):
    """土曜日または日曜日かチェック"""
    return date_obj.weekday() in [5, 6]  # 5=土曜日, 6=日曜日

if __name__ == "__main__":
    abc_info = get_latest_abc()
    
    if abc_info:
        print(f"Name: {abc_info['name']}")
        print(f"URL: {abc_info['url']}")
        print(f"Date: {abc_info['date']}")
        print(f"Contest ID: {abc_info['contest_id']}")
        
        # 日付をパース
        contest_date = parse_contest_date(abc_info['date'])
        if contest_date and is_weekend(contest_date):
            print(f"Weekend contest: {contest_date.strftime('%Y-%m-%d (%a)')}")
        elif contest_date:
            print(f"Not a weekend contest: {contest_date.strftime('%Y-%m-%d (%a)')}")
    else:
        print("No ABC contest found")
        sys.exit(1)