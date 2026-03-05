import requests
import math
import time
import json
import os

TOKEN = "8337067248:AAE6K1vHDS2D70aoteozwM-1EWW9nVgimDo"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

ADMIN_ID = 8480843841
VIP_FILE = "vip_users.json"

# VIP'leri dosyadan yükle
def load_vip():
    if os.path.exists(VIP_FILE):
        try:
            with open(VIP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except:
            pass
    return {ADMIN_ID: 9999999999}

def save_vip(vip_dict):
    with open(VIP_FILE, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in vip_dict.items()}, f, ensure_ascii=False)

vip_users = load_vip()
states = {}

prompts = [
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

keys = [
"home_name","away_name","home_matches","home_scored","home_conceded",
"away_matches","away_scored","away_conceded",
"l_home_matches","l_home_goals","l_away_matches","l_away_goals"
]

def send_message(chat_id, text):
    url = BASE_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_updates(offset):
    url = BASE_URL + "getUpdates"
    params = {"offset": offset, "timeout": 30}
    try:
        r = requests.get(url, params=params, timeout=40)
        return r.json()
    except:
        return {"ok": False}

def calculate_first_half(home_name, away_name, hm, hs, hc, am, asc, ac, lhm, lhg, lam, lag):
    if hm == 0 or am == 0 or lhm == 0 or lam == 0:
        return "❌ Maç sayısı 0 olamaz! Lütfen geçerli değerler giriniz."

    # Ortalamalar
    h_avg_s = hs / hm
    h_avg_c = hc / hm
    a_avg_s = asc / am
    a_avg_c = ac / am
    lh_avg = lhg / lhm
    la_avg = lag / lam

    # İlk yarı lambda hesaplaması (aynı mantık, çünkü veriler artık ilk yarı)
    home_attack = h_avg_s / lh_avg
    away_defense = a_avg_c / lh_avg
    lambda_home = home_attack * away_defense * lh_avg

    away_attack = a_avg_s / la_avg
    home_defense = h_avg_c / la_avg
    lambda_away = away_attack * home_defense * la_avg

    # Poisson
    def poisson(k, lam):
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        try:
            return math.exp(-lam) * (lam ** k) / math.factorial(k)
        except:
            return 0.0

    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0

    for h in range(7):
        for a in range(7):
            prob = poisson(h, lambda_home) * poisson(a, lambda_away)
            if h > a:
                p_home += prob
            elif h == a:
                p_draw += prob
            else:
                p_away += prob

    total = p_home + p_draw + p_away
    if total > 0:
        p_home /= total
        p_draw /= total
        p_away /= total

    result = f"""
🔥 <b>{home_name} - {away_name}</b> 🔥

<b>İLK YARI SONUCU TAHMİNİ</b>

Beklenen İlk Yarı Gol:
🏠 Ev: <b>{lambda_home:.2f}</b>
🚀 Dep: <b>{lambda_away:.2f}</b>

📊 <b>Olasılıklar</b>
🏆 Ev Sahibi Kazanır (1) → <b>%{p_home*100:.1f}</b>   Adil Oran: <b>{1/p_home:.2f}</b>
🤝 Beraberlik (X) → <b>%{p_draw*100:.1f}</b>   Adil Oran: <b>{1/p_draw:.2f}</b>
🏴 Deplasman Kazanır (2) → <b>%{p_away*100:.1f}</b>   Adil Oran: <b>{1/p_away:.2f}</b>

Tahmini En Muhtemel Skor: <b>{round(lambda_home)} - {round(lambda_away)}</b>
"""
    return result

print("İLK YARI SONUCU BOTU BAŞLADI 🚀")

offset = 0
while True:
    updates = get_updates(offset)
    if not updates.get("ok"):
        time.sleep(5)
        continue

    for u in updates.get("result", []):
        offset = u["update_id"] + 1

        if "message" not in u or "text" not in u["message"]:
            continue

        msg = u["message"]
        chat_id = msg["chat"]["id"]
        text = msg["text"].strip()

        if text == "/start":
            if chat_id not in vip_users or vip_users[chat_id] < time.time():
                send_message(chat_id, "Merhaba 👋\n\nVip Üyeliğiniz Yok.\n\n7 Günlük VIP: 200₺\nİletişim: @buulutz")
            else:
                send_message(chat_id, "Merhaba SAYIN VIP 👑\n\nKomut: /analiz")
            continue

        # Admin komutları
        if text.startswith("/vip_ekle") and chat_id == ADMIN_ID:
            try:
                user_id = int(text.split()[1])
                vip_users[user_id] = time.time() + 604800
                save_vip(vip_users)
                send_message(chat_id, f"✅ VIP eklendi (7 gün) → {user_id}")
            except:
                send_message(chat_id, "Kullanım: /vip_ekle ID")
            continue

        if text.startswith("/vip_sil") and chat_id == ADMIN_ID:
            try:
                user_id = int(text.split()[1])
                vip_users.pop(user_id, None)
                save_vip(vip_users)
                send_message(chat_id, "✅ VIP silindi")
            except:
                pass
            continue

        if text.startswith("/duyuru") and chat_id == ADMIN_ID:
            mesaj = text.replace("/duyuru ", "")
            for uid in list(vip_users.keys()):
                send_message(uid, f"📢 DUYURU\n\n{mesaj}")
            send_message(chat_id, "Duyuru gönderildi")
            continue

        if text == "/analiz":
            if chat_id not in vip_users or vip_users[chat_id] < time.time():
                send_message(chat_id, "❌ Bu özellik sadece VIP üyeler içindir.")
                continue
            states[chat_id] = {"step": 0, "values": {}}
            send_message(chat_id, prompts[0])
            continue

        # Analiz adımları
        if chat_id in states:
            step = states[chat_id]["step"]
            values = states[chat_id]["values"]

            if step < 2:
                values[keys[step]] = text
            else:
                try:
                    values[keys[step]] = float(text)
                except:
                    send_message(chat_id, "❌ Lütfen sayı giriniz!")
                    continue

            step += 1
            states[chat_id]["step"] = step

            if step < len(prompts):
                send_message(chat_id, prompts[step])
            else:
                v = values
                result = calculate_first_half(
                    v["home_name"], v["away_name"],
                    v["home_matches"], v["home_scored"], v["home_conceded"],
                    v["away_matches"], v["away_scored"], v["away_conceded"],
                    v["l_home_matches"], v["l_home_goals"],
                    v["l_away_matches"], v["l_away_goals"]
                )
                send_message(chat_id, result)
                del states[chat_id]
