# AtCoder レーティング通知 Bot

AtCoder のコンテスト参加後にレーティング変動を Discord に自動通知する Bot です。GitHub Actions を使用してサーバーレスで動作します。

## 機能

### レーティング変動通知
-   🚀 **自動検出**: 最新の AtCoder Beginner Contest (ABC) を自動で検出
-   📊 **レート変動通知**: レーティングに変動があった場合のみ Discord に通知
-   🔄 **重複防止**: GitHub Actions キャッシュで重複通知を防止
-   ⏰ **自動実行**: 土日の結果発表時間帯に自動実行（手動実行も可能）

### ABCコンテストリマインダー
-   🔔 **開催通知**: 開催予定のABCコンテストをDiscordに自動通知
-   📅 **複数回通知**: 土日の12:00、16:00、20:00(JST)に通知
-   🌅 **時間帯別メッセージ**: 朝・昼・夜でメッセージを変更

## 通知メッセージ例

### レーティング変動通知
```
ycookieyさんのDenso Create Programming Contest 2025（AtCoder Beginner Contest 413）での成績：4219位
パフォーマンス：774相当
レーティング：358→409 (+51) 🙂
Highestを更新し8級になりました！
#AtCoder #Denso Create Programming Contest 2025AtCoder Beginner Contest 413（ABC413） https://atcoder.jp/users/ycookiey/history/share/abc413?lang=ja
```

### ABCコンテストリマインダー
```
🌅 おはようございます！今日はAtCoder Beginner Contest 414が開催されます！
📅 開催時間: 2025-07-13(日) 21:00
🔗 https://atcoder.jp/contests/abc414
```

## セットアップ手順

### 1. リポジトリの準備

このリポジトリをフォークまたはクローンしてください。

### 2. Discord Webhook の設定

1. Discord で通知を受け取りたいチャンネルの設定を開く
2. 「統合」→「ウェブフック」→「新しいウェブフック」を作成
3. Webhook の URL をコピー（例: `https://discord.com/api/webhooks/...`）

### 3. GitHub リポジトリの環境変数設定

#### Secrets（機密情報）

リポジトリの `Settings` > `Secrets and variables` > `Actions` で以下を設定：

| Name                  | Value                                  | 説明                   |
| --------------------- | -------------------------------------- | ---------------------- |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Discord Webhook の URL |

#### Variables（公開情報）

同じ画面の `Variables` タブで以下を設定：

| Name              | Value             | 説明                           |
| ----------------- | ----------------- | ------------------------------ |
| `ATCODER_USER_ID` | `your_atcoder_id` | 監視する AtCoder のユーザー ID |

### 4. GitHub Actions の有効化

リポジトリの `Actions` タブで GitHub Actions を有効化してください。

## 実行スケジュール

### レーティング変動通知

#### 自動実行
-   **日時**: JST 土曜・日曜の 22:00〜翌 1:00
-   **間隔**: 15 分ごと
-   **対象**: AtCoder Beginner Contest (ABC) のみ

#### 手動実行
リポジトリの `Actions` タブ → `AtCoder Rating Notifier` → `Run workflow` で手動実行可能

### ABCコンテストリマインダー

#### 自動実行
-   **日時**: JST 土曜・日曜の 12:00、16:00、20:00
-   **対象**: 開催予定のAtCoder Beginner Contest (ABC)

#### 手動実行
リポジトリの `Actions` タブ → `ABC Contest Reminder` → `Run workflow` で手動実行可能

## ファイル構成

```
AtCoderNotifier/
├── notifier.py              # レーティング変動通知スクリプト
├── requirements.txt         # Python依存関係
├── scripts/
│   └── get_latest_abc.py    # ABC情報取得スクリプト
├── .github/workflows/
│   ├── atcoder_notifier.yml # レーティング変動通知ワークフロー
│   └── abc-reminder.yml     # ABCリマインダーワークフロー
└── README.md               # このファイル
```

## 技術仕様

### 使用 API

-   **kenkoooo API**: 最新のコンテスト情報を取得
-   **AtCoder 共有ページ**: ユーザーの参加確認とメッセージ取得
-   **AtCoder 履歴ページ**: レーティング変動の詳細取得

### 動作フロー

#### レーティング変動通知
1. kenkoooo API から最新の ABC 情報を取得
2. AtCoder 共有ページで該当ユーザーの参加確認
3. 履歴ページからレーティング変動を取得
4. レート変動があれば Discord に通知
5. 処理済みコンテストをキャッシュに保存

#### ABCコンテストリマインダー
1. AtCoderコンテスト一覧ページから開催予定のABC情報を取得
2. 現在時刻に応じて通知メッセージを生成
3. Discord に開催通知を送信

### 通知条件

#### レーティング変動通知
-   AtCoder Beginner Contest (ABC) への参加
-   レーティングに変動がある場合のみ
-   前回通知したコンテストとは異なる場合

#### ABCコンテストリマインダー
-   開催予定のAtCoder Beginner Contest (ABC)が存在する場合
-   土日の指定時間（12:00、16:00、20:00 JST）

## カスタマイズ

### 監視対象の変更

`notifier.py` の `get_latest_abc_contest()` 関数で、監視するコンテストタイプを変更できます：

```python
# ABCのみ（デフォルト）
if contest["id"].startswith("abc")

# ARCも含める場合
if contest["id"].startswith(("abc", "arc"))

# 全コンテスト
# startswithの条件を削除
```

### 実行スケジュールの変更

#### レーティング変動通知
`.github/workflows/atcoder_notifier.yml` の `cron` 設定を変更：

```yaml
schedule:
    # 毎日22:00に実行する場合（UTC 13:00）
    - cron: "0 13 * * *"
```

#### ABCコンテストリマインダー
`.github/workflows/abc-reminder.yml` の `cron` 設定を変更：

```yaml
schedule:
    # 毎日12:00に実行する場合（UTC 03:00）
    - cron: "0 3 * * *"
```

### メッセージフォーマットの変更

#### レーティング変動通知
`notifier.py` の `parse_contest_result()` 関数でメッセージ形式をカスタマイズできます。

#### ABCコンテストリマインダー
`.github/workflows/abc-reminder.yml` の Python スクリプト部分で時間帯別メッセージをカスタマイズできます。

## ライセンス

MIT License
