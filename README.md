# AtCoder レーティング通知 Bot

AtCoder のコンテスト参加後にレーティング変動を Discord に自動通知する Bot です。GitHub Actions を使用してサーバーレスで動作します。

## 機能

-   🚀 **自動検出**: 最新の AtCoder Beginner Contest (ABC) を自動で検出
-   📊 **レート変動通知**: レーティングに変動があった場合のみ Discord に通知
-   🔄 **重複防止**: GitHub Actions キャッシュで重複通知を防止
-   ⏰ **自動実行**: 土日の結果発表時間帯に自動実行（手動実行も可能）

## 通知メッセージ例

```
ycookieyさんのDenso Create Programming Contest 2025（AtCoder Beginner Contest 413）での成績：4219位
パフォーマンス：774相当
レーティング：358→409 (+51) 🙂
Highestを更新し8級になりました！
#AtCoder #Denso Create Programming Contest 2025AtCoder Beginner Contest 413（ABC413） https://atcoder.jp/users/ycookiey/history/share/abc413?lang=ja
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

### 自動実行

-   **日時**: JST 土曜・日曜の 22:00〜翌 1:00
-   **間隔**: 15 分ごと
-   **対象**: AtCoder Beginner Contest (ABC) のみ

### 手動実行

リポジトリの `Actions` タブ → `AtCoder Rating Notifier` → `Run workflow` で手動実行可能

## ファイル構成

```
AtCoderNotifier/
├── notifier.py              # メインスクリプト
├── requirements.txt         # Python依存関係
├── .github/workflows/
│   └── atcoder_notifier.yml # GitHub Actionsワークフロー
└── README.md               # このファイル
```

## 技術仕様

### 使用 API

-   **kenkoooo API**: 最新のコンテスト情報を取得
-   **AtCoder 共有ページ**: ユーザーの参加確認とメッセージ取得
-   **AtCoder 履歴ページ**: レーティング変動の詳細取得

### 動作フロー

1. kenkoooo API から最新の ABC 情報を取得
2. AtCoder 共有ページで該当ユーザーの参加確認
3. 履歴ページからレーティング変動を取得
4. レート変動があれば Discord に通知
5. 処理済みコンテストをキャッシュに保存

### 通知条件

-   AtCoder Beginner Contest (ABC) への参加
-   レーティングに変動がある場合のみ
-   前回通知したコンテストとは異なる場合

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

`.github/workflows/atcoder_notifier.yml` の `cron` 設定を変更：

```yaml
schedule:
    # 毎日22:00に実行する場合（UTC 13:00）
    - cron: "0 13 * * *"
```

### メッセージフォーマットの変更

`notifier.py` の `parse_contest_result()` 関数でメッセージ形式をカスタマイズできます。

## ライセンス

MIT License
