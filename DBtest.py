# check_my_access.py
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://doors_user:GlDxzFUy6V@localhost/doors_db"
MY_TELEGRAM_ID = 506169873

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    # Проверяем, что функция get_user_role возвращает
    cursor.execute("""
        SELECT role FROM users WHERE telegram_id = %s;
    """, (MY_TELEGRAM_ID,))

    result = cursor.fetchone()
    print(f"Роль в БД: {result['role'] if result else 'None'}")

    # Проверяем функцию get_user_id_by_telegram
    cursor.execute("""
        SELECT id FROM users WHERE telegram_id = %s;
    """, (MY_TELEGRAM_ID,))

    result = cursor.fetchone()
    print(f"ID в БД: {result['id'] if result else 'None'}")

    conn.close()

except Exception as e:
    print(f"❌ Ошибка: {e}")