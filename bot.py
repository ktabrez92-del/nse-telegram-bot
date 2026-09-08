import os
from flask import Flask, request
import telebot
import requests

TOKEN = "8744426734:AAFUI8IA9p5cW9SdPeXOeJ5Zy59oT78b5xQ"
GROUP_CHAT_ID = -1003915913228

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# Symbol mapping
SYMBOL_MAP = {
    "TATA MOTORS": "TATAMOTORS",
    "TATAMOTORS": "TATAMOTORS",
    "SONATA SOFTWARE": "SONATSOFTW",
    "SONATASOFTWARE": "SONATSOFTW",
    "RELIANCE": "RELIANCE",
    "SBI": "SBIN",
    "SBIN": "SBIN",
    "TCS": "TCS",
    "INFY": "INFY",
    "WIPRO": "WIPRO",
    "ITC": "ITC",
    "TATA STEEL": "TATASTEEL",
    "TATASTEEL": "TATASTEEL"
}

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return "Telegram Bot is active on Vercel!"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🟢 Bot online hai! Stock ka symbol bhejein (jaise: TATAMOTORS, RELIANCE, TCS).")

@bot.message_handler(func=lambda message: True)
def handle_stock_query(message):
    raw_query = message.text.upper().strip()
    if raw_query.startswith('/'):
        return
        
    clean_query = raw_query.replace("  ", " ")
    query = SYMBOL_MAP.get(raw_query, SYMBOL_MAP.get(clean_query, clean_query.replace(" ", "")))
    
    try:
        # Session with full browser headers to prevent Yahoo blocking
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://finance.yahoo.com"
        })
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{query}.NS?interval=1d&range=5d"
        response = session.get(url, timeout=6)
        data = response.json()
        
        result = data.get('chart', {}).get('result')
        if not result:
            bot.reply_to(message, f"❌ Stock '{raw_query}' nahi mila. Sahi NSE symbol check karein.")
            return
            
        meta = result[0]['meta']
        current_price = meta.get('regularMarketPrice')
        prev_close = meta.get('chartPreviousClose') or meta.get('previousClose')
        
        if not current_price or not prev_close:
            bot.reply_to(message, f"⚠️ '{raw_query}' ka live price data abhi available nahi hai.")
            return
            
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        indicators = result[0]['indicators']['quote'][0]
        day_high = max(filter(None, indicators.get('high', [current_price])))
        day_low = min(filter(None, indicators.get('low', [current_price])))

        if change_pct > 2.0:
            grade = "🟢 *VERY GOOD*"
        elif change_pct > 0:
            grade = "🟢 *GOOD*"
        elif change_pct == 0:
            grade = "⚪ *NEUTRAL*"
        elif change_pct > -2.0:
            grade = "🔴 *BAD*"
        else:
            grade = "🔴 *VERY BAD*"

        reply_msg = (
            f"📈 *Stock: {query}*\n"
            f"💰 *Price*: ₹{current_price:.2f}\n"
            f"📊 *Change*: {change_pct:+.2f}% {grade}\n"
            f"📌 *Day High*: ₹{day_high:.2f} | *Day Low*: ₹{day_low:.2f}"
        )
        bot.reply_to(message, reply_msg, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Connection error aa gaya. Dobara koshish karein.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
