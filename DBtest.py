import sqlite3
import os
from datetime import datetime


def backup_database():
    # Имя файла с датой
    backup_name = f"backup_doors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    print(f"💾 Создаём бэкап: {backup_name}")

    # Просто копируем файл
    os.system(f"copy test_deploy_ver1.db {backup_name}")

    print(f"✅ Бэкап создан: {backup_name}")
    print(f"📦 Размер: {os.path.getsize(backup_name)} байт")


def backup_structure_only():
    """Сохраняем только структуру (DDL)"""
    conn = sqlite3.connect('test_deploy_ver1.db')
    cursor = conn.cursor()

    structure_file = f"structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

    with open(structure_file, 'w', encoding='utf-8') as f:
        # Получаем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            # Получаем CREATE TABLE statement
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_sql = cursor.fetchone()[0]
            f.write(f"-- Таблица: {table_name}\n")
            f.write(f"{create_sql};\n\n")

    conn.close()
    print(f"📋 Структура сохранена в: {structure_file}")


if __name__ == "__main__":
    backup_database()
    backup_structure_only()

"""
def show_users_list():
    conn = sqlite3.connect('test_deploy_ver1.db')
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    print("👥 ПОЛЬЗОВАТЕЛИ")
    print("=" * 80)
    print(f"{'ID':<4} {'Telegram ID':<12} {'Имя':<15} {'Фамилия':<15} {'Роль':<10}")
    print("-" * 80)


        #SELECT id, telegram_id, first_name, last_name, role 
        #FROM users 
        #ORDER BY id

    users = cursor.fetchall()

    for user in users:
        print(f"{user[0]:<4} {user[1]:<12} {user[2]:<15} {user[3]:<15} {user[4]:<10}")

    print("=" * 80)
    print(f"Всего: {len(users)}")
    print("=" * 80)

    conn.close()


if __name__ == "__main__":
    show_users_list()
    
"""

"""
db = sqlite3.connect('doors_ctrl_test_new.db')
cursor = db.cursor()

print("📋 ПОСЛЕДНИЕ ПРИГЛАШЕНИЯ:")
cursor.execute('''
    SELECT id, code, role, created_by, created_at, expires_at, is_used, used_by 
    FROM invites 
    ORDER BY id DESC 
    LIMIT 5
''')
invites = cursor.fetchall()
for inv in invites:
    print(f"ID: {inv[0]}, роль: {inv[2]}, создал: {inv[3]}, использовано: {inv[6]}, кем: {inv[7]}")
    print(f"   код: {inv[1]}")
    print("-" * 40)

print("\n👤 ПОСЛЕДНИЕ ПОЛЬЗОВАТЕЛИ:")
cursor.execute('''
    SELECT id, telegram_id, name, role, created_at 
    FROM users 
    ORDER BY id DESC 
    LIMIT 5
''')
users = cursor.fetchall()
for u in users:
    print(f"ID: {u[0]}, TG: {u[1]}, имя: {u[2]}, роль: {u[3]}, создан: {u[4]}")

db.close()

"""