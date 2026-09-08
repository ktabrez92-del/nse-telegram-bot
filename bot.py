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
    bot.reply_to(message, "🟢 Bot online hai! Kisi bhi stock ka naam bhejein (jaise: RELIANCE, TATAMOTORS, TCS).")

@bot.message_handler(func=lambda message: True)
def handle_stock_query(message):
    query = message.text.strip()
    if query.startswith('/'):
        return
        
    try:
        # Groww/NSE public search API (Never blocked on Vercel)
        search_url = f"https://groww.in/v1/api/search/v1/query?page=0&q={query}&size=1"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(search_url, headers=headers, timeout=5).json()
        
        stocks = res.get('data', {}).get('stocks', [])
        if not stocks:
            bot.reply_to(message, f"❌ Stock '{query}' nahi mila. Sahi naam likhein.")
            return
            
        stock_info = stocks[0]
        live_price = stock_info.get('livePriceOrLtp')
        close_price = stock_info.get('close') or live_price
        title = stock_info.get('companyName', query.upper())
        
        if not live_price:
            bot.reply_to(message, f"⚠️ '{title}' ka live price abhi available nahi hai.")
            return
            
        change = live_price - close_price
        change_pct = (change / close_price) * 100 if close_price else 0.0

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
            f"📈 *Stock: {title}*\n"
            f"💰 *Price*: ₹{live_price:.2f}\n"
            f"📊 *Change*: {change_pct:+.2f}% {grade}"
        )
        bot.reply_to(message, reply_msg, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Server connection error. Dobara try karein.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
