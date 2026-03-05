# handlers/apartment_requests.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import config
from database import (
    get_user_id_by_telegram,
    get_user_role,
    create_apartment_request,
    get_pending_requests_for_admin,
    get_my_requests,
    approve_request,
    reject_request,
    geocode_address
)
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


class ApartmentRequest(StatesGroup):
    waiting_for_address = State()
    waiting_for_wifi_ssid = State()
    waiting_for_wifi_password = State()
    confirm_data = State()


# ====== НОВАЯ ЗАЯВКА (ДЛЯ OWNER/ADMIN/ROOT) ======
@router.callback_query(F.data == "new_apartment_request")
async def new_apartment_request_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания заявки на квартиру"""

    logger.info(f"🔵 [new_apartment_request_start] Нажата кнопка создания заявки")
    logger.info(f"🔵 Пользователь: {callback.from_user.id} (@{callback.from_user.username})")

    await callback.answer()
    await state.set_state(ApartmentRequest.waiting_for_address)

    logger.info(f"🔵 Установлено состояние: waiting_for_address")

    await callback.message.answer(
        f"{config.EMOJI['apartment']} <b>Новая заявка на квартиру</b>\n\n"
        f"Введите адрес квартиры:\n"
        f"(например: ул. Светланская, д. 20, кв. 5)",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()  # 👈 кнопка отмены
    )



@router.message(ApartmentRequest.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка введённого адреса"""

    logger.info(f"🟢 [process_address] Получен адрес: {message.text}")
    logger.info(f"🟢 От пользователя: {message.from_user.id}")

    address = message.text.strip()

    # Геокодинг через DaData
    logger.info(f"🟢 Вызов geocode_address для: {address}")
    geo_result = geocode_address(address)
    logger.info(f"🟢 Результат геокодинга: {geo_result}")

    if not geo_result:
        logger.warning(f"⚠️ [process_address] Не удалось определить адрес: {address}")
        await message.answer(
            f"{config.EMOJI['warning']} Не удалось определить адрес. Попробуйте ещё раз:"
        )
        return

    # Сохраняем данные в state
    await state.update_data(
        raw_address=address,
        normalized_address=geo_result['normalized'],
        city=geo_result['city'],
        street=geo_result['street'],
        building=geo_result['building'],
        apartment=geo_result['apartment'],
        timezone=geo_result['timezone'],
        latitude=geo_result['lat'],
        longitude=geo_result['lon']
    )

    # Получаем данные для лога
    data = await state.get_data()
    logger.info(f"🟢 Данные сохранены в state: {data}")

    # Показываем результат и запрашиваем подтверждение
    text = (
        f"{config.EMOJI['apartment']} <b>Найден адрес:</b>\n"
        f"{geo_result['normalized']}\n\n"
        f"📍 Город: {geo_result['city']}\n"
        f"🕐 Часовой пояс: {geo_result['timezone']}\n\n"
        f"Всё верно?"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm_address"),
            InlineKeyboardButton(text="❌ Нет", callback_data="new_apartment_request")
        ]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(ApartmentRequest.confirm_data)
    logger.info(f"🟢 Установлено состояние: confirm_data")


@router.callback_query(F.data == "confirm_address")
async def confirm_address(callback: CallbackQuery, state: FSMContext):
    """Подтверждение адреса → сразу к WiFi (без комнат и мест)"""

    logger.info(f"🟡 [confirm_address] Адрес подтвержден")
    logger.info(f"🟡 Пользователь: {callback.from_user.id}")

    await callback.answer()
    await state.set_state(ApartmentRequest.waiting_for_wifi_ssid)
    logger.info(f"🟡 Установлено состояние: waiting_for_wifi_ssid")

    await callback.message.edit_text(
        f"{config.EMOJI['apartment']} <b>Параметры квартиры</b>\n\n"
        f"Введите название Wi-Fi сети (SSID):",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()  # 👈 кнопка отмены
    )


@router.message(ApartmentRequest.waiting_for_wifi_ssid)
async def process_wifi_ssid(message: Message, state: FSMContext):
    """Обработка SSID"""

    logger.info(f"🔴 [process_wifi_ssid] Получен SSID: {message.text}")

    ssid = message.text.strip()
    if not ssid:
        logger.warning(f"⚠️ [process_wifi_ssid] Пустой SSID")
        await message.answer("❌ SSID не может быть пустым")
        return

    await state.update_data(wifi_ssid=ssid)
    await state.set_state(ApartmentRequest.waiting_for_wifi_password)
    logger.info(f"🔴 Установлено состояние: waiting_for_wifi_password")

    await message.answer(
        f"Введите пароль Wi-Fi:",
        reply_markup=get_cancel_keyboard()  # 👈 кнопка отмены
    )


@router.message(ApartmentRequest.waiting_for_wifi_password)
async def process_wifi_password(message: Message, state: FSMContext):
    """Обработка пароля и сохранение заявки"""

    logger.info(f"🟤 [process_wifi_password] Получен пароль: {message.text}")

    password = message.text.strip()
    if not password:
        logger.warning(f"⚠️ [process_wifi_password] Пустой пароль")
        await message.answer("❌ Пароль не может быть пустым")
        return

    await state.update_data(wifi_password=password)

    # Получаем все данные
    data = await state.get_data()
    logger.info(f"🟤 Все данные из state: {data}")

    user_id = get_user_id_by_telegram(message.from_user.id)
    logger.info(f"🟤 user_id из БД: {user_id}")

    if not user_id:
        logger.error(f"❌ [process_wifi_password] Не удалось получить user_id для telegram_id: {message.from_user.id}")
        await message.answer("❌ Ошибка: пользователь не найден в системе")
        await state.clear()
        return

    # Создаём заявку в БД
    logger.info(f"🟤 Вызов create_apartment_request с параметрами:")
    logger.info(f"    owner_id: {user_id}")
    logger.info(f"    address: {data['normalized_address']}")
    logger.info(f"    city: {data['city']}")
    logger.info(f"    timezone: {data['timezone']}")
    logger.info(f"    wifi_ssid: {data['wifi_ssid']}")

    request_id = create_apartment_request(
        owner_id=user_id,
        address=data['normalized_address'],
        city=data['city'],
        street=data['street'],
        building=data['building'],
        apartment=data['apartment'],
        timezone=data['timezone'],
        wifi_ssid=data['wifi_ssid'],
        wifi_password=data['wifi_password'],
        latitude=data.get('latitude'),
        longitude=data.get('longitude')
    )

    logger.info(f"🟤 Результат create_apartment_request: request_id={request_id}")

    await state.clear()
    logger.info(f"🟤 State очищен")

    if request_id:
        await message.answer(
            f"{config.EMOJI['confirm']} <b>Заявка отправлена!</b>\n\n"
            f"ID заявки: {request_id}\n"
            f"Статус: ⏳ ожидает подтверждения администратором",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[  # 👈 возврат в меню
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="start")]
            ])
        )
        logger.info(f"✅ [process_wifi_password] Заявка {request_id} успешно создана")
    else:
        await message.answer(
            f"{config.EMOJI['warning']} <b>Ошибка при создании заявки</b>\n\n"
            f"Попробуйте позже или обратитесь к администратору",
            parse_mode="HTML"
        )
        logger.error(f"❌ [process_wifi_password] Не удалось создать заявку")


# ====== ПРОСМОТР ЗАЯВОК ДЛЯ ADMIN/ROOT ======
@router.callback_query(F.data == "admin_requests")
async def show_admin_requests(callback: CallbackQuery):
    """Показывает все активные заявки для ADMIN/ROOT"""

    await callback.answer()
    admin_id = get_user_id_by_telegram(callback.from_user.id)
    role = get_user_role(callback.from_user.id)

    requests = get_pending_requests_for_admin(admin_id, role)

    if not requests:
        await callback.message.edit_text(
            f"{config.EMOJI['info']} Нет активных заявок",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Назад", callback_data="start")
            ]])
        )
        return

    # Удаляем старое сообщение
    await callback.message.delete()

    for req in requests:
        # Формируем красивое сообщение для каждой заявки
        text = (
            f"🏠 <b>Заявка #{req['apartment_id']}</b>\n"
            f"👤 Владелец: {req['owner_name']}\n"
            f"📍 {req['address']}\n"
            f"🕐 Часовой пояс: {req['timezone']}\n"
            f"📶 Wi-Fi: {req['wifi_ssid']}\n"
            f"📅 Создана: {req['created_at'].strftime('%d.%m.%Y %H:%M')}"
        )

        # Кнопки для каждой заявки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_req_{req['apartment_id']}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_req_{req['apartment_id']}")
            ]
        ])

        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    # Кнопка возврата в меню
    await callback.message.answer(
        "👥 <b>Управление заявками</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Назад", callback_data="start")
        ]]),
        parse_mode="HTML"
    )


# ====== ПОДТВЕРЖДЕНИЕ ЗАЯВКИ ======
@router.callback_query(F.data.startswith("approve_req_"))
async def approve_request_handler(callback: CallbackQuery):
    """Подтверждение заявки и создание квартиры"""

    apartment_id = int(callback.data.split("_")[2])
    logger.info(f"✅ [approve_request_handler] Подтверждение заявки {apartment_id}")

    admin_id = get_user_id_by_telegram(callback.from_user.id)
    logger.info(f"✅ admin_id: {admin_id}")

    success = approve_request(apartment_id, admin_id)
    logger.info(f"✅ Результат подтверждения: {success}")

    if success:
        await callback.answer("✅ Заявка подтверждена, квартира создана", show_alert=True)
    else:
        await callback.answer("❌ Ошибка при подтверждении", show_alert=True)

    # Обновляем список заявок
    await show_admin_requests(callback)


# ====== ОТКЛОНЕНИЕ ЗАЯВКИ ======
@router.callback_query(F.data.startswith("reject_req_"))
async def reject_request_handler(callback: CallbackQuery):
    """Отклонение заявки"""

    apartment_id = int(callback.data.split("_")[2])
    logger.info(f"❌ [reject_request_handler] Отклонение заявки {apartment_id}")

    admin_id = get_user_id_by_telegram(callback.from_user.id)
    logger.info(f"❌ admin_id: {admin_id}")

    success = reject_request(apartment_id, admin_id)
    logger.info(f"❌ Результат отклонения: {success}")

    if success:
        await callback.answer("❌ Заявка отклонена", show_alert=True)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

    await show_admin_requests(callback)


# ====== МОИ ЗАЯВКИ (ДЛЯ OWNER/MANAGER) ======
@router.callback_query(F.data == "my_requests")
async def show_my_requests(callback: CallbackQuery):
    """Показывает заявки текущего пользователя"""

    logger.info(f"📋 [show_my_requests] Запрос своих заявок")

    user_id = get_user_id_by_telegram(callback.from_user.id)
    logger.info(f"📋 user_id: {user_id}")

    requests = get_my_requests(user_id)
    logger.info(f"📋 Найдено заявок: {len(requests)}")

    if not requests:
        await callback.message.edit_text(
            f"{config.EMOJI['info']} У вас нет заявок",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Назад", callback_data="start")
            ]])
        )
        await callback.answer()
        return

    text = f"{config.EMOJI['apartment']} <b>Ваши заявки</b>\n\n"
    keyboard = []

    for req in requests:
        status_emoji = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌',
            'canceled': '🚫'
        }.get(req['status'], '⏳')

        logger.info(f"📋 Заявка {req['apartment_id']}: статус {req['status']}")

        text += (
            f"{status_emoji} ID: {req['apartment_id']}\n"
            f"📍 {req['address']}\n"
            f"🕐 {req['timezone']}\n"
            f"📶 {req['wifi_ssid']}\n"
            f"Статус: {req['status']}\n\n"
        )

        if req['status'] == 'pending':
            keyboard.append([InlineKeyboardButton(
                text=f"❌ Отозвать заявку {req['apartment_id']}",
                callback_data=f"cancel_req_{req['apartment_id']}"
            )])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="start")])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


# ====== ОТОЗВАТЬ ЗАЯВКУ ======
@router.callback_query(F.data.startswith("cancel_req_"))
async def cancel_request_handler(callback: CallbackQuery):
    """Отмена заявки пользователем"""

    apartment_id = int(callback.data.split("_")[2])
    logger.info(f"🗑️ [cancel_request_handler] Отмена заявки {apartment_id}")

    user_id = get_user_id_by_telegram(callback.from_user.id)
    logger.info(f"🗑️ user_id: {user_id}")

    success = reject_request(apartment_id, user_id, canceled_by_user=True)
    logger.info(f"🗑️ Результат отмены: {success}")

    if success:
        await callback.answer("✅ Заявка отозвана", show_alert=True)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

    await show_my_requests(callback)


def get_cancel_keyboard():
    """Возвращает клавиатуру с кнопкой отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Отмена", callback_data="start")]
    ])