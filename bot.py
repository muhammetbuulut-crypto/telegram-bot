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

def skor_olasiligi(h, a, lh, la):
return poisson(h, lh) * poisson(a, la)

def mac_sonu(lh, la, max_gol=8):
ev, ber, dep = 0, 0, 0
for h in range(max_gol):
for a in range(max_gol):
p = skor_olasiligi(h, a, lh, la)
if h > a:
ev += p
elif h == a:
ber += p
else:
dep += p
return ev, ber, dep

def ihalftime_label(h, a):
if h > a:
return “1”
elif h == a:
return “X”
else:
return “2”

def fulltime_label(h, a):
if h > a:
return “1”
elif h == a:
return “X”
else:
return “2”

# ──────────────────────────────────────────────

def calculate(home_name, away_name, hm, hs, hc, am, asc, ac):
if hm <= 0 or am <= 0:
return None, “❌ Maç sayısı 0 olamaz.”

```
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

lambda_home = max(home_attack * away_defense * genel_hucum,  0.01)
lambda_away = max(away_attack * home_defense * genel_defans, 0.01)

# İlk yarı için lambda yarıya indirilir (yaklaşık model)
lh_iy = lambda_home * 0.45
la_iy = lambda_away * 0.45

# Tüm İY/MS kombinasyonlarını hesapla
max_gol = 7
iyms = {}

for h_iy in range(max_gol):
    for a_iy in range(max_gol):
        p_iy = skor_olasiligi(h_iy, a_iy, lh_iy, la_iy)
        if p_iy < 0.0001:
            continue
        iy_label = ihalftime_label(h_iy, a_iy)

        for h_ms in range(max_gol):
            for a_ms in range(max_gol):
                # Maç sonu skoru ilk yarıdan az olamaz
                if h_ms < h_iy or a_ms < a_iy:
                    continue

                # 2. yarı gollerini ayrıca hesapla
                h_2y = h_ms - h_iy
                a_2y = a_ms - a_iy
                lh_2y = lambda_home * 0.55
                la_2y = lambda_away * 0.55
                p_2y = skor_olasiligi(h_2y, a_2y, lh_2y, la_2y)
                if p_2y < 0.0001:
                    continue

                ms_label = fulltime_label(h_ms, a_ms)
                key = f"{iy_label}/{ms_label}"
                iyms[key] = iyms.get(key, 0) + p_iy * p_2y

# En olası İY/MS bul
en_olasilар = sorted(iyms.items(), key=lambda x: x[1], reverse=True)
en_iyi_key, en_iyi_oran = en_olasilар[0]

# Maç sonu genel tahmini (bilgi amaçlı)
ev, ber, dep = mac_sonu(lambda_home, lambda_away)
if ev >= ber and ev >= dep:
    ms_genel = f"1 (Ev Sahibi) — %{ev*100:.0f}"
elif ber >= ev and ber >= dep:
    ms_genel = f"X (Beraberlik) — %{ber*100:.0f}"
else:
    ms_genel = f"2 (Deplasman) — %{dep*100:.0f}"

msg = (
    f"⚽ {home_name} - {away_name}\n"
    f"━━━━━━━━━━━━━━━━\n"
    f"📊 İY/MS ANALİZİ\n\n"
    f"🎯 Öneri:  {en_iyi_key}  ✅\n"
    f"📈 Olasılık: %{en_iyi_oran*100:.1f}\n\n"
    f"🏆 Maç Sonu Tahmini: {ms_genel}\n"
    f"━━━━━━━━━━━━━━━━"
)

return msg, None
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
                "/analiz — İY/MS analizi başlat\n"
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
            send_message(chat_id, f"({step}/{len(prompts)-1}) " + prompts[step])
        else:
            v = values
            result, hata = calculate(
                v["home_name"], v["away_name"],
                v["home_matches"], v["home_scored"], v["home_conceded"],
                v["away_matches"], v["away_scored"], v["away_conceded"],
            )

            if hata:
                send_message(chat_id, hata)
            else:
                send_message(chat_id, result)

            del states[chat_id]
```
