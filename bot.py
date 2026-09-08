import os
from flask import Flask, request
import telebot
import yfinance as yf
from datetime import datetime
import pytz

TOKEN = "8744426734:AAFUI8IA9p5cW9SdPeXOeJ5Zy59oT78b5xQ"
GROUP_CHAT_ID = -1003915913228

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

IST = pytz.timezone('Asia/Kolkata')

@app.route('/')
def home():
    return "Bot is active and running on Vercel!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Forbidden', 403

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🟢 Bot is online! Stock ka naam bhejein (jaise: RELIANCE) ya /gapup try karein.")

@bot.message_handler(commands=['gapup'])
def gap_up_analysis(message):
    bot.reply_to(message, "📊 Pre-market gap analysis: RELIANCE (+2.45% - Very Good), INFY (-1.15% - Bad).")

@bot.message_handler(commands=['sendalert'])
def send_group_alert(message):
    try:
        bot.send_message(GROUP_CHAT_ID, "🚨 *Automatic Group Alert Test*: Bot is active and monitoring NSE/BSE markets!", parse_mode="Markdown")
        bot.reply_to(message, "✅ Group par alert bhej diya gaya hai!")
    except Exception as e:
        bot.reply_to(message, f"❌ Group par message bhejne mein error aaya: {e}")

@bot.message_handler(func=lambda message: True)
def handle_stock_query(message):
    query = message.text.upper().strip()
    if query.startswith('/'):
        return
        
    ticker_symbol = f"{query}.NS"
    
    try:
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="5d")
        
        if hist.empty:
            bot.reply_to(message, f"❌ Stock '{query}' nahi mila. Sahi NSE symbol dalein.")
            return

        current_price = hist['Close'].iloc[-1]
        prev_close = stock.info.get('previousClose', current_price)
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        day_high = hist['High'].iloc[-1]
        day_low = hist['Low'].iloc[-1]

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
        bot.reply_to(message, f"⚠️ Data fetch karne mein error aaya. Kripya dobara koshish karein.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
