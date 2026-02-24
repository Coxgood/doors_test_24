# handlers/test_qr.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import config
from database import get_connection
from datetime import datetime

router = Router()


# Таблица для логов (создать, если нет)
def init_logs_table():
    db = get_connection()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT,
            door_id INTEGER,
            success BOOLEAN,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()
    db.close()


# Команда для тестирования
@router.message(Command("test_qr"))
async def test_qr(message: Message):
    await message.answer(
        "📸 <b>ТЕСТОВЫЙ РЕЖИМ QR</b>\n\n"
        "🔹 ESP32 в тестовом режиме отправляет QR каждые 10 секунд\n"
        "🔹 OWNER получит уведомление при сканировании\n"
        "🔹 Смотрите консоль ESP32 и логи бота\n\n"
        "📊 <b>Последние сканирования:</b>",
        parse_mode="HTML"
    )

    # Показать последние 5 записей из лога
    db = get_connection()
    cursor = db.cursor()
    cursor.execute('''
        SELECT qr_code, success, scanned_at FROM scan_logs 
        ORDER BY scanned_at DESC LIMIT 5
    ''')
    logs = cursor.fetchall()
    db.close()

    if logs:
        text = ""
        for log in logs:
            emoji = "✅" if log[1] else "❌"
            text += f"{emoji} {log[0]} — {log[2]}\n"
        await message.answer(text)
    else:
        await message.answer("❌ Пока нет сканирований")


# Уведомление OWNER при сканировании (вызывается из API)
async def notify_owner(owner_telegram_id: int, door_address: str, qr_code: str):
    from aiogram import Bot
    bot = Bot(token=config.BOT_TOKEN)

    await bot.send_message(
        owner_telegram_id,
        f"🔔 <b>QR-код активирован!</b>\n\n"
        f"🏠 <b>{door_address}</b>\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"📱 Код: <code>{qr_code}</code>",
        parse_mode="HTML"
    )