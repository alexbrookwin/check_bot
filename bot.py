import logging
import datetime
import asyncio
from zoneinfo import ZoneInfo  # для работы с часовыми поясами
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
        "open_time": "16:00"  # Время открытия по Кургану
    }
]

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# /start команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    for staff in STAFF:
        if staff["username"] == user.username:
            staff["chat_id"] = user.id
            await update.message.reply_text("Ты зарегистрирован как сотрудник. Жди уведомления утром.")
            return
    await update.message.reply_text("Ты не в списке сотрудников.")

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    status, username, point = query.data.split("|")
    symbol = "✅" if status == "yes" else "❌"
    message = f"@{username} ({point}) — выходит {symbol}"

    for staff in STAFF:
        if staff["username"] == ADMIN_USERNAME and staff["chat_id"]:
            await context.bot.send_message(chat_id=staff["chat_id"], text=message)

# Рассылка уведомлений
async def send_daily_notifications(application):
    while True:
        now = datetime.datetime.now(ZoneInfo("Asia/Yekaterinburg"))
        current_time = now.strftime("%H:%M")
        logging.info(f"Проверка времени: {current_time}")

        for staff in STAFF:
            if staff["chat_id"]:
                open_time = datetime.datetime.strptime(staff["open_time"], "%H:%M")
                notify_time = (open_time - datetime.timedelta(minutes=30)).time().strftime("%H:%M")

                if current_time == notify_time:
                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✅ Да", callback_data=f"yes|{staff['username']}|{staff['point']}"),
                            InlineKeyboardButton("❌ Нет", callback_data=f"no|{staff['username']}|{staff['point']}")
                        ]
                    ])
                    try:
                        await application.bot.send_message(
                            chat_id=staff["chat_id"],
                            text="Выходишь сегодня на смену?",
                            reply_markup=keyboard
                        )
                    except Exception as e:
                        logging.error(f"Ошибка при отправке уведомления: {e}")

        await asyncio.sleep(60)

# Запуск бота
async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Убираем вебхук и запускаем long polling
    await application.bot.delete_webhook(drop_pending_updates=True)

    # Запускаем задачу отправки уведомлений
    asyncio.create_task(send_daily_notifications(application))

    logging.info("Бот запускается...")
    await application.run_polling()

# Старт
if __name__ == "__main__":
    asyncio.run(main())
