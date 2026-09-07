import os
import telebot
from flask import Flask, request

TOKEN = '8846968829:AAHlJyEqdPsTyUtPP9dL5J4uHnkQYXKLNfo'
API_URL = 'https://late-pine-2f2c.ktabrez92.workers.dev'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Stock Bot is live and connected to Cloudflare API!"

@app.message_handler(func=lambda message: True)
def handle_stock_query(message):
    text = message.text.strip().upper()
    bot.reply_to(message, f"📈 Fetching live NSE/BSE data for *{text}* via Cloudflare API...", parse_mode='Markdown')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
  
