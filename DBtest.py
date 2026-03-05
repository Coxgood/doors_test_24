import psycopg2
from datetime import datetime

DATABASE_URL = "postgresql://doors_user:GlDxzFUy6V@localhost/doors_db"

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, code, role, created_by, expires_at, is_used 
        FROM invites 
        ORDER BY id DESC;
    """)

    invites = cur.fetchall()

    print("\n" + "=" * 50)
    print("🔗 ВСЕ ИНВАЙТЫ")
    print("=" * 50)

    if not invites:
        print("❌ В базе нет инвайтов")
    else:
        for inv in invites:
            status = "✅ ИСПОЛЬЗОВАН" if inv[5] else "⏳ АКТИВЕН"
            expires = inv[4].strftime("%d.%m.%Y %H:%M") if inv[4] else "нет"
            print(f"\nID: {inv[0]}")
            print(f"  Код: {inv[1]}")
            print(f"  Роль: {inv[2]}")
            print(f"  Создатель ID: {inv[3]}")
            print(f"  Истекает: {expires}")
            print(f"  Статус: {status}")

    conn.close()

except Exception as e:
    print(f"❌ Ошибка: {e}")