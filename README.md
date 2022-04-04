# tweetBOT_statink
Splatooon2のステージスケジュールとStat.inkの過去戦績から勝率予測するツイートBOT。  
A tweet BOT that provides Splatoon2 win rates by schedule with data from stat.ink.  
  
2時間ごとに更新されるステージ情報をチェックしそのステージの勝率を元にガチマッチに潜るべきか否か判断基準をツイートしてくれる。  
![image](https://user-images.githubusercontent.com/102900238/161430074-b54ad54a-134c-4924-ab0f-b99ea3c52d8f.png)


# 必要なもの
- Twitterアカウント
- Twitterデベロッパーアカウント
- Stat.inkアカウント（BOT実行にログインは不要）
- Stat.inkにUploadされた戦績
- Python実行環境

# 実行方法
- Twitter API を実行するための認証情報を入力
>ck = ""  #API_KEY  
>cs = ""  #API_SECRET  
>at = ""  #ACCESS_TOKEN  
>ats = "" #ACCESS_TOKEN_SECRET  
- 戦績チェックをしたいユーザのTwitterアカウントとStat.inkアカウントをリスト形式で記載
- 複数ユーザに対応
> account_list = [["@twitter_account_hoge","@statink_account_hoge"],["@twitter_account_fuga","@statink_account_fuga"],,,]  
- Pythonを実行

# 処理の概要
- イカの処理をscheduleモジュールで定期実行する
- スケジュール情報の取得：スケジュール情報BOT(https://twitter.com/splatoon2_mini)の定時ツイートを検知しステージ情報を把握
- ステージごとの戦績を取得：Stat.inkのWebページからスクレイピング
- ガチパワー増減を予想：2時間で14戦実施した想定で勝+10：敗-10として、2ステージの勝率を乗算し期待値を導出
> # -100---x--->-10--?-->0--△-->+10--o-->+30---◎--->+100  
> #   ◎ 絶対行った方がいい！！  
> #   ○ そこそこ期待できそう！  
> #   △ 悪くはない  
> #   ？ 行っても無駄かも  
> #   × 大事故が起きます  
- 解析結果の通知：時間、ルール、ステージ、勝率、XP、パワー増減をTwitterアカウントにツイート

# 今後の予定
- スケジュール情報の取得先の変更 https://splatoon2.ink/
- 通知手段の変更 ツイートだけでなくDM、メールに対応
