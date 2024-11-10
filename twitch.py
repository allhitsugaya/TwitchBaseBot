
import sqlite3
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
from telegram.error import BadRequest

#Конфигурация
BOT_TOKEN = 'YOUR_TOKEN'
TARGET_USER_ID = YOUR_ID
CHANNEL_USERNAME = 'your_channelname'

conn = sqlite3.connect('messages.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        message_type TEXT,
        file_id TEXT,
        caption TEXT
    )
''')
conn.commit()

def start(update: Update, context: CallbackContext):
    """Отправляет приветственное сообщение при команде /start."""
    welcome_message = (
        "🎉 Привіт! Я 🤖 бот для Twitch каналу - difu3en! 🕹️\n\n"
        "Надішліть мені своє повідомлення або медіа, і я передам його далі! 📩\n\n"
        "Розробник: @all_hitsugaya 👨‍💻"
    )
    update.message.reply_text(welcome_message)

def check_subscription(user_id):
    """Проверяет, подписан ли пользователь на указанный канал."""
    try:
        member = updater.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'creator', 'administrator']:
            return True
        else:
            return False
    except BadRequest:
        #Если бот не имеет доступа к каналу или пользователя нет
        return False

def store_message(update: Update, context: CallbackContext):
    message = update.message
    user = message.from_user

    #Проверяем подписку пользователя
    if not check_subscription(user.id):
        message.reply_text(
            "❌ Щоб використовувати цього бота, будь ласка, підпишіться на наш канал: "
            f"{CHANNEL_USERNAME}"
        )
        return

    message_type = None
    file_id = None

    #Определяем тип сообщения и получаем file_id
    if message.photo:
        message_type = 'photo'
        file_id = message.photo[-1].file_id  # Берем фото в наибольшем разрешении
    elif message.video:
        message_type = 'video'
        file_id = message.video.file_id
    elif message.text:
        message_type = 'text'
        file_id = None
    else:
        return  #Не поддерживаемый тип сообщения

    #Сохраняем сообщение в базе данных
    cursor.execute('''
        INSERT INTO messages (user_id, username, message_type, file_id, caption)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        user.id,
        user.username or user.full_name,
        message_type,
        file_id,
        message.caption or message.text or ''
    ))
    conn.commit()

    #Пересылаем сообщение Диме
    forward_message(update, context, user)

def forward_message(update: Update, context: CallbackContext, sender_user):
    message = update.message
    sender_info = f"📨 Від @{sender_user.username}" if sender_user.username else f"📨 Від {sender_user.full_name}"

    if message.photo:
        context.bot.send_photo(
            chat_id=TARGET_USER_ID,
            photo=message.photo[-1].file_id,
            caption=f"{sender_info}\n{message.caption or ''}"
        )
    elif message.video:
        context.bot.send_video(
            chat_id=TARGET_USER_ID,
            video=message.video.file_id,
            caption=f"{sender_info}\n{message.caption or ''}"
        )
    elif message.text:
        context.bot.send_message(
            chat_id=TARGET_USER_ID,
            text=f"{sender_info}\n{message.text}"
        )

def main():
    global updater
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.video, store_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
