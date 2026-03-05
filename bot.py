import requests
import math
import time
import json
import os

TOKEN = "8337067248:AAE6K1vHDS2D70aoteozwM-1EWW9nVgimDo"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

ADMIN_ID = 8480843841
VIP_FILE = "vip_users.json"


def load_vip():
    if os.path.exists(VIP_FILE):
        try:
            with open(VIP_FILE,"r",encoding="utf-8") as f:
                data=json.load(f)
                return {int(k):v for k,v in data.items()}
        except:
            pass
    return {ADMIN_ID:9999999999}


def save_vip(vip_dict):
    with open(VIP_FILE,"w",encoding="utf-8") as f:
        json.dump({str(k):v for k,v in vip_dict.items()},f)


vip_users=load_vip()
states={}


prompts=[
"Ev sahibi takımın adı nedir?",
"Deplasman takımın adı nedir?",
"Ev sahibinin evde oynadığı toplam maç sayısı?",
"Ev sahibinin evde ilk yarı attığı toplam gol sayısı?",
"Ev sahibinin evde ilk yarı yediği toplam gol sayısı?",
"Deplasman takımının deplasmanda oynadığı toplam maç sayısı?",
"Deplasman takımının deplasmanda ilk yarı attığı toplam gol sayısı?",
"Deplasman takımının deplasmanda ilk yarı yediği toplam gol sayısı?",
"Ligdeki toplam ev maç sayısı?",
"Ligdeki tüm ev maçlarında ilk yarı atılan toplam gol sayısı?",
"Ligdeki toplam deplasman maç sayısı?",
"Ligdeki tüm deplasman maçlarında ilk yarı atılan toplam gol sayısı?"
]


keys=[
"home_name","away_name","home_matches","home_scored","home_conceded",
"away_matches","away_scored","away_conceded",
"l_home_matches","l_home_goals","l_away_matches","l_away_goals"
]


def send_message(chat_id,text):
    url=BASE_URL+"sendMessage"
    payload={"chat_id":chat_id,"text":text,"parse_mode":"HTML"}
    try:
        requests.post(url,json=payload,timeout=10)
    except:
        pass


def get_updates(offset):
    url=BASE_URL+"getUpdates"
    params={"offset":offset,"timeout":30}
    try:
        r=requests.get(url,params=params,timeout=40)
        return r.json()
    except:
        return {"ok":False}


def calculate_first_half(home_name,away_name,hm,hs,hc,am,asc,ac,lhm,lhg,lam,lag):

    if hm==0 or am==0:
        return "❌ Maç sayısı 0 olamaz!"

    h_avg_s=hs/hm
    h_avg_c=hc/hm
    a_avg_s=asc/am
    a_avg_c=ac/am

    lambda_home=(h_avg_s+a_avg_c)/2
    lambda_away=(a_avg_s+h_avg_c)/2


    def poisson(k,l):
        if l<=0:
            return 1.0 if k==0 else 0.0
        return math.exp(-l)*(l**k)/math.factorial(k)


    p_home=0
    p_draw=0
    p_away=0


    for h in range(8):
        for a in range(8):

            prob=poisson(h,lambda_home)*poisson(a,lambda_away)

            if h>a:
                p_home+=prob
            elif h==a:
                p_draw+=prob
            else:
                p_away+=prob


    total=p_home+p_draw+p_away

    if total>0:
        p_home/=total
        p_draw/=total
        p_away/=total


    best=max(p_home,p_draw,p_away)

    if best<0.45:
        prediction="⚠️ Net tahmin yok"
    else:
        if best==p_home:
            prediction="İY 1"
        elif best==p_draw:
            prediction="İY X"
        else:
            prediction="İY 2"


    lambda_total=lambda_home+lambda_away

    alt=0
    for k in range(3):
        alt+=poisson(k,lambda_total)

    ust=1-alt


    odd_home=1/p_home if p_home>0 else 0
    odd_draw=1/p_draw if p_draw>0 else 0
    odd_away=1/p_away if p_away>0 else 0

    odd_alt=1/alt if alt>0 else 0
    odd_ust=1/ust if ust>0 else 0


    result=f"""
🔥 <b>{home_name} - {away_name}</b>

<b>İLK YARI SONUCU</b>

Tahmin: <b>{prediction}</b>

🏠 1 → %{p_home*100:.1f} | Adil: {odd_home:.2f}
🤝 X → %{p_draw*100:.1f} | Adil: {odd_draw:.2f}
🚀 2 → %{p_away*100:.1f} | Adil: {odd_away:.2f}

<b>2.5 ALT / ÜST</b>

🔻 ALT → %{alt*100:.1f} | Adil: {odd_alt:.2f}
🔺 ÜST → %{ust*100:.1f} | Adil: {odd_ust:.2f}

Beklenen Gol
Ev: {lambda_home:.2f}
Dep: {lambda_away:.2f}
"""

    return result



print("BOT BASLADI")

offset=0


while True:

    updates=get_updates(offset)

    if not updates.get("ok"):
        time.sleep(5)
        continue


    for u in updates.get("result",[]):

        offset=u["update_id"]+1

        if "message" not in u:
            continue

        msg=u["message"]

        if "text" not in msg:
            continue

        chat_id=msg["chat"]["id"]
        text=msg["text"].strip()


        if text=="/start":

            if chat_id not in vip_users or vip_users[chat_id]<time.time():

                send_message(
                    chat_id,
                    "❌ VIP Üyeliğiniz Yok\n\n"
                    "7 Günlük VIP: 200₺\n"
                    "İletişim: @buulutz"
                )

            else:

                send_message(
                    chat_id,
                    "👑 Merhaba SAYIN VIP ÜYE\n\n"
                    "Komutlar:\n"
                    "/analiz"
                )

            continue



        if text.startswith("/vip_ekle") and chat_id==ADMIN_ID:

            try:

                user_id=int(text.split()[1])

                vip_users[user_id]=time.time()+604800

                save_vip(vip_users)

                send_message(chat_id,"VIP eklendi")

            except:

                send_message(chat_id,"Kullanım: /vip_ekle ID")

            continue



        if text.startswith("/vip_sil") and chat_id==ADMIN_ID:

            try:

                user_id=int(text.split()[1])

                vip_users.pop(user_id,None)

                save_vip(vip_users)

                send_message(chat_id,"VIP silindi")

            except:
                pass

            continue



        if text=="/analiz":

            if chat_id not in vip_users or vip_users[chat_id]<time.time():

                send_message(chat_id,"❌ Bu analiz VIP üyeler içindir.")

                continue


            states[chat_id]={"step":0,"values":{}}

            send_message(chat_id,prompts[0])

            continue



        if chat_id in states:

            step=states[chat_id]["step"]
            values=states[chat_id]["values"]


            if step<2:

                values[keys[step]]=text

            else:

                try:

                    values[keys[step]]=float(text)

                except:

                    send_message(chat_id,"❌ Lütfen sayı giriniz")

                    continue


            step+=1
            states[chat_id]["step"]=step


            if step<len(prompts):

                send_message(chat_id,prompts[step])

            else:

                v=values

                result=calculate_first_half(
                    v["home_name"],
                    v["away_name"],
                    v["home_matches"],
                    v["home_scored"],
                    v["home_conceded"],
                    v["away_matches"],
                    v["away_scored"],
                    v["away_conceded"],
                    v["l_home_matches"],
                    v["l_home_goals"],
                    v["l_away_matches"],
                    v["l_away_goals"]
                )

                send_message(chat_id,result)

                del states[chat_id]
