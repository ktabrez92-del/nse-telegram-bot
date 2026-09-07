import os
from flask import Flask, request
import telebot

TOKEN = "8744426734:AAFR62qx-AikwDnTUGtj-F9tID_VA7Bq39A"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running successfully!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Namaste! Main aapka naya Stock Analysis Bot hoon. Koi bhi stock ka naam bhejiye.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    stock_name = message.text.upper()
    bot.reply_to(message, f"Aapne {stock_name} search kiya hai. Iski details jald hi yahan aayengi!")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
  
