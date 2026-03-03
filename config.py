# config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Пути
BASE_DIR = Path(__file__).parent
QR_CODES_DIR = BASE_DIR / 'qr_codes'

# Создаём папку для QR, если нет
QR_CODES_DIR.mkdir(exist_ok=True)

# Названия месяцев (индексация с 1)
MONTHS = (
    '',        # 0 - пустой
    'январь',
    'февраль',
    'март',
    'апрель',
    'май',
    'июнь',
    'июль',
    'август',
    'сентябрь',
    'октябрь',
    'ноябрь',
    'декабрь'
)

# Дни недели
WEEKDAYS = (
    'понедельник',
    'вторник',
    'среда',
    'четверг',
    'пятница',
    'суббота',
    'воскресенье'
)

# Эмодзи для разных ситуаций
# Эмодзи для разных ситуаций
EMOJI = {
    'apartment': '🏠',
    'calendar': '📅',
    'time': '⏰',
    'confirm': '✅',
    'cancel': '❌',
    'delete': '🗑️',
    'qr': '🔑',
    'door': '🚪',
    'warning': '⚠️',
    'info': 'ℹ️',
    'cleaning': '🧹',
    'linen': '🛏️',
    'supplies': '🧴',
    'guest': '👤',
    'manager': '📋',
    'owner': '👑',
    'admin': '⚙️',
    'id': '🆔',  # 👈 Добавить эту строку
}

# Временные слоты для бронирования
TIME_SLOTS = [
    {'hour': 8,  'display': '08:00', 'display_busy': '08:00❕'},
    {'hour': 12, 'display': '12:00', 'display_busy': '12:00❕'},
    {'hour': 18, 'display': '18:00', 'display_busy': '18:00❕'},
    {'hour': 22, 'display': '22:00', 'display_busy': '22:00❕'},
]

# Настройки календаря
CALENDAR = {
    'months_to_show': 2,           # сколько месяцев показывать
    'future_months_buttons': 6,     # сколько кнопок месяцев вперёд
    'buttons_per_row': 3,           # кнопок в ряду
}

# Роли пользователей
ROLES = {
    'admin': '⚙️ Админ',
    'owner': '👑 Собственник',
    'manager': '📋 Менеджер',
    'guest': '👤 Гость',
}

# Настройки БД
DATABASE_PATH = os.getenv('DATABASE_PATH', 'doors_ctrl_test.db')

# Настройки QR
QR_CONFIG = {
    'version': 1,
    'box_size': 10,
    'border': 4,
    'guest_length': 16,      # длина QR для гостя
    'cleaner_length': 8,      # длина QR для клинера (короче)
}

# ====== ИНДЕКСЫ ДЛЯ ТАБЛИЦ БАЗЫ ДАННЫХ ======

# Индексы для таблицы bookings (кортеж из БД)
BOOKING_ID = 0              # id
BOOKING_NUMBER = 1          # booking_number
BOOKING_APARTMENT_ID = 2    # apartment_id
BOOKING_GUEST_ID = 3        # guest_id
BOOKING_GUEST_NAME = 4      # guest_name
BOOKING_GUEST_PHONE = 5     # guest_phone
BOOKING_CREATED_BY = 6      # created_by
BOOKING_CHECKIN_DATE = 7    # checkin_date
BOOKING_CHECKOUT_DATE = 8   # checkout_date
BOOKING_QR_CODE = 9         # qr_code
BOOKING_STATUS = 10         # status
BOOKING_CREATED_AT = 11     # created_at
BOOKING_ACCESS_TYPE = 12    # access_type (rent/cleaning/repair/install)  👈 новое поле

# Индексы для таблицы apartments (кортеж из БД)
APARTMENT_ID = 0            # apartment_id
APARTMENT_OWNER_ID = 1      # owner_id
APARTMENT_ADDRESS = 2       # address
APARTMENT_INSTALLED_BY = 3  # installed_by
APARTMENT_ROOMS = 4         # rooms_count
APARTMENT_BEDS = 5          # bed_count
APARTMENT_TARIFF = 6        # tariff_id
APARTMENT_CREATED_AT = 7    # created_at
APARTMENT_LATITUDE = 8      # latitude
APARTMENT_LONGITUDE = 9     # longitude
APARTMENT_CADASTRAL = 10    # cadastral_number
APARTMENT_COUNTRY = 11      # country
APARTMENT_CITY = 12         # city
APARTMENT_DISTRICT = 13     # district
APARTMENT_STREET = 14       # street
APARTMENT_BUILDING = 15     # building
APARTMENT_POSTAL = 16       # postal_code
APARTMENT_APARTMENT = 17    # apartment (номер квартиры)                👈 новое поле
APARTMENT_TIMEZONE = 18     # timezone (Asia/Krasnoyarsk)               👈 новое поле

# Индексы для таблицы users (кортеж из БД)
USER_ID = 0                 # id
USER_TELEGRAM_ID = 1        # telegram_id
USER_FIRST_NAME = 2         # first_name
USER_LAST_NAME = 3          # last_name
USER_PHONE = 4              # phone
USER_ROLE = 5               # role
USER_PASSPORT = 6           # passport_data
USER_VERIFIED = 7           # verified
USER_CREATED_AT = 8         # created_at
USER_TIMEZONE = 9           # timezone (Europe/Moscow)                  👈 новое поле

# Индексы для таблицы guests (добавляем новую таблицу)
GUEST_ID = 0                # id
GUEST_FIRST_NAME = 1        # first_name
GUEST_LAST_NAME = 2         # last_name
GUEST_PHONE = 3             # phone
GUEST_PASSPORT = 4          # passport_data
GUEST_EMAIL = 5             # email
GUEST_TOTAL_BOOKINGS = 6    # total_bookings
GUEST_LAST_BOOKING = 7      # last_booking
GUEST_MARKETING = 8         # marketing_consent
GUEST_CREATED_AT = 9        # created_at
GUEST_TYPE = 10             # type (guest/cleaner/technician)           👈 новое поле
GUEST_MANAGER_ID = 11       # manager_id                                👈 новое поле
GUEST_OWNER_ID = 12         # owner_id                                  👈 новое поле

# Индексы для таблицы invites (добавляем)
INVITE_ID = 0               # id
INVITE_CODE = 1             # code
INVITE_CREATED_BY = 2       # created_by
INVITE_ROLE = 3             # role
INVITE_CREATED_AT = 4       # created_at
INVITE_EXPIRES_AT = 5       # expires_at
INVITE_USED_BY = 6          # used_by
INVITE_USED_AT = 7          # used_at
INVITE_IS_USED = 8          # is_used

# Индексы для таблицы devices (новая таблица)
DEVICE_ID = 0               # device_id
DEVICE_OWNER_ID = 1         # owner_id
DEVICE_INSTALLED_BY = 2     # installed_by
DEVICE_ESP32_ID = 3         # esp32_id
DEVICE_ESP32_IP = 4         # esp32_ip
DEVICE_LAST_SEEN = 5        # last_seen
DEVICE_IS_ACTIVE = 6        # is_active
DEVICE_FIRMWARE = 7         # firmware_version
DEVICE_BATTERY = 8          # battery_level
DEVICE_CREATED_AT = 9       # created_at
DEVICE_WIFI_SSID = 10       # wifi_ssid                                 👈 добавим позже
DEVICE_WIFI_PASSWORD = 11   # wifi_password                             👈 добавим позже

# Проверка токена
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в .env")
    print("Создайте файл .env и добавьте строку: BOT_TOKEN=ваш_токен")
    exit(1)