import sqlite3
from datetime import datetime

DB_PATH = 'doors_ctrl_test_new.db'


def check_last_booking():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    # Берём последнюю бронь
    cursor.execute('''
        SELECT id, door_id, qr_code, checkin_date, checkout_date, status, created_at 
        FROM bookings 
        ORDER BY id DESC 
        LIMIT 1
    ''')

    booking = cursor.fetchone()

    if booking:
        print("\n" + "=" * 60)
        print("📋 ПОСЛЕДНЯЯ БРОНЬ В БД")
        print("=" * 60)
        print(f"ID:           {booking[0]}")
        print(f"Дверь ID:     {booking[1]}")
        print(f"QR-код:       {booking[2]}")
        print(f"Заезд:        {booking[3]}")
        print(f"Выезд:        {booking[4]}")
        print(f"Статус:       {booking[5]}")
        print(f"Создано:      {booking[6]}")
        print("=" * 60)

        # Проверим, активна ли бронь сейчас
        now = datetime.now()
        checkin = datetime.strptime(booking[3], "%Y-%m-%d %H:%M")
        checkout = datetime.strptime(booking[4], "%Y-%m-%d %H:%M")

        if checkin <= now <= checkout:
            print("✅ Бронь активна в данный момент!")
        else:
            print("⏰ Бронь не активна (не в периоде)")

    else:
        print("❌ В БД нет броней!")

    db.close()


if __name__ == '__main__':
    check_last_booking()