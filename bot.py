elif command == "remove_ad":
        try:
            channel = context.args[1]
            cursor.execute("DELETE FROM ads WHERE channel=?", (channel,))
            conn.commit()
            update.message.reply_text(f"✅ کانال {channel} حذف شد!")
        except:
            update.message.reply_text("🚨 خطا! شاید این کانال در لیست نباشد.")

# بخش برداشت
def withdraw(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # بررسی عضویت
    is_member, channel = is_user_member(user_id)
    if not is_member:
        update.message.reply_text(f"🚨 لطفاً ابتدا در کانال {channel} عضو شوید.")
        return

    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        update.message.reply_text("🚨 شما در سیستم ثبت نشده‌اید!")
        return

    balance = user[0]

    if balance < MIN_WITHDRAW:
        update.message.reply_text(f"🚨 حداقل مقدار برداشت {MIN_WITHDRAW}$ است!")
        return

    update.message.reply_text("🔄 در حال پردازش برداشت...")

    # صفر کردن موجودی
    cursor.execute("UPDATE users SET balance = 0 WHERE user_id=?", (user_id,))
    conn.commit()

    update.message.reply_text("❌ سیستم پاسخ نمی‌دهد! لطفاً بعداً دوباره امتحان کنید.")

# دلار روزانه
def daily_dollar(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    cursor.execute("SELECT last_daily_claim FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        update.message.reply_text("🚨 شما در سیستم ثبت نشده‌اید!")
        return

    last_claim = user[0]
    current_day = random.randint(1, 365)  # شبیه‌سازی روزهای مختلف

    if last_claim == current_day:
        update.message.reply_text("⚠ شما امروز قبلاً دلار روزانه دریافت کرده‌اید!")
        return

    cursor.execute("UPDATE users SET balance = balance + ?, last_daily_claim = ? WHERE user_id=?", 
                   (DAILY_DOLLAR, current_day, user_id))
    conn.commit()

    update.message.reply_text(f"✅ {DAILY_DOLLAR}$ به حساب شما اضافه شد!")

# تنظیم ربات
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("account", account))
dispatcher.add_handler(CommandHandler("withdraw", withdraw))
dispatcher
import logging
import sqlite3
import random
import requests
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# تنظیمات اولیه
TOKEN = "YOUR_BOT_API_TOKEN"
ADMIN_ID = 123456789  # آیدی عددی شما
MIN_WITHDRAW = 10.0  # حداقل برداشت
MAX_WITHDRAW = 100.0  # حداکثر برداشت
DAILY_DOLLAR = 1.0  # مقدار دلار روزانه
CHANNELS = ["@channel1", "@channel2"]  # کانال‌های تبلیغاتی

bot = Bot(token=TOKEN)

# تنظیم دیتابیس
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0.0,
    referral_code TEXT UNIQUE,
    referred_by INTEGER DEFAULT NULL,
    last_daily_claim INTEGER DEFAULT 0
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT UNIQUE
)''')

conn.commit()

# بررسی عضویت در کانال‌ها
def is_user_member(user_id):
    for channel in CHANNELS:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={channel}&user_id={user_id}"
        response = requests.get(url).json()
        if response.get("ok") and response["result"]["status"] in ["member", "administrator", "creator"]:
            continue
        else:
            return False, channel
    return True, None

# ثبت‌نام کاربران جدید
def register_user(user_id, referrer_id=None):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        referral_code = str(random.randint(100000, 999999))
        cursor.execute("INSERT INTO users (user_id, referral_code, referred_by) VALUES (?, ?, ?)", 
                       (user_id, referral_code, referrer_id))
        conn.commit()

# فرمان استارت
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    referrer_id = None

    if context.args:
        try:
            referrer_id = int(context.args[0])
        except ValueError:
            pass

    register_user(user_id, referrer_id)

    # بررسی عضویت
    is_member, channel = is_user_member(user_id)
    if not is_member:
        update.message.reply_text(f"🚨 برای استفاده از ربات، ابتدا در کانال {channel} عضو شوید.")
        return

    update.message.reply_text("🚀 به قوی‌ترین ربات کسب درآمد خوش آمدید! \nسرمایه‌گذار این پروژه ایلان ماسک است!")

# نمایش حساب کاربر
def account(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # بررسی عضویت
    is_member, channel = is_user_member(user_id)
    if not is_member:
        update.message.reply_text(f"🚨 لطفاً ابتدا در کانال {channel} عضو شوید.")
        return

    cursor.execute("SELECT balance, referral_code FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if user:
        balance, referral_code = user
        cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,))
        referrals = cursor.fetchone()[0]
        update.message.reply_text(f"💰 موجودی: {balance} $\n👥 زیرمجموعه‌ها: {referrals}\n🔗 کد دعوت: {referral_code}")
    else:
        update.message.reply_text("🚨 شما در سیستم ثبت نشده‌اید!")

# مدیریت تبلیغات
def admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("🚫 شما اجازه دسترسی ندارید!")
        return

    command = context.args[0] if context.args else ""

    if command == "add_ad":
        try:
            channel = context.args[1]
            cursor.execute("INSERT INTO ads (channel) VALUES (?)", (channel,))
            conn.commit()
            update.message.reply_text(f"✅ کانال {channel} به لیست تبلیغات اضافه شد!")
        except:
            update.message.reply_text("🚨 خطا! شاید این کانال قبلاً اضافه شده باشد.")
