import os
from flask import Flask, request
import telebot
import yfinance as yf
import pytz

TOKEN = "8744426734:AAFUI8IA9p5cW9SdPeXOeJ5Zy59oT78b5xQ"
GROUP_CHAT_ID = -1003915913228

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

IST = pytz.timezone('Asia/Kolkata')

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
    bot.reply_to(message, "🟢 Bot online hai! Stock ka symbol bhejein (jaise: RELIANCE, TCS, MOIL).")

@bot.message_handler(func=lambda message: True)
def handle_stock_query(message):
    raw_query = message.text.upper().strip()
    if raw_query.startswith('/'):
        return
        
    query = raw_query.replace(" ", "")
    ticker_symbol = f"{query}.NS"
    
    try:
        # Direct download method (yfinance ka yeh tareeka zyada stable hota hai)
        df = yf.download(ticker_symbol, period="5d", progress=False)
        
        if df.empty or 'Close' not in df.columns:
            bot.reply_to(message, f"❌ Stock '{raw_query}' ka data nahi mil paya. Yahoo Finance par yeh symbol unavailable ho sakta hai.")
            return

        current_price = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        day_high = float(df['High'].iloc[-1])
        day_low = float(df['Low'].iloc[-1])

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
        bot.reply_to(message, f"⚠️ Error: {str(e)[:100]}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
