# AtCoder レーティング通知 Bot

AtCoder のコンテスト参加後にレーティング変動を Discord に自動通知する Bot です。GitHub Actions を使用してサーバーレスで動作します。

## 機能

### レーティング変動通知

-   🚀 **自動検出**: 最新の AtCoder Beginner Contest (ABC) を自動で検出
-   📊 **レート変動通知**: レーティングに変動があった場合のみ Discord に通知
-   🔄 **重複防止**: GitHub Actions キャッシュで同じコンテストの重複通知を防止
-   ⚡ **即時通知**: 履歴ページから直接取得で高速化
-   ⏰ **自動実行**: 土日の結果発表時間帯に自動実行（手動実行も可能）
-   🔗 **複数 webhook 対応**: 複数の Discord チャンネルに同時通知可能

### ABC コンテストリマインダー

-   🔔 **開催通知**: 開催予定の ABC コンテストを Discord に自動通知
-   📅 **複数回通知**: 土日の 12:00、20:00(JST)に通知
-   🌅 **時間帯別メッセージ**: 朝・夜でメッセージを変更
-   🔗 **複数 webhook 対応**: 複数の Discord チャンネルに同時通知可能

## 通知メッセージ例

### レーティング変動通知

```
ycookieyさんのDenso Create Programming Contest 2025（AtCoder Beginner Contest 413）での成績：4219位
パフォーマンス：774相当
レーティング：358→409 (+51) 🙂
#AtCoder #Denso Create Programming Contest 2025AtCoder Beginner Contest 413（ABC413） https://atcoder.jp/users/ycookiey/history/share/abc413?lang=ja
```

### ABC コンテストリマインダー

```
🌅 おはようございます！今日はAtCoder Beginner Contest 414が開催されます！
📅 開催時間: 2025/07/12 21:00 - 22:40 JST
🔗 https://atcoder.jp/contests/abc414
```

## セットアップ手順

### 1. リポジトリの準備

このリポジトリをフォークまたはクローンしてください。

```bash
# リポジトリをクローン
git clone https://github.com/your-username/AtCoderNotifier.git
cd AtCoderNotifier
```

**注意**: `your-username` を実際の GitHub ユーザー名に置き換えてください。

### 2. Discord Webhook の設定

1. Discord で通知を受け取りたいチャンネルの設定を開く
2. 「統合」→「ウェブフック」→「新しいウェブフック」を作成
3. Webhook の URL をコピー（例: `https://discord.com/api/webhooks/...`）

### 3. GitHub リポジトリの環境変数設定

#### Secrets（機密情報）

リポジトリの `Settings` > `Secrets and variables` > `Actions` で以下を設定：

| Name                            | Value                                  | 説明                                      |
| ------------------------------- | -------------------------------------- | ----------------------------------------- |
| `DISCORD_WEBHOOK_URLS_NOTIFIER` | `https://discord.com/api/webhooks/...` | レーティング通知用 Discord Webhook の URL |
| `DISCORD_WEBHOOK_URLS_REMINDER` | `https://discord.com/api/webhooks/...` | リマインダー用 Discord Webhook の URL     |

**複数 webhook 設定例:**

```
DISCORD_WEBHOOK_URLS_NOTIFIER=https://discord.com/api/webhooks/111,https://discord.com/api/webhooks/222
DISCORD_WEBHOOK_URLS_REMINDER=https://discord.com/api/webhooks/333;https://discord.com/api/webhooks/444
```

#### Variables（公開情報）

同じ画面の `Variables` タブで以下を設定：

| Name              | Value             | 説明                           |
| ----------------- | ----------------- | ------------------------------ |
| `ATCODER_USER_ID` | `your_atcoder_id` | 監視する AtCoder のユーザー ID |

### 4. GitHub Actions の有効化

リポジトリの `Actions` タブで GitHub Actions を有効化してください。

### 5. CLI による環境変数設定（オプション）

GitHub CLI (`gh`) を使用して環境変数を設定することも可能です：

```bash
# GitHub CLIでログイン（初回のみ）
gh auth login

# Secrets（機密情報）の設定
gh secret set DISCORD_WEBHOOK_URLS_NOTIFIER --body "https://discord.com/api/webhooks/your-webhook-url"
gh secret set DISCORD_WEBHOOK_URLS_REMINDER --body "https://discord.com/api/webhooks/your-webhook-url"

# Variables（公開情報）の設定
gh variable set ATCODER_USER_ID --body "your_atcoder_id"

# 設定の確認
gh secret list
gh variable list
```

**注意**: webhook URL と AtCoder ユーザー ID は実際の値に置き換えてください。

## 実行スケジュール

### レーティング変動通知

#### 自動実行

-   **日時**: JST 土曜・日曜の 23:00〜翌 1:00
-   **間隔**: 5 分ごと
-   **対象**: AtCoder Beginner Contest (ABC) のみ
-   **制限**: 同じコンテストの重複通知を防止

#### 手動実行

リポジトリの `Actions` タブ → `AtCoder Rating Notifier` → `Run workflow` で手動実行可能

### ABC コンテストリマインダー

#### 自動実行

-   **日時**: JST 土曜・日曜の 12:00、20:00
-   **対象**: 開催予定の AtCoder Beginner Contest (ABC)

#### 手動実行

リポジトリの `Actions` タブ → `ABC Contest Reminder` → `Run workflow` で手動実行可能

## ファイル構成

```
AtCoderNotifier/
├── notifier.py              # レーティング変動通知スクリプト
├── reminder.py              # ABCリマインダースクリプト
├── requirements.txt         # Python依存関係
├── last_contest.txt         # 最後に通知したコンテスト情報（自動生成）
├── notified_today.txt       # 通知済み日付情報（自動生成）
├── scripts/
│   └── get_latest_abc.py    # ABC情報取得スクリプト（参考用）
├── .github/workflows/
│   ├── atcoder_notifier.yml # レーティング変動通知ワークフロー
│   └── abc-reminder.yml     # ABCリマインダーワークフロー
└── README.md               # このファイル
```

## 技術仕様

### 使用 API

-   **AtCoder 履歴ページ**: 最新のコンテスト情報とレーティング変動の詳細取得
-   **AtCoder 共有ページ**: ユーザーの参加確認とメッセージ取得

### 動作フロー

#### レーティング変動通知

1. **ABC 情報取得**: AtCoder 履歴ページから最新の ABC 情報を取得
2. **重複チェック**: 前回処理済みコンテストと比較し、同じ場合は処理を終了
3. **参加確認**: AtCoder 共有ページで該当ユーザーの参加確認
4. **レート変動取得**: 履歴ページからレーティング変動を取得
5. **Discord 通知**: レート変動があれば Discord に通知
6. **状態保存**: 処理済みコンテストと通知日付を GitHub Actions キャッシュに保存

#### ABC コンテストリマインダー

1. AtCoder コンテスト一覧ページから開催予定の ABC 情報をスクレイピングで取得
2. 現在時刻に応じて通知メッセージを生成（朝・夜）
3. 複数の Discord webhook に開催通知を送信

### 通知条件

#### レーティング変動通知

-   AtCoder Beginner Contest (ABC) への参加
-   レーティングに変動がある場合のみ
-   前回通知したコンテストとは異なる場合（同じコンテストの重複通知を防止）

#### ABC コンテストリマインダー

-   開催予定の AtCoder Beginner Contest (ABC)が存在する場合
-   土日の指定時間（12:00、20:00 JST）

## カスタマイズ

### 監視対象の変更

`notifier.py` の `get_latest_abc_contest()` 関数で、監視するコンテストタイプを変更できます：

```python
# ABCのみ（デフォルト）
if "/contests/abc" in href:

# ARCも含める場合
if "/contests/abc" in href or "/contests/arc" in href:

# 全コンテスト
# 条件を削除してすべてのコンテストを対象にする
```

### 実行スケジュールの変更

#### レーティング変動通知

`.github/workflows/atcoder_notifier.yml` の `cron` 設定を変更：

```yaml
schedule:
    # 毎日22:00に実行する場合（UTC 13:00）
    - cron: "0 13 * * *"
    # 現在の設定: 土日23:00-翌1:00、5分おき（UTC 14:00-16:00）
    - cron: "*/5 14-16 * * 6,0"
```

#### ABC コンテストリマインダー

`.github/workflows/abc-reminder.yml` の `cron` 設定を変更：

```yaml
schedule:
    # 毎日12:00に実行する場合（UTC 03:00）
    - cron: "0 3 * * *"
```

### メッセージフォーマットの変更

#### レーティング変動通知

`notifier.py` の `parse_contest_result()` 関数でメッセージ形式をカスタマイズできます。

#### ABC コンテストリマインダー

`reminder.py` の `create_reminder_message()` 関数で時間帯別メッセージをカスタマイズできます。

### 複数 webhook 設定

環境変数でカンマ(`,`)またはセミコロン(`;`)区切りで複数の webhook URL を指定できます：

```
# レーティング通知を複数チャンネルに送信
DISCORD_WEBHOOK_URLS_NOTIFIER=https://discord.com/api/webhooks/111,https://discord.com/api/webhooks/222

# リマインダーを複数チャンネルに送信
DISCORD_WEBHOOK_URLS_REMINDER=https://discord.com/api/webhooks/333;https://discord.com/api/webhooks/444
```

## ライセンス

MIT License
