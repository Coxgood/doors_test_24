import sqlite3

DB_PATH = 'doors_ctrl_test_new.db'


def show_structure():
    try:
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()

        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()

        print("=" * 60)
        print(f"📁 БАЗА ДАННЫХ: {DB_PATH}")
        print("=" * 60)

        for table in tables:
            table_name = table[0]
            print(f"\n📋 ТАБЛИЦА: {table_name}")
            print("-" * 40)

            # Получаем структуру таблицы
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                pk_mark = "🔑" if is_pk else "  "
                null_mark = "NOT NULL" if not_null else "NULL"
                default = f" DEFAULT {default_val}" if default_val else ""
                print(f"  {pk_mark} {col_name:20} {col_type:10} {null_mark}{default}")

        # Получаем внешние ключи
        print("\n" + "=" * 60)
        print("🔗 ВНЕШНИЕ КЛЮЧИ")
        print("=" * 60)

        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = cursor.fetchall()
            if fks:
                print(f"\n📋 {table_name}:")
                for fk in fks:
                    print(f"  {fk[3]} → {fk[2]}({fk[4]})")

        db.close()

        print("\n" + "=" * 60)
        print("✅ ГОТОВО")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    show_structure()