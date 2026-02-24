# database.py
import sqlite3
from datetime import datetime

DB_NAME = 'test_deploy_ver1.db'


def get_connection():
    """Возвращает соединение с БД"""
    return sqlite3.connect(DB_NAME)


def init_db():
    """Инициализация базы данных (если нужно создать таблицы)"""
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица уже существует, просто проверяем
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookings'")
    if cursor.fetchone():
        print("✅ База данных инициализирована")
    else:
        print("⚠️ Таблицы не найдены")

    conn.close()


# ====== ПОЛЬЗОВАТЕЛИ ======
def get_user_id_by_telegram(telegram_id):
    """
    Получает внутренний ID пользователя по его telegram_id
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Преобразуем в int
    try:
        telegram_id = int(telegram_id)
    except (ValueError, TypeError):
        print(f"❌ [get_user_id_by_telegram] Некорректный telegram_id: {telegram_id}")
        conn.close()
        return None

    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        print(f"✅ [get_user_id_by_telegram] Найден пользователь с ID: {result[0]}")
        return result[0]

    print(f"❌ [get_user_id_by_telegram] Пользователь {telegram_id} не найден")
    return None


def get_user_role(telegram_id):
    """
    Получает роль пользователя по telegram_id
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        telegram_id = int(telegram_id)
    except (ValueError, TypeError):
        conn.close()
        return None

    cursor.execute("SELECT role FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        print(f"👤 [get_user_role] Пользователь {telegram_id} имеет роль: {result[0]}")
        return result[0]

    print(f"⚠️ [get_user_role] Пользователь {telegram_id} не найден")
    return None


def get_active_invites(telegram_id):
    """
    Получает активные приглашения для пользователя
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        telegram_id = int(telegram_id)
    except (ValueError, TypeError):
        conn.close()
        return []

    # Сначала получаем внутренний ID пользователя
    cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    user_result = cursor.fetchone()

    if not user_result:
        conn.close()
        return []

    user_id = user_result[0]

    # Получаем активные приглашения
    cursor.execute("""
        SELECT * FROM invites 
        WHERE used_by = ? AND is_used = 0
    """, (user_id,))

    invites = cursor.fetchall()
    conn.close()

    print(f"📨 [get_active_invites] Для пользователя {telegram_id} найдено {len(invites)} приглашений")
    return invites


# ====== КВАРТИРЫ ======
def room_list(owner_id):
    """
    Возвращает список квартир владельца
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT apartment_id, owner_id, address, rooms_count, bed_count, tariff_id 
        FROM apartments 
        WHERE owner_id = ?
    """, (owner_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def room_search(apartment_id):
    """
    Найти квартиру по ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM apartments WHERE apartment_id = ?", (apartment_id,))
    apartment = cursor.fetchone()
    conn.close()

    if apartment:
        print(f"🔍 [room_search] Найдена квартира {apartment_id}: {apartment}")
    else:
        print(f"⚠️ [room_search] Квартира {apartment_id} не найдена")

    return apartment


def doors_search1(apartment_id):
    """Алиас для room_search"""
    return room_search(apartment_id)


# ====== БРОНИРОВАНИЯ ======
def take_order(order_id):
    """
    Получить бронирование по ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()

    if order:
        print(f"📦 [take_order] Найдено бронирование: {order}")
    else:
        print(f"⚠️ [take_order] Бронирование {order_id} не найдено")

    return order


def new_order(order_info):
    """
    Создать новое бронирование
    order_info: (booking_number, apartment_id, guest_name, guest_phone,
                 checkin_date, checkout_date, qr_code, status, created_at, access_type)
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO bookings 
            (booking_number, apartment_id, guest_name, guest_phone,
             checkin_date, checkout_date, qr_code, status, created_at, access_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', order_info)

        conn.commit()
        order_id = cursor.lastrowid
        print(f"✅ [new_order] Бронь сохранена, ID: {order_id}")
        return order_id
    except Exception as e:
        print(f"❌ [new_order] Ошибка: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def del_order(order_id):
    """
    Удалить бронирование
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bookings WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    print(f"🗑️ [del_order] Бронирование {order_id} удалено")


# ====== ПРИГЛАШЕНИЯ ======
def create_invite(code, created_by, role, expires_at):
    """
    Создать новое приглашение
    """
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute('''
            INSERT INTO invites 
            (code, created_by, role, created_at, expires_at, is_used)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (code, created_by, role, created_at, expires_at))

        conn.commit()
        invite_id = cursor.lastrowid
        print(f"✅ [create_invite] Приглашение создано, ID: {invite_id}")
        return invite_id
    except Exception as e:
        print(f"❌ [create_invite] Ошибка: {e}")
        return None
    finally:
        conn.close()


def check_invite(code):
    """
    Проверяет существование и статус приглашения по коду
    Возвращает информацию о приглашении или None
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, code, created_by, role, created_at, expires_at, used_by, used_at, is_used 
        FROM invites 
        WHERE code = ?
    """, (code,))

    invite = cursor.fetchone()
    conn.close()

    if invite:
        print(f"🔍 [check_invite] Приглашение {code} найдено")
        return invite
    else:
        print(f"⚠️ [check_invite] Приглашение {code} не найдено")
        return None


def use_invite(code, user_id):
    """
    Активировать приглашение
    """
    conn = get_connection()
    cursor = conn.cursor()

    used_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute('''
            UPDATE invites 
            SET used_by = ?, used_at = ?, is_used = 1
            WHERE code = ? AND is_used = 0
        ''', (user_id, used_at, code))

        conn.commit()

        if cursor.rowcount > 0:
            print(f"✅ [use_invite] Приглашение {code} активировано")
            return True
        else:
            print(f"⚠️ [use_invite] Приглашение {code} не найдено или уже использовано")
            return False
    except Exception as e:
        print(f"❌ [use_invite] Ошибка: {e}")
        return False
    finally:
        conn.close()


def get_all_invites():
    """
    Получает список всех приглашений
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.*, u.first_name, u.last_name 
        FROM invites i
        LEFT JOIN users u ON i.used_by = u.id
        ORDER BY i.created_at DESC
    """)

    invites = cursor.fetchall()
    conn.close()

    print(f"📋 [get_all_invites] Получено {len(invites)} приглашений")
    return invites