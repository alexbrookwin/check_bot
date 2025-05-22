import logging
import datetime
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CallbackQueryHandler,
    CommandHandler, ContextTypes
)

# Токен и настройки
TOKEN = "7827265617:AAEQvEsQE-v9gU0IpZZo7eUnUzjeqwawRM0"
ADMIN_USERNAME = "alice_alekseeevna"
STAFF = [
    {
        "username": "alice_alekseeevna",
        "chat_id": None,
        "point": "Тестовая точка",
        "open_time": "16:00"
    }
]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    for staff in STAFF:
        if staff["username"] == user.username:
            staff["chat_id"] = user.id
            await update.message.reply_text("Ты зарегистрирован как сотрудник. Жди уведомления утром.")
            return
    await update.message.reply_text("Ты не в списке сотрудников.")

# Кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    status, username, point = query.data.split("|")
    symbol = "✅" if status == "yes" else "❌"
    message = f"@{username} ({point}) — выходит {symbol}"

    for staff in STAFF:
        if staff["username"] == ADMIN_USERNAME and staff["chat_id"]:
            await context.bot.send_message(chat_id=staff["chat_id"], text=message)

# Рассылка
async def send_daily_notifications(app):
    while True:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        logging.info(f"Проверка времени: {current_time}")

        for staff in STAFF:
            # Если текущее время 13:35, и сотрудник должен выйти в 14:00
            if staff["chat_id"] and staff["open_time"] == "16:00" and current_time == "15:40":
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Да", callback_data=f"yes|{staff['username']}|{staff['point']}"),
                        InlineKeyboardButton("❌ Нет", callback_data=f"no|{staff['username']}|{staff['point']}")
                    ]
                ])
                try:
                    await app.bot.send_message(
                        chat_id=staff["chat_id"],
                        text="Выходишь сегодня на смену?",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logging.error(f"Ошибка при отправке: {e}")

        await asyncio.sleep(60)  # Проверяем каждую минуту

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Удаляем старые вебхуки, если есть
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Запускаем таск с рассылкой уведомлений
    asyncio.create_task(send_daily_notifications(app))

    logging.info("Бот запускается...")

    # Запускаем бота в режиме polling (долгого опроса)
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
