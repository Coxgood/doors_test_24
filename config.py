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

# Индексы для таблицы apartments (кортеж из БД)
APARTMENT_ID = 0            # apartment_id
APARTMENT_OWNER_ID = 1      # owner_id
APARTMENT_ADDRESS = 2       # address
APARTMENT_ROOMS = 3         # rooms_count
APARTMENT_BEDS = 4          # bed_count
APARTMENT_TARIFF = 5        # tariff_id

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

# Проверка токена
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в .env")
    print("Создайте файл .env и добавьте строку: BOT_TOKEN=ваш_токен")
    exit(1)