import os
from flask import Flask, request
import telebot
import requests

TOKEN = "TOKEN = "8846968829:AAH1JyEqdPsTyUtPP9dL5J4uHnkQYXKLNfo"
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
    bot.reply_to(message, "🟢 Bot active hai! Stock ka naam bhejein (jaise: RELIANCE, TCS).")

@bot.message_handler(func=lambda message: True)
def handle_stock_query(message):
    query = message.text.strip().upper()
    if query.startswith('/'):
        return
        
    try:
        # Using NSE India public market summary endpoint alternative
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        url = f"https://www.google.com/finance/quote/{query}:NSE"
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            bot.reply_to(message, f"❌ Stock '{query}' nahi mila. Sahi symbol check karein.")
            return
            
        # Simple text parsing fallback for live data
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_div = soup.find(attrs={"class": "YMlKec fxKbKc"})
        if not price_div:
            bot.reply_to(message, f"⚠️ '{query}' ka price data fetch nahi ho paya.")
            return
            
        price_str = price_div.text.replace('₹', '').replace(',', '').strip()
        current_price = float(price_str)

        reply_msg = (
            f"📈 *Stock: {query} (NSE)*\n"
            f"💰 *Live Price*: ₹{current_price:.2f}"
        )
        bot.reply_to(message, reply_msg, parse_mode="Markdown")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error aa gaya. Dobara try karein.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
