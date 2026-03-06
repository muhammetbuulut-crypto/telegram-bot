import requests
import math
import time

TOKEN = “8337067248:AAE6K1vHDS2D70aoteozwM-1EWW9nVgimDo”
BASE_URL = f”https://api.telegram.org/bot{TOKEN}/”

ADMIN_ID = 8480843841

states = {}
vip_users = {ADMIN_ID: 9999999999}

prompts = [
“Ev sahibi takımın adı nedir?”,
“Deplasman takımının adı nedir?”,
“Ev sahibinin evde oynadığı toplam maç sayısı?”,
“Ev sahibinin evde attığı toplam gol sayısı?”,
“Ev sahibinin evde yediği toplam gol sayısı?”,
“Deplasman takımının deplasmanda oynadığı toplam maç sayısı?”,
“Deplasman takımının deplasmanda attığı toplam gol sayısı?”,
“Deplasman takımının deplasmanda yediği toplam gol sayısı?”,
]

keys = [
“home_name”, “away_name”,
“home_matches”, “home_scored”, “home_conceded”,
“away_matches”, “away_scored”, “away_conceded”,
]

# ──────────────────────────────────────────────

def poisson(k, lam):
if lam <= 0:
return 1.0 if k == 0 else 0.0
return math.exp(-lam) * (lam ** k) / math.factorial(k)

def poisson_cumulative(max_k, lam):
return sum(poisson(k, lam) for k in range(max_k + 1))

def oneri(oran_ust, oran_alt, ust_label, alt_label):
if oran_ust >= oran_alt:
return f”🔺 {ust_label} önerilir ✅”
else:
return f”🔻 {alt_label} önerilir ✅”

# ──────────────────────────────────────────────

def calculate(home_name, away_name, hm, hs, hc, am, asc, ac):

```
if hm <= 0 or am <= 0:
    return None, None, "❌ Maç sayısı 0 olamaz."

h_avg_s = hs / hm
h_avg_c = hc / hm
a_avg_s = asc / am
a_avg_c = ac / am

genel_hucum  = (h_avg_s + a_avg_c) / 2
genel_defans = (h_avg_c + a_avg_s) / 2

home_attack  = h_avg_s / genel_hucum  if genel_hucum  > 0 else 1
home_defense = h_avg_c / genel_defans if genel_defans > 0 else 1
away_attack  = a_avg_s / genel_defans if genel_defans > 0 else 1
away_defense = a_avg_c / genel_hucum  if genel_hucum  > 0 else 1

lambda_home  = max(home_attack * away_defense * genel_hucum,  0.01)
lambda_away  = max(away_attack * home_defense * genel_defans, 0.01)
lambda_total = lambda_home + lambda_away

# Alt / Üst
alt15 = poisson_cumulative(1, lambda_total)
alt25 = poisson_cumulative(2, lambda_total)
alt35 = poisson_cumulative(3, lambda_total)
ust15 = 1 - alt15
ust25 = 1 - alt25
ust35 = 1 - alt35

# KG
p_home_sifir = poisson(0, lambda_home)
p_away_sifir = poisson(0, lambda_away)
kg_yok = p_home_sifir + p_away_sifir - p_home_sifir * p_away_sifir
kg_var = 1 - kg_yok

# ── Mesaj 1: Alt / Üst ──
altust_msg = (
    f"⚽ {home_name} - {away_name}\n"
    f"━━━━━━━━━━━━━━━━\n"
    f"📊 ALT / ÜST ANALİZİ\n\n"
    f"1.5  →  {oneri(ust15, alt15, 'ÜST 1.5', 'ALT 1.5')}\n"
    f"2.5  →  {oneri(ust25, alt25, 'ÜST 2.5', 'ALT 2.5')}\n"
    f"3.5  →  {oneri(ust35, alt35, 'ÜST 3.5', 'ALT 3.5')}\n"
    f"━━━━━━━━━━━━━━━━"
)

# ── Mesaj 2: KG ──
kg_msg = (
    f"⚽ {home_name} - {away_name}\n"
    f"━━━━━━━━━━━━━━━━\n"
    f"🔵 KG ANALİZİ\n\n"
    f"{oneri(kg_var, kg_yok, 'KG VAR', 'KG YOK')}\n"
    f"━━━━━━━━━━━━━━━━"
)

return altust_msg, kg_msg, None
```

# ──────────────────────────────────────────────

def send_message(chat_id, text):
url = BASE_URL + “sendMessage”
payload = {“chat_id”: chat_id, “text”: text}
try:
requests.post(url, json=payload, timeout=10)
except:
pass

def get_updates(offset):
url = BASE_URL + “getUpdates”
params = {“offset”: offset, “timeout”: 30}
try:
r = requests.get(url, params=params, timeout=40)
return r.json()
except:
return {“ok”: False}

# ──────────────────────────────────────────────

print(“BOT BAŞLADI ✅”)
offset = 0

while True:
updates = get_updates(offset)

```
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

    # ── /start ──
    if text == "/start":
        if chat_id not in vip_users or vip_users[chat_id] < time.time():
            send_message(chat_id,
                "Merhaba 👋\n\n"
                "VIP üyeliğiniz olmadığı için botu kullanamazsınız.\n\n"
                "🔑 7 Günlük VIP: 200₺\n"
                "📩 İletişim: @buulutz"
            )
        else:
            send_message(chat_id,
                "Merhaba Sayın VIP Üye 👑\n\n"
                "Komutlar:\n"
                "/analiz — Maç analizi başlat\n"
                "/iptal  — Analizi iptal et\n"
                "/vip    — VIP bitiş tarihiniz"
            )
        continue

    # ── /vip ──
    if text == "/vip":
        if chat_id in vip_users and vip_users[chat_id] > time.time():
            kalan = int((vip_users[chat_id] - time.time()) / 86400)
            send_message(chat_id, f"👑 VIP üyeliğiniz aktif.\n📅 Kalan süre: ~{kalan} gün")
        else:
            send_message(chat_id, "❌ Aktif VIP üyeliğiniz yok.")
        continue

    # ── /iptal ──
    if text == "/iptal":
        if chat_id in states:
            del states[chat_id]
            send_message(chat_id, "✅ Analiz iptal edildi.")
        else:
            send_message(chat_id, "Aktif bir analiz yok.")
        continue

    # ── Admin komutları ──
    if text.startswith("/vip_ekle") and chat_id == ADMIN_ID:
        try:
            user_id = int(text.split()[1])
            vip_users[user_id] = time.time() + 604800
            send_message(chat_id, f"✅ {user_id} için 7 günlük VIP eklendi.")
        except:
            send_message(chat_id, "Kullanım: /vip_ekle <user_id>")
        continue

    if text.startswith("/vip_sil") and chat_id == ADMIN_ID:
        try:
            user_id = int(text.split()[1])
            vip_users.pop(user_id, None)
            send_message(chat_id, f"✅ {user_id} VIP silindi.")
        except:
            send_message(chat_id, "Kullanım: /vip_sil <user_id>")
        continue

    if text == "/vip_liste" and chat_id == ADMIN_ID:
        aktif = [(uid, int((exp - time.time()) / 86400))
                 for uid, exp in vip_users.items() if exp > time.time()]
        if aktif:
            liste = "\n".join(f"👤 {uid} — {gun} gün" for uid, gun in aktif)
            send_message(chat_id, f"👑 Aktif VIP Kullanıcılar:\n\n{liste}")
        else:
            send_message(chat_id, "Aktif VIP kullanıcı yok.")
        continue

    if text.startswith("/duyuru") and chat_id == ADMIN_ID:
        mesaj = text.replace("/duyuru", "").strip()
        if mesaj:
            for uid in list(vip_users.keys()):
                send_message(uid, "📢 DUYURU\n\n" + mesaj)
            send_message(chat_id, "✅ Duyuru gönderildi.")
        else:
            send_message(chat_id, "Kullanım: /duyuru <mesaj>")
        continue

    # ── /analiz ──
    if text == "/analiz":
        if chat_id not in vip_users or vip_users[chat_id] < time.time():
            send_message(chat_id, "❌ Bu özellik sadece VIP üyeler içindir.")
            continue
        states[chat_id] = {"step": 0, "values": {}}
        send_message(chat_id, prompts[0])
        continue

    # ── Analiz adımları ──
    if chat_id in states:
        step   = states[chat_id]["step"]
        values = states[chat_id]["values"]

        if step < 2:
            values[keys[step]] = text
        else:
            try:
                val = float(text.replace(",", "."))
                if val < 0:
                    send_message(chat_id, "❌ Negatif değer girilemez. Tekrar girin:")
                    continue
                values[keys[step]] = val
            except:
                send_message(chat_id, "⚠️ Lütfen geçerli bir sayı girin:")
                continue

        step += 1
        states[chat_id]["step"] = step

        if step < len(prompts):
            send_message(chat_id, prompts[step])
        else:
            v = values
            altust_msg, kg_msg, hata = calculate(
                v["home_name"], v["away_name"],
                v["home_matches"], v["home_scored"], v["home_conceded"],
                v["away_matches"], v["away_scored"], v["away_conceded"],
            )

            if hata:
                send_message(chat_id, hata)
            else:
                send_message(chat_id, altust_msg)
                time.sleep(0.5)
                send_message(chat_id, kg_msg)

            del states[chat_id]
```
