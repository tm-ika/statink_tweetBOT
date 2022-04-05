#!/usr/bin/python
# -*- coding: <encoding utf-8> -*-

import tweepy
import requests
from bs4 import BeautifulSoup

import schedule
import time
import datetime

# 認証用外部ファイルの読み込み
import twitter_auth_info


# Twitter上の表記とstst.ink上の表記の変換
tw2stat_stage = {"Ｂバスパーク" : "bbass","アジフライスタジアム" : "ajifry", "海女美術大学" : "ama", "アロワナモール" : "arowana", "アンチョビットゲームズ" : "anchovy", "エンガワ河川敷" : "engawa", "ガンガゼ野外音楽堂" : "gangaze", "コンブトラック" : "kombu", "ザトウマーケット" : "zatou", "ショッツル鉱山" : "shottsuru", "スメーシーワールド" : "sumeshi", "タチウオパーキング" : "tachiuo", "チョウザメ造船" : "chozame", "デボン海洋博物館" : "devon", "ハコフグ倉庫" : "hakofugu", "バッテラストリート" : "battera", "フジツボスポーツクラブ" : "fujitsubo", "ホッケふ頭" : "hokke", "ホテルニューオートロ" : "otoro", "マンタマリア号" : "manta", "ムツゴ楼" : "mutsugoro", "モズク農園" : "mozuku", "モンガラキャンプ場" : "mongara"}
tw2stat_rule = {"▼ガチエリア":"standard-gachi-area", "▼ガチヤグラ":"standard-gachi-yagura", "▼ガチホコ":"standard-gachi-hoko", "▼ガチアサリ":"standard-gachi-asari"}


# Twieterアカウントとstat.inkアカウントをリストで設定。複数ユーザにも対応
account_list = twitter_auth_info.account_list
tw_stage_info = "@splatoon2_mini"
tw_stage_info = tw_stage_info.replace("@","")


# Twitterの認証、取得したキーを格納 twitter_auth_info.pyから読み込み
ck = twitter_auth_info.ck   # consumer_key
cs = twitter_auth_info.cs   # consumer_secret
at = twitter_auth_info.at   # access_token
ats = twitter_auth_info.ats # access_token_secret


# Twitter APIの動作確認
print("[+] Health Check,,," + tw_stage_info)
auth = tweepy.OAuth1UserHandler(consumer_key=ck, consumer_secret=cs, access_token=at, access_token_secret=ats)
api = tweepy.API(auth)
t_lines = api.user_timeline(screen_name = tw_stage_info)

for s in t_lines:
    print(s.created_at, s.id)


# メッセージからステージ情報の抜粋
def get_stage(msg):
    """
    04/01 19:00～
    ▼ナワバリ
    ショッツル鉱山、ムツゴ楼

    ▼ガチホコ
    Ｂバスパーク、モズク農園

    ▼リーグ：ガチアサリ
    ガンガゼ野外音楽堂、ホッケふ頭
    """
    res_text = msg

    res_list = []
    res_text = res_text.strip().replace("\n\n","\n")
    res_list = res_text.split("\n")

    gachi_time = res_list[0]
    gachi_rule = res_list[3]
    gachi_stages = res_list[4].split("、")

    if gachi_rule not in list(tw2stat_rule.keys()):
        print("[!] Format Error : Rule & Stage")
        return False
    else:
        print(gachi_time, gachi_rule, gachi_stages)
        return gachi_time, gachi_rule, gachi_stages
    

# stat.inkにアクセスしステージごとの戦績を出力
def get_win_rate(stat_account, gachi_rule, gachi_stage):
    url = "https://stat.ink/" + stat_account + "/spl2?filter%5Brule%5D=" + tw2stat_rule[gachi_rule] +"&filter%5Bmap%5D=" + tw2stat_stage[gachi_stage] \
          + "&filter%5Bweapon%5D=&filter%5Brank%5D=&filter%5Bresult%5D=&filter%5Bhas_disconnect%5D=&filter%5Bterm%5D=last-50-battles&filter%5Bterm_from%5D=&filter%5Bterm_to%5D=&filter%5Btimezone%5D=Asia%2FTokyo"

    print("[+] HTTPreq to stat.ink...")
    print(url)
    res = requests.get(url)
    res_text = res.text
    res_text = res_text.replace("&#8203;","<small>計測中</small>") # 計測中はXPが空欄
    
    soup = BeautifulSoup(res_text, "html.parser")
    divs = soup.find_all("div" ,class_='row battles-summary mb-3')
    divs = divs[0].find_all("div" ,class_='user-number')
    win_rate_50s = divs[1].text.strip()
    win_rate_24h = divs[2].text.strip()
    
    smalls = soup.find_all("small")

    if not len(smalls) == 9:
        print("[!] Format Error : XP")

    if gachi_rule == "▼ガチエリア":
        XP_now = smalls[1].text
        XP_max = smalls[5].text
    elif gachi_rule == "▼ガチヤグラ":
        XP_now = smalls[2].text
        XP_max = smalls[6].text
    elif gachi_rule == "▼ガチホコ":
        XP_now = smalls[3].text
        XP_max = smalls[7].text
    elif gachi_rule == "▼ガチアサリ":
        XP_now = smalls[4].text
        XP_max = smalls[8].text
    else:
        return False

    print("\t" + stat_account + "\t" + gachi_rule + "：" + gachi_stage)
    print("\t50戦勝率：" + win_rate_50s + "\t24h勝率：" +  win_rate_24h + "\tXP：" + XP_now + " / " + XP_max)
    return win_rate_50s, win_rate_24h, XP_now, XP_max


# stat.inkの戦績をもとに、メッセージを準備
def prepare_message(stats):
    str_stats = ""
    power = 0
    delta_power = 10
    match_num = 14
    win_num = 0
    
    # パワー期待値の計算
    for i in range(len(stats)):
        win_rate = stats[i][1].replace("%","")
        win_rate = float(win_rate)
        power = power + (win_rate/100 * 2 - 1) * (match_num/len(stats)) * delta_power
        win_num = win_num + match_num/len(stats)*(win_rate/100)
        
        if not str_stats == "":
            str_stats = str_stats + "\n"
        str_stats = str_stats  + " ┗ "  + stats[i][0] + " " + str(stats[i][1]) + "(" + str(stats[i][2]) + ")"

    power = round(power, 1)
    win_num = round(win_num, 1)

    # 評価基準
    if power >= 30:
        evaluation = "◎ 絶対行った方がいい！！"
    elif power >= 10:
        evaluation = "○ そこそこ期待できそう！"
    elif power >= 0:
        evaluation = "△ 悪くはない"
    elif power >= -10:
        evaluation = "？ 行っても無駄かも"
    else:
        evaluation = "× 大事故が起きます"

    msg = "{}\n次は {}\n{}\n\n" + str(match_num) + "戦した場合、" + str(win_num) + "勝。盛れるパワー期待値は" + str(power) + "\n⇒" + evaluation + "\n\n50戦勝率（24h勝率）\n" + str_stats

    return msg


# 生成したメッセージのTweetを自動送信
def tweet_message(msg):
    s = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    client = tweepy.Client(consumer_key=ck, consumer_secret=cs, access_token=at, access_token_secret=ats)
    msg = msg + "\n\n ... 自動ツイート " + s
    print("[+] tweeted!!")
    print(msg)
    client.create_tweet(text= msg)

    return True


# ステージ情報BOTのタイムラインを確認し、更新状況を把握
def get_stage_tweet(checked_id):
    t_lines = api.user_timeline(screen_name = tw_stage_info)

    if t_lines[0].id > checked_id :
        print("[+] New tweet found!! " + str(checked_id) + " -> " + str(t_lines[0].id))
        checked_id = t_lines[0].id
        text = t_lines[0].text
    else:
        # print("[-] No tweet")
        checked_id = checked_id
        text = "N/A"

    return checked_id, text


# 定期実行のためのメイン
def auto_stat_main(account_list):
    global checked_id
    try:
        print(checked_id)
        pass
    except:
        checked_id = 0
        print(checked_id)
        
    checked_id, text = get_stage_tweet(checked_id)

    for account in account_list:
        tw_account = account[0]
        stat_account = account[1]

        if not text == "N/A":
            gachi_time, gachi_rule, gachi_stages = get_stage(text)

            stats = []
            for st in gachi_stages:
                win_rate_50s, win_rate_24h, XP_now, XP_max = get_win_rate(stat_account, gachi_rule, st)
                stats.append([st, win_rate_50s, win_rate_24h])

            XP = "現在のXP " + XP_now + " / 最大XP " + XP_max
            msg = prepare_message(stats)
            msg = tw_account + "\n" + msg.format(gachi_time, gachi_rule, XP)

            # tweetの送信
            tweet_message(msg)


# スケジュールON
def job():
    s = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    print("[+] I'm working... "+s)
    auto_stat_main(account_list)


# スケジュールOFF
def cancel():
    schedule.clear()


# スケジュールを利用して定期実行
if __name__ == '__main__':
    # スケジュール設定
    rotation_sec = 300
    print("\n定期実行：毎" + str(rotation_sec) + "秒")
    schedule.every(rotation_sec).seconds.do(job)
    # schedule.every().day.at("14:47").do(cancel)

    while True:
        schedule.run_pending()
        time.sleep(60)
