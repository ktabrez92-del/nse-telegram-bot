import os
from flask import Flask, request
import telebot
import requests
from bs4 import BeautifulSoup

TOKEN = "8744426734:AAHnITXqS8yTC-S2wOk8FSewqAiQudBwN2o"
GROUP_CHAT_ID = -1003915913228

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        try:
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
        except Exception as e:
            print(f"Error: {e}")
        return '', 200
    return "Telegram Bot is active on Vercel!"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🟢 Market Bot active hai! Kisi bhi NSE stock ka naam bhejein (jaise: RELIANCE, TCS, TATAMOTORS).")

@bot.message_handler(func=lambda message: True)
def handle_stock_query(message):
    query = message.text.strip().upper()
    if query.startswith('/'):
        return
        
    sent_msg = bot.reply_to(message, f"🔍 Fetching market data for {query}...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        url = f"https://www.google.com/finance/quote/{query}:NSE"
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            bot.edit_message_text(f"❌ Stock '{query}' nahi mila. Sahi NSE symbol check karein.", chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Price fetch
        price_div = soup.find(attrs={"class": "YMlKec fxKbKc"})
        if not price_div:
            bot.edit_message_text(f"⚠️ '{query}' ka price data fetch nahi ho paya.", chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)
            return
            
        price_str = price_div.text.replace('₹', '',).replace(',', '').strip()
        current_price = float(price_str)

        # Percentage change fetch (Market feature)
        change_div = soup.find(attrs={"class": "JwB6zf"})
        change_text = change_div.text if change_div else "N/A"
        
        # Emoji based on market trend
        trend_emoji = "🟢" if "-" not in change_text else "🔴"

        reply_msg = (
            f"📈 *Stock: {query} (NSE)*\n"
            f"💰 *Live Price*: ₹{current_price:.2f}\n"
            f"📊 *Change*: {trend_emoji} {change_text}"
        )
        bot.edit_message_text(reply_msg, chat_id=sent_msg.chat.id, message_id=sent_msg.message_id, parse_mode="Markdown")
        
    except Exception as e:
        bot.edit_message_text(f"⚠️ Market server error. Dobara try karein.", chat_id=sent_msg.chat.id, message_id=sent_msg.message_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
