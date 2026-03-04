import requests
import math
import time

TOKEN = "8337067248:AAE6K1vHDS2D70aoteozwM-1EWW9nVgimDo"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

ADMIN_ID = 8480843841
vip_users = {}

states = {}

prompts = [
    "Ev sahibi takımın adı nedir?",
    "Deplasman takımın adı nedir?",
    "Ev sahibinin evde oynadığı toplam maç sayısı?",
    "Ev sahibinin evde attığı toplam gol sayısı?",
    "Ev sahibinin evde yediği toplam gol sayısı?",
    "Deplasman takımının deplasmanda oynadığı toplam maç sayısı?",
    "Deplasman takımının deplasmanda attığı toplam gol sayısı?",
    "Deplasman takımının deplasmanda yediği toplam gol sayısı?",
    "Ligdeki toplam ev maç sayısı?",
    "Ligdeki tüm ev maçlarında atılan toplam gol sayısı?",
    "Ligdeki toplam deplasman maç sayısı?",
    "Ligdeki tüm deplasman maçlarında atılan toplam gol sayısı?"
]

keys = [
    "home_name", "away_name", "home_matches", "home_scored", "home_conceded",
    "away_matches", "away_scored", "away_conceded",
    "l_home_matches", "l_home_goals", "l_away_matches", "l_away_goals"
]

def send_message(chat_id, text):
    try:
        url = BASE_URL + "sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_updates(offset):
    try:
        url = BASE_URL + "getUpdates"
        params = {"offset": offset, "timeout": 30}
        r = requests.get(url, params=params, timeout=40)
        return r.json()
    except:
        return {"ok": False}

def calculate_alt_ust(home_name, away_name, hm, hs, hc, am, asc, ac, lhm, lhg, lam, lag):
    try:
        if hm <= 0 or am <= 0 or lhm <= 0 or lam <= 0:
            return "Hata: Maç sayıları sıfır veya negatif olamaz!"

        h_avg_s = hs / hm
        h_avg_c = hc / hm
        a_avg_s = asc / am
        a_avg_c = ac / am
        lh_avg = lhg / lhm
        la_avg = lag / lam

        home_attack = h_avg_s / lh_avg
        away_defense = a_avg_c / lh_avg
        lambda_home = home_attack * away_defense * lh_avg

        away_attack = a_avg_s / la_avg
        home_defense = h_avg_c / la_avg
        lambda_away = away_attack * home_defense * la_avg

        lambda_total = lambda_home + lambda_away

        def poisson_pmf(k, lam):
            return math.exp(-lam) * (lam ** k) / math.factorial(k)

        alt_prob = sum(poisson_pmf(k, lambda_total) for k in range(3))
        ust_prob = 1 - alt_prob

        result = f"""**{home_name} - {away_name} 2.5 Alt/Üst Analizi**

Beklenen Gol:
Ev: {lambda_home:.2f}
Dep: {lambda_away:.2f}
Toplam: {lambda_total:.2f}

**Alt 2.5** → %{alt_prob*100:.1f}
**Üst 2.5** → %{ust_prob*100:.1f}

Adil Oran:
Alt: {1/alt_prob:.2f}
Üst: {1/ust_prob:.2f}"""
        return result
    except:
        return "Hesaplama hatası."

print("🤖 Bot başlatıldı!")

offset = 0

while True:

    try:
        updates = get_updates(offset)

        if not updates.get("ok"):
            time.sleep(5)
            continue

        for u in updates.get("result", []):

            offset = u["update_id"] + 1

            if "message" not in u:
                continue

            msg = u["message"]

            if "text" not in msg:
                continue

            chat_id = msg["chat"]["id"]
            text = msg["text"].strip()

            if text == "/start":
                send_message(chat_id,"Merhaba!\nAnaliz için /analiz yaz.")
                continue


            # VIP EKLE
            if text.startswith("/vip_ekle") and chat_id == ADMIN_ID:

                try:

                    user_id = int(text.split()[1])

                    vip_users[user_id] = time.time() + 7*24*60*60

                    send_message(chat_id,f"{user_id} kullanıcısı 7 gün VIP oldu")

                except:

                    send_message(chat_id,"Kullanım:\n/vip_ekle USER_ID")

                continue


            # VIP SİL
            if text.startswith("/vip_sil") and chat_id == ADMIN_ID:

                try:

                    user_id = int(text.split()[1])

                    vip_users.pop(user_id,None)

                    send_message(chat_id,f"{user_id} VIP silindi")

                except:

                    send_message(chat_id,"Kullanım:\n/vip_sil USER_ID")

                continue


            if text == "/analiz":

                if chat_id not in vip_users or vip_users[chat_id] < time.time():

                    send_message(chat_id,"❌ Bu komut sadece VIP üyeler içindir.")

                    continue

                states[chat_id] = {"step":0,"values":{}}

                send_message(chat_id,prompts[0])

                continue


            if chat_id in states:

                step = states[chat_id]["step"]

                values = states[chat_id]["values"]

                if step < 2:

                    values[keys[step]] = text

                else:

                    try:

                        num = float(text)

                        if num < 0:

                            raise ValueError

                        values[keys[step]] = num

                    except:

                        send_message(chat_id,"❌ Pozitif sayı gir")

                        send_message(chat_id,prompts[step])

                        continue

                step += 1

                states[chat_id]["step"] = step

                if step < len(prompts):

                    send_message(chat_id,prompts[step])

                else:

                    v = values

                    result = calculate_alt_ust(

                        v["home_name"], v["away_name"],

                        v["home_matches"], v["home_scored"], v["home_conceded"],

                        v["away_matches"], v["away_scored"], v["away_conceded"],

                        v["l_home_matches"], v["l_home_goals"],

                        v["l_away_matches"], v["l_away_goals"]

                    )

                    send_message(chat_id,result)

                    del states[chat_id]

    except:

        time.sleep(5)
