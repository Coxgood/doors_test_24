# test_api.py
from fastapi import FastAPI, HTTPException
import sqlite3
import uvicorn
from datetime import datetime
import asyncio
from aiogram import Bot
import config

# Импортируем из database
from database import check_bind_token

app = FastAPI()

DB_PATH = 'doors_ctrl_test_new.db'
bot = Bot(token=config.BOT_TOKEN)


# ===== ФУНКЦИЯ ДЛЯ ОТПРАВКИ УВЕДОМЛЕНИЙ =====
async def notify_owner(owner_telegram_id: int, door_address: str, qr_code: str):
    """Отправляет уведомление OWNER через Telegram бота"""
    try:
        print(f"📨 Уведомление для {owner_telegram_id}:")
        print(f"   🏠 {door_address}")
        print(f"   📱 {qr_code}")
        print(f"   ⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}")

        # Реальная отправка через бота
        await bot.send_message(
            owner_telegram_id,
            f"🔔 <b>QR-код активирован!</b>\n\n"
            f"🏠 {door_address}\n"
            f"📱 Код: <code>{qr_code}</code>\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML"
        )
        return True
    except Exception as e:
        print(f"❌ Ошибка уведомления: {e}")
        return False


# ===== ОСНОВНОЙ ЭНДПОИНТ ПРОВЕРКИ QR =====
@app.get("/api/check_qr")
async def check_qr(qr: str):
    print(f"\n{'='*50}")
    print(f"📡 [{datetime.now().strftime('%H:%M:%S')}] ЗАПРОС QR")
    print(f"🔍 QR код: {qr}")
    print(f"{'='*50}")

    db = None
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()

        # Ищем активную бронь с таким QR
        cursor.execute('''
            SELECT 
                b.id, 
                b.door_id, 
                d.owner_id, 
                d.address,
                b.checkin_date,
                b.checkout_date
            FROM bookings b
            JOIN doors d ON b.door_id = d.door_id
            WHERE b.qr_code = ? AND b.status = 'active'
        ''', (qr,))

        booking = cursor.fetchone()

        if not booking:
            print("❌ QR не найден в БД")

            # Логируем неудачную попытку
            cursor.execute('''
                INSERT INTO scan_logs (qr_code, door_id, success)
                VALUES (?, NULL, 0)
            ''', (qr,))
            db.commit()

            return {"status": "deny", "reason": "QR not found"}

        booking_id, door_id, owner_id, address, checkin, checkout = booking

        print(f"✅ QR найден!")
        print(f"   🆔 Бронь: {booking_id}")
        print(f"   🏠 Адрес: {address}")
        print(f"   👤 OWNER ID: {owner_id}")

        # Проверяем, активна ли бронь по датам
        now = datetime.now()
        checkin_date = datetime.strptime(checkin, "%Y-%m-%d %H:%M")
        checkout_date = datetime.strptime(checkout, "%Y-%m-%d %H:%M")

        if checkin_date <= now <= checkout_date:
            print(f"✅ Бронь активна в текущий момент")

            # Получаем telegram_id OWNER
            cursor.execute('''
                SELECT telegram_id FROM users WHERE id = ?
            ''', (owner_id,))
            owner = cursor.fetchone()

            if owner:
                owner_tg = owner[0]
                print(f"📨 Отправка уведомления OWNER {owner_tg}")

                # Отправляем уведомление (асинхронно)
                asyncio.create_task(notify_owner(owner_tg, address, qr))
            else:
                print(f"⚠️ OWNER {owner_id} не найден в users")

            success = True
        else:
            print(f"⚠️ Бронь не активна по датам")
            print(f"   📅 Заезд: {checkin}")
            print(f"   📅 Выезд: {checkout}")
            print(f"   🕐 Сейчас: {now}")
            success = False

        # Логируем результат
        cursor.execute('''
            INSERT INTO scan_logs (qr_code, door_id, success)
            VALUES (?, ?, ?)
        ''', (qr, door_id, 1 if success else 0))

        db.commit()

        if success:
            return {
                "status": "open",
                "message": "Доступ разрешён",
                "booking_id": booking_id,
                "door_id": door_id,
                "address": address
            }
        else:
            return {
                "status": "deny",
                "reason": "booking not active",
                "booking_period": f"{checkin} - {checkout}"
            }

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        if db:
            db.close()
        print(f"{'='*50}\n")


# ===== ЭНДПОИНТ ДЛЯ НАЖАТИЯ КНОПКИ НА ESP32 =====
@app.get("/api/button_press")
async def button_press(token: str):
    """ESP32 сообщает о нажатии кнопки"""
    print(f"\n{'='*50}")
    print(f"🔘 [{datetime.now().strftime('%H:%M:%S')}] НАЖАТИЕ КНОПКИ")
    print(f"🔑 Токен: {token}")
    print(f"{'='*50}")

    # Проверяем токен
    owner_id = check_bind_token(token)

    if owner_id:
        print(f"✅ Токен действителен для OWNER {owner_id}")

        # Отправляем уведомление в Telegram
        try:
            await bot.send_message(
                owner_id,
                f"🔔 <b>Уведомление с ESP32</b>\n\n"
                f"🚪 Кнопка на замке была нажата!\n"
                f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                parse_mode="HTML"
            )
            print("📨 Уведомление отправлено")
            return {"status": "ok", "message": "Notification sent"}
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            raise HTTPException(status_code=500, detail="Failed to send message")

    print("❌ Недействительный токен")
    raise HTTPException(status_code=403, detail="Invalid token")


# ===== ТЕСТОВЫЙ ЭНДПОИНТ =====
@app.get("/")
async def root():
    return {
        "message": "✅ QR API работает!",
        "status": "online",
        "time": str(datetime.now())
    }


# ===== ЗАПУСК =====
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 ЗАПУСК QR API СЕРВЕРА")
    print("="*60)
    print(f"📂 База данных: {DB_PATH}")
    print("🌐 Адрес: http://192.168.1.102:8000")
    print("📡 Эндпоинты:")
    print("   • /api/check_qr?qr=ВАШ_QR")
    print("   • /api/button_press?token=ТОКЕН")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)