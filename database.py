# database.py - PostgreSQL версия с заявками в apartments
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from dotenv import load_dotenv

from dadata import Dadata
import aiohttp
import asyncio

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
DADATA_TOKEN = os.getenv('DADATA_TOKEN')
DADATA_SECRET = os.getenv('DADATA_SECRET')

if not DATABASE_URL:
    raise Exception(
        "❌ DATABASE_URL не найден в .env! Добавьте: DATABASE_URL=postgresql://doors_user:GlDxzFUy6V@localhost/doors_db")


def get_connection():
    """Возвращает соединение с PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Проверка подключения к БД"""
    try:
        conn = get_connection()
        conn.close()
        print("✅ PostgreSQL подключена")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        raise


# ====== ПЕРЕСЧЕТ UTC НА МЕСТНОЕ ВРЕМЯ ======
def get_bookings_with_local_time(apartment_id):
    """
    Возвращает все брони квартиры с временем, приведённым к таймзоне квартиры
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Получаем таймзону квартиры
    cursor.execute("SELECT timezone FROM apartments WHERE apartment_id = %s", (apartment_id,))
    result = cursor.fetchone()

    if result and result['timezone']:
        apt_tz = pytz.timezone(result['timezone'])
    else:
        apt_tz = pytz.timezone('Europe/Moscow')

    # Получаем брони
    cursor.execute("""
        SELECT id, checkin_date, checkout_date 
        FROM bookings 
        WHERE apartment_id = %s
        ORDER BY checkin_date
    """, (apartment_id,))

    rows = cursor.fetchall()
    conn.close()

    bookings = []
    for row in rows:
        bookings.append({
            'id': row['id'],
            'checkin': row['checkin_date'].astimezone(apt_tz),
            'checkout': row['checkout_date'].astimezone(apt_tz)
        })
    return bookings, apt_tz


# ====== ПОЛЬЗОВАТЕЛИ ======
def get_user_id_by_telegram(telegram_id):
    """Получает внутренний ID пользователя по telegram_id"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        telegram_id = int(telegram_id)
    except (ValueError, TypeError):
        conn.close()
        return None

    cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cursor.fetchone()
    conn.close()

    return result['id'] if result else None


def get_user_role(telegram_id):
    """Получает роль пользователя по telegram_id"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        telegram_id = int(telegram_id)
    except (ValueError, TypeError):
        conn.close()
        return None

    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (telegram_id,))
    result = cursor.fetchone()
    conn.close()

    return result['role'] if result else None


def get_active_invites(telegram_id):
    """Получает активные приглашения для пользователя"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        telegram_id = int(telegram_id)
    except (ValueError, TypeError):
        conn.close()
        return []

    cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    user_result = cursor.fetchone()

    if not user_result:
        conn.close()
        return []

    user_id = user_result['id']

    cursor.execute("""
        SELECT * FROM invites 
        WHERE used_by = %s AND is_used = false
    """, (user_id,))

    invites = cursor.fetchall()
    conn.close()
    return invites


# ====== КВАРТИРЫ ======
def room_list(owner_id):
    """Список квартир владельца (только active)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT apartment_id, owner_id, address, rooms_count, bed_count, 
               tariff_id, timezone, city
        FROM apartments 
        WHERE owner_id = %s AND status = 'active'
    """, (owner_id,))

    rows = cursor.fetchall()
    conn.close()
    return rows


def room_search(apartment_id):
    """Найти квартиру по ID (любого статуса)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM apartments WHERE apartment_id = %s", (apartment_id,))
    apartment = cursor.fetchone()
    conn.close()

    return apartment


def doors_search1(apartment_id):
    """Алиас для room_search"""
    return room_search(apartment_id)


# ====== БРОНИРОВАНИЯ ======
def take_order(order_id):
    """Получить бронирование по ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    conn.close()

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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', order_info)

        order_id = cursor.fetchone()['id']
        conn.commit()
        print(f"✅ Бронь сохранена, ID: {order_id}")
        return order_id
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def del_order(order_id):
    """Удалить бронирование"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bookings WHERE id = %s", (order_id,))
    conn.commit()
    conn.close()
    print(f"🗑️ Бронирование {order_id} удалено")


# ====== ПРИГЛАШЕНИЯ ======
def create_invite(code, created_by, role, expires_at):
    """Создать новое приглашение"""
    conn = get_connection()
    cursor = conn.cursor()

    created_at = datetime.now()

    try:
        cursor.execute('''
            INSERT INTO invites 
            (code, created_by, role, created_at, expires_at, is_used)
            VALUES (%s, %s, %s, %s, %s, false)
            RETURNING id
        ''', (code, created_by, role, created_at, expires_at))

        invite_id = cursor.fetchone()['id']
        conn.commit()
        print(f"✅ Приглашение создано, ID: {invite_id}")
        return invite_id
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None
    finally:
        conn.close()


def check_invite(code):
    """Проверяет существование приглашения по коду"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, code, created_by, role, created_at, expires_at, 
               used_by, used_at, is_used 
        FROM invites 
        WHERE code = %s
    """, (code,))

    invite = cursor.fetchone()
    conn.close()
    return invite


def use_invite(code, user_id):
    """Активировать приглашение"""
    conn = get_connection()
    cursor = conn.cursor()

    used_at = datetime.now()

    try:
        cursor.execute('''
            UPDATE invites 
            SET used_by = %s, used_at = %s, is_used = true
            WHERE code = %s AND is_used = false
        ''', (user_id, used_at, code))

        conn.commit()
        success = cursor.rowcount > 0
        if success:
            print(f"✅ Приглашение {code} активировано")
        return success
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        conn.close()


def get_all_invites():
    """Получает список всех приглашений"""
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
    return invites


# ====== ЗАЯВКИ НА КВАРТИРЫ (через таблицу apartments) ======

def create_apartment_request(owner_id, address, city, street, building, apartment,
                             timezone, wifi_ssid, wifi_password,  # 👈 убрали rooms, beds
                             latitude=None, longitude=None):
    """
    Создаёт новую заявку на квартиру (статус pending)
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO apartments (
                        owner_id, address, city, street, building, apartment,
                        timezone, wifi_ssid, wifi_password,
                        latitude, longitude, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
            RETURNING apartment_id
        """, (owner_id, address, city, street, building, apartment,
              timezone, wifi_ssid, wifi_password,
              latitude, longitude))

        apartment_id = cursor.fetchone()['apartment_id']
        conn.commit()
        print(f"✅ [create_apartment_request] Заявка создана, ID: {apartment_id}")
        return apartment_id
    except Exception as e:
        print(f"❌ [create_apartment_request] Ошибка: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_pending_requests_for_admin(admin_id, role):
    """
    Возвращает все заявки со статусом pending
    Для ADMIN — только от его OWNER
    Для ROOT — все заявки
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if role == 'root':
            # ROOT видит все заявки
            cursor.execute("""
                SELECT 
                    a.apartment_id, 
                    a.owner_id, 
                    a.address, 
                    a.city, 
                    a.timezone,
                    a.wifi_ssid, 
                    a.status, 
                    a.created_at,
                    u.first_name as owner_name,
                    u.telegram_id as owner_tg
                FROM apartments a
                JOIN users u ON a.owner_id = u.id
                WHERE a.status = 'pending'
                ORDER BY a.created_at DESC;
            """)
        else:
            # ADMIN видит только заявки от своих OWNER
            cursor.execute("""
                SELECT 
                    a.apartment_id, 
                    a.owner_id, 
                    a.address, 
                    a.city, 
                    a.timezone,
                    a.wifi_ssid, 
                    a.status, 
                    a.created_at,
                    u.first_name as owner_name,
                    u.telegram_id as owner_tg
                FROM apartments a
                JOIN users u ON a.owner_id = u.id
                WHERE a.status = 'pending'
                AND u.created_by = %s
                ORDER BY a.created_at DESC;
            """, (admin_id,))

        requests = cursor.fetchall()
        print(f"📋 [get_pending_requests] Найдено заявок: {len(requests)}")
        return requests
    except Exception as e:
        print(f"❌ [get_pending_requests] Ошибка: {e}")
        return []
    finally:
        conn.close()


def get_my_requests(user_id):
    """
    Возвращает заявки текущего пользователя (любого статуса)
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                apartment_id,
                owner_id,
                address,
                city,
                timezone,
                wifi_ssid,
                status,
                created_at,
                registered_at
            FROM apartments
            WHERE owner_id = %s
            ORDER BY created_at DESC;
        """, (user_id,))

        requests = cursor.fetchall()
        print(f"📋 [get_my_requests] Найдено заявок: {len(requests)}")
        return requests
    except Exception as e:
        print(f"❌ [get_my_requests] Ошибка: {e}")
        return []
    finally:
        conn.close()


def approve_request(apartment_id, admin_id):
    """
    Подтверждение заявки (меняем статус на active)
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE apartments
            SET status = 'active', 
                registered_by = %s, 
                registered_at = NOW()
            WHERE apartment_id = %s AND status = 'pending'
            RETURNING apartment_id
        """, (admin_id, apartment_id))

        result = cursor.fetchone()
        conn.commit()

        if result:
            print(f"✅ [approve_request] Заявка {apartment_id} подтверждена")
            return True
        else:
            print(f"⚠️ [approve_request] Заявка {apartment_id} не найдена или уже обработана")
            return False
    except Exception as e:
        print(f"❌ [approve_request] Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def reject_request(apartment_id, admin_id, canceled_by_user=False):
    """
    Отклонение заявки (админом или отмена пользователем)
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        status = 'rejected' if not canceled_by_user else 'canceled'

        cursor.execute("""
            UPDATE apartments
            SET status = %s,
                registered_by = %s,
                registered_at = NOW()
            WHERE apartment_id = %s AND status = 'pending'
        """, (status, admin_id, apartment_id))

        conn.commit()
        affected = cursor.rowcount
        if affected > 0:
            print(f"✅ [reject_request] Заявка {apartment_id} отклонена (статус: {status})")
            return True
        else:
            print(f"⚠️ [reject_request] Заявка {apartment_id} не найдена или уже обработана")
            return False
    except Exception as e:
        print(f"❌ [reject_request] Ошибка: {e}")
        return False
    finally:
        conn.close()


# ====== ГЕОКОДИНГ (DaData) ======
def geocode_address(address):
    """
    Геокодирование адреса через DaData
    Возвращает словарь с данными адреса
    """
    if not DADATA_TOKEN or not DADATA_SECRET:
        print("⚠️ DaData ключи не найдены, используется заглушка")
        return fallback_geocode(address)

    try:
        # Используем синхронный клиент Dadata
        with Dadata(DADATA_TOKEN, DADATA_SECRET) as dadata:
            result = dadata.clean("address", address)

            if not result:
                print(f"⚠️ DaData не вернул результат для: {address}")
                return fallback_geocode(address)

            # Определяем часовой пояс по координатам (если есть)
            timezone = 'Europe/Moscow'  # по умолчанию
            if result.get('geo_lat') and result.get('geo_lon'):
                timezone = get_timezone_by_coords(result['geo_lat'], result['geo_lon'])

            # Формируем нормализованный адрес
            normalized = result.get('result', address)

            # Собираем все данные
            geo_data = {
                # Основные поля
                'normalized': normalized,
                'city': result.get('city') or result.get('settlement') or result.get('region'),
                'street': result.get('street'),
                'building': result.get('house'),
                'apartment': result.get('flat'),
                'postal_code': result.get('postal_code'),
                'timezone': timezone,
                'lat': result.get('geo_lat'),
                'lon': result.get('geo_lon'),

                # Дополнительные поля для будущего использования
                'region': result.get('region'),
                'area': result.get('area'),  # район области
                'city_district': result.get('city_district'),  # район города
                'street_type': result.get('street_type'),
                'house_type': result.get('house_type'),
                'flat_type': result.get('flat_type'),
                'flat_area': result.get('flat_area'),  # площадь квартиры
                'flat_price': result.get('flat_price'),  # кадастровая стоимость

                # Коды КЛАДР и ФИАС
                'region_kladr_id': result.get('region_kladr_id'),
                'region_fias_id': result.get('region_fias_id'),
                'city_kladr_id': result.get('city_kladr_id'),
                'city_fias_id': result.get('city_fias_id'),
                'street_kladr_id': result.get('street_kladr_id'),
                'street_fias_id': result.get('street_fias_id'),
                'house_kladr_id': result.get('house_kladr_id'),
                'house_fias_id': result.get('house_fias_id'),
                'fias_id': result.get('fias_id'),
                'fias_level': result.get('fias_level'),
                'kladr_id': result.get('kladr_id'),

                # Кадастровые номера
                'house_cadnum': result.get('house_cadnum'),
                'flat_cadnum': result.get('flat_cadnum'),
                'stead_cadnum': result.get('stead_cadnum'),

                # Дополнительная информация
                'okato': result.get('okato'),
                'oktmo': result.get('oktmo'),
                'tax_office': result.get('tax_office'),
                'qc': result.get('qc'),  # код качества
                'qc_geo': result.get('qc_geo'),  # код точности координат
            }

            print(f"✅ DaData: {normalized}")
            return geo_data

    except Exception as e:
        print(f"❌ Ошибка DaData: {e}")
        return fallback_geocode(address)


def fallback_geocode(address):
    """
    Заглушка на случай ошибки DaData
    """
    return {
        'normalized': address,
        'city': 'Владивосток',
        'street': 'Светланская',
        'building': '20',
        'apartment': '5',
        'postal_code': '690000',
        'timezone': 'Asia/Vladivostok',
        'lat': 43.116,
        'lon': 131.882,
        'region_kladr_id': None,
        'fias_id': None,
        'house_cadnum': None,
        'flat_cadnum': None
    }


def get_timezone_by_coords(lat, lon):
    """
    Определяет часовой пояс по координатам с приоритетом точных библиотек
    """
    try:
        # Пытаемся использовать timezonefinder для точного определения
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()

        # Преобразуем строки в числа с плавающей точкой
        lat_float = float(lat) if lat is not None else None
        lon_float = float(lon) if lon is not None else None

        if lat_float is not None and lon_float is not None:
            # Пробуем найти точный часовой пояс по координатам
            tz = tf.timezone_at(lat=lat_float, lng=lon_float)
            if tz:
                print(f"✅ Точный часовой пояс: {tz}")
                return tz
    except (ImportError, ValueError, TypeError) as e:
        print(f"⚠️ TimezoneFinder не доступен, используем приблизительный метод: {e}")

    # Fallback: определяем по долготе, если точный метод не сработал
    try:
        lon_float = float(lon) if lon is not None else None
        if lon_float is not None:
            # Основные пояса России по долготе
            if 30 < lon_float < 45:
                return 'Europe/Moscow'  # Москва, СПб (UTC+3)
            elif 45 < lon_float < 60:
                return 'Europe/Samara'  # Самара, Уфа (UTC+4)
            elif 60 < lon_float < 75:
                return 'Asia/Yekaterinburg'  # Екатеринбург, Тюмень (UTC+5)
            elif 75 < lon_float < 82:
                return 'Asia/Omsk'  # Омск (UTC+6)
            elif 82 < lon_float < 95:
                return 'Asia/Krasnoyarsk'  # Красноярск, Кемерово (UTC+7)  👈 ЭТО НАШ СЛУЧАЙ!
            elif 95 < lon_float < 115:
                return 'Asia/Irkutsk'  # Иркутск, Улан-Удэ (UTC+8)
            elif 115 < lon_float < 125:
                return 'Asia/Yakutsk'  # Якутск (UTC+9)
            elif 125 < lon_float < 140:
                return 'Asia/Vladivostok'  # Владивосток, Хабаровск (UTC+10)
            elif 140 < lon_float < 160:
                return 'Asia/Magadan'  # Магадан (UTC+11)
            elif 160 < lon_float < 180:
                return 'Asia/Kamchatka'  # Камчатка (UTC+12)
    except (ValueError, TypeError):
        pass

    return 'Europe/Moscow'  # По умолчанию


# Асинхронная версия (если понадобится)
async def geocode_address_async(address):
    """
    Асинхронная версия геокодинга через aiohttp
    """
    if not DADATA_TOKEN or not DADATA_SECRET:
        return fallback_geocode(address)

    try:
        async with aiohttp.ClientSession() as session:
            url = "https://cleaner.dadata.ru/api/v1/clean/address"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {DADATA_TOKEN}",
                "X-Secret": DADATA_SECRET
            }

            async with session.post(url, json=[address], headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and len(data) > 0:
                        result = data[0]

                        timezone = 'Europe/Moscow'
                        if result.get('geo_lat') and result.get('geo_lon'):
                            timezone = get_timezone_by_coords(result['geo_lat'], result['geo_lon'])

                        normalized = result.get('result', address)

                        return {
                            'normalized': normalized,
                            'city': result.get('city') or result.get('settlement') or result.get('region'),
                            'street': result.get('street'),
                            'building': result.get('house'),
                            'apartment': result.get('flat'),
                            'postal_code': result.get('postal_code'),
                            'timezone': timezone,
                            'lat': result.get('geo_lat'),
                            'lon': result.get('geo_lon'),
                            'region_kladr_id': result.get('region_kladr_id'),
                            'city_kladr_id': result.get('city_kladr_id'),
                            'street_kladr_id': result.get('street_kladr_id'),
                            'house_kladr_id': result.get('house_kladr_id'),
                            'fias_id': result.get('fias_id'),
                            'kladr_id': result.get('kladr_id'),
                            'house_cadnum': result.get('house_cadnum'),
                            'flat_cadnum': result.get('flat_cadnum'),
                        }
    except Exception as e:
        print(f"❌ Ошибка асинхронного DaData: {e}")
    print(f"DEBUG: lat type = {type(result.get('geo_lat'))}, value = {result.get('geo_lat')}")
    return fallback_geocode(address)