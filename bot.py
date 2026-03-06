import math
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 8480843841

user_data_store = {}

steps = [
    "Home Team Name:",
    "Away Team Name:",
    "H5 BTTS (home last 5 btts count):",
    "A5 BTTS:",
    "H5+ (home goals scored last 5):",
    "H5- (home goals conceded last 5):",
    "A5+ (away goals scored last 5):",
    "A5- (away goals conceded last 5):"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data_store[user_id] = {"step":0,"data":[]}
    
    await update.message.reply_text(
        "Welcome to BTTS Analysis Bot\n\nSend data step by step.\n\n" + steps[0]
    )

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in user_data_store:
        return
    
    text = update.message.text
    step = user_data_store[user_id]["step"]
    
    user_data_store[user_id]["data"].append(text)
    user_data_store[user_id]["step"] += 1
    
    if step + 1 < len(steps):
        await update.message.reply_text(steps[step+1])
        return
    
    data = user_data_store[user_id]["data"]
    
    home = data[0]
    away = data[1]
    
    h5_btts = int(data[2])
    a5_btts = int(data[3])
    
    h5_plus = int(data[4])
    h5_minus = int(data[5])
    
    a5_plus = int(data[6])
    a5_minus = int(data[7])
    
    home_attack = h5_plus / 5
    home_defense = h5_minus / 5
    
    away_attack = a5_plus / 5
    away_defense = a5_minus / 5
    
    lambda_home = (home_attack + away_defense) / 2
    lambda_away = (away_attack + home_defense) / 2
    
    p_home0 = math.exp(-lambda_home)
    p_away0 = math.exp(-lambda_away)
    
    poisson = (1 - p_home0) * (1 - p_away0)
    
    trend = ((h5_btts/5) + (a5_btts/5)) / 2
    
    final = (poisson + trend) / 2
    
    percent = round(final * 100)
    
    result = "BTTS ✅" if percent >= 60 else "BTTS ⛔️"
    
    msg = f"""
{home} vs {away}

{result}
{percent}%
"""
    
    await update.message.reply_text(msg)
    
    del user_data_store[user_id]

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))
    
    app.run_polling()

if __name__ == "__main__":
    main()
