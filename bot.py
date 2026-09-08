import os
from flask import Flask, request
import telebot
import requests

TOKEN = "8744426734:AAFUI8IA9p5cW9SdPeXOeJ5Zy59oT78b5xQ"
GROUP_CHAT_ID = -1003915913228

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

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
    bot.reply_to(message, "🟢 Bot online hai! Stock ka symbol bhejein (jaise: TATAMOTORS, RELIANCE, SBIN).")

@bot.message_handler(func=lambda message: True)
def handle_stock_query(message):
    raw_query = message.text.upper().strip()
    if raw_query.startswith('/'):
        return
        
    query = raw_query.replace(" ", "")
    
    try:
        # Yahoo Finance alternative lightweight API endpoint (Vercel friendly)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{query}.NS?interval=1d&range=5d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        result = data.get('chart', {}).get('result')
        if not result:
            bot.reply_to(message, f"❌ Stock '{raw_query}' nahi mila. Sahi symbol check karein.")
            return
            
        meta = result[0]['meta']
        current_price = meta.get('regularMarketPrice')
        prev_close = meta.get('chartPreviousClose') or meta.get('previousClose')
        
        if not current_price or not prev_close:
            bot.reply_to(message, f"⚠️ '{raw_query}' ka live price data abhi available nahi hai.")
            return
            
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        indicators = result[0]['indicators']['quote'][0]
        day_high = max(indicators['high']) if 'high' in indicators and indicators['high'] else current_price
        day_low = min(indicators['low']) if 'low' in indicators and indicators['low'] else current_price

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
        bot.reply_to(message, f"⚠️ Connection error. Dobara koshish karein.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
