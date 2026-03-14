import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://doors_user:GlDxzFUy6V@localhost/doors_db"

try:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()

    print("=" * 60)
    print("🔍 СТРУКТУРА ТАБЛИЦЫ devices")
    print("=" * 60)

    # Получаем структуру таблицы
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'devices' 
        ORDER BY ordinal_position;
    """)

    columns = cursor.fetchall()

    if not columns:
        print("❌ Таблица 'devices' не существует!")
    else:
        print(f"\n📊 Найдено полей: {len(columns)}\n")

        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  • {col['column_name']}: {col['data_type']} {nullable}{default}")

        # Проверяем наличие apartment_id
        has_apartment = any(col['column_name'] == 'apartment_id' for col in columns)
        print(f"\n🔑 Поле apartment_id: {'✅ ЕСТЬ' if has_apartment else '❌ НЕТ'}")

    # Покажем несколько записей (если есть)
    cursor.execute("SELECT COUNT(*) FROM devices;")
    count = cursor.fetchone()['count']
    print(f"\n📈 Всего записей в devices: {count}")

    if count > 0:
        cursor.execute("""
            SELECT device_id, esp32_id, apartment_id, last_seen, is_active 
            FROM devices 
            LIMIT 5;
        """)
        records = cursor.fetchall()
        print("\n🔍 Пример записей:")
        for rec in records:
            print(f"  • device_id: {rec['device_id']}, esp32_id: {rec['esp32_id']}, "
                  f"apartment_id: {rec['apartment_id']}, last_seen: {rec['last_seen']}")

    conn.close()

except Exception as e:
    print(f"❌ Ошибка: {e}")