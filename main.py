import os
import telebot
import sqlite3
from datetime import datetime
from telebot import types
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Referral Bot is Running! - @Refer_kerka_kamao_bot"

API_TOKEN = os.environ.get('BOT_TOKEN', '8070973105:AAGXXG0XB_jVkxjaohefmfKYISJp-S9O5o0')
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME', 'FFHackHub')

bot = telebot.TeleBot(API_TOKEN)
CHANNEL_LINK = f'https://t.me/{CHANNEL_USERNAME}'

def init_db():
    conn = sqlite3.connect('referral.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, referral_code TEXT UNIQUE, 
                  referred_by INTEGER, points INTEGER DEFAULT 0, join_date TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER,
                  referred_id INTEGER, date TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def generate_referral_code(user_id):
    return f"REF{user_id}"

def add_user(user_id, username, referred_by=None):
    conn = sqlite3.connect('referral.db')
    c = conn.cursor()
    referral_code = generate_referral_code(user_id)
    try:
        c.execute('INSERT INTO users VALUES (?,?,?,?,?,?)',
                 (user_id, username, referral_code, referred_by, 0, datetime.now()))
        if referred_by:
            c.execute('UPDATE users SET points = points + 10 WHERE user_id = ?', (referred_by,))
            c.execute('INSERT INTO referrals VALUES (?,?,?)', (referred_by, user_id, datetime.now()))
        conn.commit()
    except:
        pass
    conn.close()
    return referral_code

def get_user_info(user_id):
    conn = sqlite3.connect('referral.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def get_referral_count(user_id):
    conn = sqlite3.connect('referral.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def check_channel_membership(user_id):
    try:
        chat_member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except:
        return False

def create_channel_button():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    keyboard.add(types.InlineKeyboardButton("✅ Check Membership", callback_data="check_membership"))
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    if not check_channel_membership(user_id):
        bot.send_message(user_id, "🚫 Please join our channel first!\n\n👉 " + CHANNEL_LINK + "\n\nAfter joining, click 'Check Membership' below.", reply_markup=create_channel_button())
        return
    
    referred_by = None
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        conn = sqlite3.connect('referral.db')
        c = conn.cursor()
        c.execute('SELECT user_id FROM users WHERE referral_code = ?', (ref_code,))
        result = c.fetchone()
        if result:
            referred_by = result[0]
        conn.close()
    
    ref_code = add_user(user_id, username, referred_by)
    
    welcome_text = f"""🎉 Welcome to Refer & Earn Bot!

🤖 Bot: @Refer_kerka_kamao_bot
📢 Channel: @{CHANNEL_USERNAME}

🎯 Your Referral Code: {ref_code}
⭐ Your Points: 0

🔗 Your Referral Link:
https://t.me/Refer_kerka_kamao_bot?start={ref_code}

💰 Earn 10 points for each friend who joins using your link!

📋 Commands:
/myinfo - Your statistics
/myreferrals - Your referrals
/redeem - Redeem points
/help - Help guide"""
    bot.send_message(user_id, welcome_text)

@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(call):
    user_id = call.from_user.id
    if check_channel_membership(user_id):
        bot.send_message(user_id, "✅ Thank you for joining!\n\nNow send /start to use the bot.")
    else:
        bot.send_message(user_id, "❌ You haven't joined yet!\n\nPlease join our channel first.", reply_markup=create_channel_button())

@bot.message_handler(commands=['myinfo'])
def myinfo_command(message):
    user_id = message.from_user.id
    user_info = get_user_info(user_id)
    if user_info:
        ref_count = get_referral_count(user_id)
        info_text = f"""📊 Your Information:

👤 User ID: {user_info[0]}
📛 Username: {user_info[1]}
🎯 Referral Code: {user_info[2]}
⭐ Points: {user_info[4]}
👥 Total Referrals: {ref_count}
📅 Join Date: {user_info[5]}"""
        bot.send_message(user_id, info_text)
    else:
        bot.send_message(user_id, "❌ Please send /start first!")

@bot.message_handler(commands=['myreferrals'])
def myreferrals_command(message):
    user_id = message.from_user.id
    ref_count = get_referral_count(user_id)
    bot.send_message(user_id, f"👥 Total Referrals: {ref_count}\n⭐ Total Points: {ref_count * 10}")

@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    user_id = message.from_user.id
    user_info = get_user_info(user_id)
    if user_info and user_info[4] >= 50:
        bot.send_message(user_id, f"🎉 You can redeem {user_info[4]} points!\n\nContact @{CHANNEL_USERNAME} for rewards.")
    else:
        bot.send_message(user_id, "❌ You need at least 50 points to redeem!")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """📖 Help Guide:

🎯 How to Earn:
1. Share your referral link with friends
2. Get 10 points for each successful referral
3. Redeem points for exciting rewards

💎 Commands:
/start - Start the bot
/myinfo - Your information
/myreferrals - Your referrals
/redeem - Redeem points
/help - This help message

📢 Note: You must join our channel to use this bot!"""
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        return
    bot.send_message(message.chat.id, "🤖 Send /help to see available commands!")

if __name__ == "__main__":
    print("✅ Bot is running successfully!")
    print(f"🤖 Bot Username: @Refer_kerka_kamao_bot")
    print(f"📢 Channel: @{CHANNEL_USERNAME}")
    bot.infinity_polling()
