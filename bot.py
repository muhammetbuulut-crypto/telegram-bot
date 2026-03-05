import requests
import math
import time
import json
import os
from PIL import Image, ImageDraw, ImageFont

TOKEN = "8337067248:AAE6K1vHDS2D70aoteozwM-1EWW9nVgimDo"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

ADMIN_ID = 8480843841
VIP_FILE = "vip_users.json"

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

def send_photo(chat_id, photo_path, caption=""):
    url = BASE_URL + "sendPhoto"
    files = {'photo': open(photo_path, 'rb')}
    payload = {"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, files=files)
    except:
        pass
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)  # temizlik

def create_result_image(home, away, lh, la, p1, px, p2):
    WIDTH, HEIGHT = 900, 1250
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 25, 55))  # koyu futbol mavisi
    draw = ImageDraw.Draw(img)

    # Fontlar (Windows'ta arial, Linux'ta DejaVu dener)
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 65)
        font_big   = ImageFont.truetype("arial.ttf", 85)
        font_med   = ImageFont.truetype("arial.ttf", 55)
        font_small = ImageFont.truetype("arial.ttf", 40)
    except:
        try:
            font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 65)
            font_big   = ImageFont.truetype("DejaVuSans.ttf", 85)
            font_med   = ImageFont.truetype("DejaVuSans.ttf", 55)
            font_small = ImageFont.truetype("DejaVuSans.ttf", 40)
        except:
            font_title = font_big = font_med = font_small = ImageFont.load_default()

    # Bot adı
    draw.text((WIDTH//2, 60), "İLK YARI TAHMİN BOTU", font=font_title, fill="#FFD700", anchor="mt")

    # Takımlar
    draw.text((WIDTH//2, 180), f"{home} - {away}", font=font_big, fill="white", anchor="mt")

    # Başlık
    draw.text((WIDTH//2, 290), "İLK YARI SONUCU TAHMİNİ", font=font_med, fill="#00FF88", anchor="mt")

    # Olasılıklar
    y = 420
    draw.text((180, y), "🏠 1", font=font_med, fill="white")
    draw.text((WIDTH//2 + 80, y), f"%{p1*100:.1f}", font=font_big, fill="#FFD700", anchor="lm")

    y += 140
    draw.text((180, y), "🤝 X", font=font_med, fill="white")
    draw.text((WIDTH//2 + 80, y), f"%{px*100:.1f}", font=font_big, fill="#FFD700", anchor="lm")

    y += 140
    draw.text((180, y), "🚀 2", font=font_med, fill="white")
    draw.text((WIDTH//2 + 80, y), f"%{p2*100:.1f}", font=font_big, fill="#FFD700", anchor="lm")

    # Beklenen gol + tahmini skor
    y += 170
    draw.text((WIDTH//2, y), f"Beklenen Gol: {lh:.2f} - {la:.2f}", font=font_small, fill="#CCCCCC", anchor="mt")

    y += 90
    draw.text((WIDTH//2, y), f"Tahmini Skor: {round(lh)} - {round(la)}", font=font_med, fill="#00FF88", anchor="mt")

    # Watermark (X paylaşımı için)
    draw.text((WIDTH//2, HEIGHT-50), "X'te paylaş • @buulutz", font=font_small, fill="#666666", anchor="mb")

    # Kenarlık
    draw.rectangle([20, 20, WIDTH-20, HEIGHT-20], outline="#FFD700", width=8)

    path = "ilk_yari_sonuc.png"
    img.save(path, quality=95)
    return path

def calculate_first_half(home_name, away_name, hm, hs, hc, am, asc, ac, lhm, lhg, lam, lag):
    if hm == 0 or am == 0 or lhm == 0 or lam == 0:
        return None, "❌ Maç sayısı 0 olamaz!"

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

    def poisson(k, lam):
        if lam <= 0: return 1.0 if k == 0 else 0.0
        try:
            return math.exp(-lam) * (lam ** k) / math.factorial(k)
        except:
            return 0.0

    p_home = p_draw = p_away = 0.0
    for h in range(0, 8):
        for a in range(0, 8):
            prob = poisson(h, lambda_home) * poisson(a, lambda_away)
            if h > a: p_home += prob
            elif h == a: p_draw += prob
            else: p_away += prob

    total = p_home + p_draw + p_away
    if total > 0:
        p_home /= total
        p_draw /= total
        p_away /= total

    image_path = create_result_image(home_name, away_name, lambda_home, lambda_away, p_home, p_draw, p_away)
    return image_path, None

print("📸 İLK YARI FOTOĞRAF BOTU BAŞLADI 🚀")

offset = 0
while True:
    updates = get_updates(offset)   # (get_updates fonksiyonu aşağıda aynı kalıyor)
    # ... (get_updates fonksiyonunu aşağıya ekledim, tam kodu kopyala)

    # (Kodun geri kalanı aynı, sadece /analiz kısmını değiştiriyorum)

        if text == "/analiz":
            if chat_id not in vip_users or vip_users[chat_id] < time.time():
                send_message(chat_id, "❌ Bu özellik sadece VIP üyeler içindir.")
                continue
            states[chat_id] = {"step": 0, "values": {}}
            send_message(chat_id, prompts[0])
            continue

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
                image_path, error = calculate_first_half(
                    v["home_name"], v["away_name"],
                    v["home_matches"], v["home_scored"], v["home_conceded"],
                    v["away_matches"], v["away_scored"], v["away_conceded"],
                    v["l_home_matches"], v["l_home_goals"],
                    v["l_away_matches"], v["l_away_goals"]
                )

                if error:
                    send_message(chat_id, error)
                else:
                    caption = f"<b>{v['home_name']} - {v['away_name']}</b>\nİlk Yarı Tahmini 📸\nX'te paylaşabilirsin!"
                    send_photo(chat_id, image_path, caption)

                if chat_id in states:
                    del states[chat_id]

# get_updates fonksiyonu (kodun en altına ekle)
def get_updates(offset):
    url = BASE_URL + "getUpdates"
    params = {"offset": offset, "timeout": 30}
    try:
        r = requests.get(url, params=params, timeout=40)
        return r.json()
    except:
        return {"ok": False}
