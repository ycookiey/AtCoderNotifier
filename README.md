# AtCoderNotifier

AtCoder Beginner Contest(ABC)の結果とレーティングの変動を、Discordのチャンネルに送るBot。ABCの開催日には、開催のリマインダーも送る。GitHub Actionsで動くので、サーバーは不要。

## 通知の例

レーティングの通知:

```
<ユーザーID>さんのTokio Marine & Nichido Fire Insurance Programming Contest 2026  (AtCoder Beginner Contest 459)での成績：6010位
パフォーマンス：653相当
レーティング：395→424 (+29) 🙂
#AtCoder #Tokio Marine & Nichido Fire Insurance Programming Contest 2026  AtCoder Beginner Contest 459（ABC459） https://atcoder.jp/users/<ユーザーID>/history/share/abc459?lang=ja
```

20:00のリマインダー:

```
🌙 お疲れ様です！SMBC Programming Contest #2 (AtCoder Beginner Contest 481）が開催中または間もなく開始です！
📅 開催時間: <t:1792843200:f> - <t:1792849200:t>
🔗 https://atcoder.jp/contests/abc481
📝 問題: [A](https://atcoder.jp/contests/abc481/tasks/abc481_a) [B](https://atcoder.jp/contests/abc481/tasks/abc481_b) …… [G](https://atcoder.jp/contests/abc481/tasks/abc481_g)
```

開催時間はDiscordのタイムスタンプの書式で送るので、Discordは読む人のタイムゾーンの時刻で表示する。

## 通知する時刻と条件

| workflow | 実行する時刻(JST) | 通知する条件 |
| --- | --- | --- |
| `AtCoder Rating Notifier` | 土曜と日曜の23:00から翌1:55まで、5分ごと | 指定したユーザーの成績の履歴に、前回の通知と別のABCが載ったとき。レーティングの変動が0でも通知する |
| `ABC Contest Reminder` | 土曜と日曜の10:00と20:00 | 実行した日に、次のABCを開催するとき |

## 設定

1. このrepoをforkする
2. 通知を送るDiscordのチャンネルの設定でウェブフックを作り、URLをコピーする
3. forkしたrepoの`Settings` → `Secrets and variables` → `Actions`で、次の値を登録する。Variableは同じ画面の`Variables`タブで登録する

   | 種類 | 名前 | 値 |
   | --- | --- | --- |
   | Secret | `DISCORD_WEBHOOK_URLS_NOTIFIER` | レーティングの通知を送るウェブフックのURL |
   | Secret | `DISCORD_WEBHOOK_URLS_REMINDER` | リマインダーを送るウェブフックのURL |
   | Variable | `ATCODER_USER_ID` | 成績を通知するAtCoderのユーザーID |

   複数のチャンネルに送るときは、URLを`,`か`;`か改行で区切って書く。`https://`で始まらない値は無視する。

4. forkしたrepoの`Actions`タブでworkflowを有効にする。forkした直後のrepoでは、GitHubがscheduleによる実行を止めている
5. `Actions`タブで2つのworkflowを選び、それぞれ`Run workflow`で手動で実行して、Discordに届くかを確かめる。レーティングの通知は、初めての実行では履歴の最新のABCの結果を送る。リマインダーは、ABCの開催日でなければ送らない

片方の通知だけを使うときは、使わないほうのworkflowを`Actions`タブで無効にする。無効にしないと、ウェブフックのURLが無いほうのworkflowが失敗する。リマインダーが失敗するのは、ABCの開催日だけ。

実行する時刻は、`.github/workflows/atcoder_notifier.yml`と`.github/workflows/abc-reminder.yml`の`cron`で変える。`cron`の時刻はUTCで書く。例: JSTの22:00はUTCの13:00なので`0 13 * * *`。リマインダーは、実行した時刻がJSTの10時台なら朝の文、20時台なら夜の文、ほかの時刻なら朝と夜のどちらでもない文を送る。

## 既知の制限

- AtCoderのページのHTMLから値を読む。AtCoderがページの構成を変えると、通知が届かなくなる。2026年10月22日のページで、値の取得と通知の文の組み立てを確かめた
- 2回目に通知したABCからは、レーティングの通知の実行のたびに、同じ結果を送り直す。前回通知したABCを保存するキャッシュの`key`がcommitで決まり、新しいcommitが無いかぎり、最初に保存した後は保存し直されないため
- GitHub Actionsのscheduleは遅れることがあり、GitHubが混む時間には実行が飛ぶ。このrepoの2025年9月までの記録では、5分ごとの設定でも、23:00から翌1:55までの実行は1日に20回ほどだった。リマインダーの10:00の実行は、すべて11時台に動き、朝の文ではなく、どちらでもない文を送った
- public repoでは、60日間活動が無いと、GitHubがscheduleによる実行を止める。止まったら`Actions`タブでworkflowを有効にし直す
- 通知するコンテストはABCだけ。リマインダーの終了時刻は開始から100分後として計算し、問題のリンクはAからGまでの7問分を作る

## 止める

`Actions`タブで2つのworkflowを無効にするか、forkしたrepoを消す。Discordのウェブフックも消す。

## ライセンス

MIT License
