import os
import requests
import sys

# --- 設定 ---
ATCODER_USER_ID = os.environ.get("ATCODER_USER_ID")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
API_URL = f"https://kenkoooo.com/atcoder/atcoder-api/v3/user/history?user={ATCODER_USER_ID}"
STATE_FILE = "latest_contest.txt" # 最後に通知したコンテストIDを保存するファイル

# --- メイン処理 ---
def main():
    if not ATCODER_USER_ID or not DISCORD_WEBHOOK_URL:
        print("エラー: 環境変数が設定されていません。")
        sys.exit(1)

    try:
        # AtCoder Problems APIからコンテスト履歴を取得
        response = requests.get(API_URL)
        response.raise_for_status()
        history = response.json()

        if not history:
            print("コンテスト参加履歴が見つかりませんでした。")
            return

        # 最新のコンテスト情報を取得
        latest_contest = history[-1]
        latest_contest_id = latest_contest.get("ContestScreenName")

        # 前回通知したコンテストIDをファイルから読み込む
        last_notified_id = ""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                last_notified_id = f.read().strip()
        
        # 最新のコンテストが前回通知したものと同じか、レート変動がない場合は終了
        if latest_contest_id == last_notified_id:
            print("新しいコンテスト結果はありません。")
            return
            
        old_rating = latest_contest.get("OldRating")
        new_rating = latest_contest.get("NewRating")
        if old_rating == new_rating and latest_contest_id:
            print("レート変動がなかったため、通知をスキップします。")
            # 変動がなくてもファイルは更新し、次回以降の重複チェックに備える
            with open(STATE_FILE, "w") as f:
                f.write(latest_contest_id)
            print(f"状態ファイルを更新しました: {latest_contest_id}")
            return

        # Discordに送信するメッセージを作成・送信
        message = create_message(latest_contest)
        send_to_discord(message)
        print("Discordへの通知を送信しました。")

        # 最新のコンテストIDをファイルに書き込む
        with open(STATE_FILE, "w") as f:
            f.write(latest_contest_id)
        print(f"状態ファイルを更新しました: {latest_contest_id}")

    except requests.exceptions.RequestException as e:
        print(f"APIリクエストエラー: {e}")
        sys.exit(1)
    except (KeyError, IndexError) as e:
        print(f"APIレスポンス解析エラー: {e}")
        sys.exit(1)

def create_message(contest_result):
    contest_name = contest_result.get("ContestName")
    performance = contest_result.get("Performance")
    old_rating = contest_result.get("OldRating")
    new_rating = contest_result.get("NewRating")
    place = contest_result.get("Place")
    
    rating_diff = new_rating - old_rating
    diff_sign = "+" if rating_diff >= 0 else ""

    payload = {
        "embeds": [
            {
                "title": f"{contest_name} の結果",
                "description": f"**{ATCODER_USER_ID}** さんのレーティングが変動しました！",
                "color": 0x3366ff,
                "fields": [
                    {"name": "順位", "value": f"{place}位", "inline": True},
                    {"name": "パフォーマンス", "value": f"{performance}", "inline": True},
                    {"name": "レーティング", "value": f"**{old_rating} → {new_rating} ({diff_sign}{rating_diff})**", "inline": False},
                ],
            }
        ]
    }
    return payload

def send_to_discord(payload):
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()

if __name__ == "__main__":
    main()