# handlers/orders.py
from datetime import datetime
import pytz
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import config
from database import take_order, doors_search1, del_order, new_order
from utils import qrcode_image
router = Router()


@router.callback_query(F.data.startswith("accept_order"))
async def accept_order_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание бронирования"""
    try:
        await callback.answer()
    except:
        pass

    # ====== 1. ПРОВЕРЯЕМ СОСТОЯНИЕ ======
    data = await state.get_data()

    # Что должно быть в state на финальном этапе
    required_keys = ['user_id', 'door_id', 'address', 'checkin_date', 'checkout_date', 'checkin_pass']
    missing = [key for key in required_keys if key not in data]

    if missing:
        print(f"⚠️ Ошибка: отсутствуют {missing} в state")

        # Удаляем старое сообщение
        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(
            f"{config.EMOJI['warning']} Данные устарели. Начните бронирование заново.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"{config.EMOJI['apartment']} К выбору квартир",
                    callback_data="start"
                )
            ]])
        )
        await state.clear()
        return

    # ====== 2. БЕРЁМ USER_ID (С ЗАПАСНЫМ ВАРИАНТОМ) ======
    user_id = data.get('user_id', callback.from_user.id)
    if 'user_id' not in data:
        print(f"⚠️ user_id не найден в state, берём из callback: {user_id}")

    # ====== 3. ФОРМИРУЕМ ДАННЫЕ ДЛЯ БД ======
    booking_number = f"BKG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id}"

    # Получаем смещение из state
    tz_offset = data.get('apartment_tz_offset', '+03')  # '+10' или '+03'

    # Создаём фиксированное смещение в минутах
    offset_minutes = int(tz_offset.replace('+', '')) * 60
    apartment_tz = pytz.FixedOffset(offset_minutes)  # +10 → 600 минут

    # Привязываем даты (replace, не localize)
    checkin_aware = data['checkin_date'].replace(tzinfo=apartment_tz)
    checkout_aware = data['checkout_date'].replace(tzinfo=apartment_tz)

    # ✅ Преобразуем в строки с меткой пояса (ISO формат)
    checkin_str = checkin_aware.isoformat()  # "2026-04-02T08:00:00+10:00"
    checkout_str = checkout_aware.isoformat()  # "2026-04-03T08:00:00+10:00"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    guest_name = f"Гость {user_id}"
    guest_phone = str(user_id)
    qr_code = data['checkin_pass']

    order_info = (
        booking_number,
        data['door_id'],
        guest_name,
        guest_phone,
        checkin_str,
        checkout_str,
        qr_code,
        'active',
        created_at,
        'rent'
    )

    new_order(order_info)

    # ====== 4. ГЕНЕРИРУЕМ QR ======
    qrcode_image(qr_code)
    photo = FSInputFile('qrcode.png')

    # ====== 5. КНОПКА ВОЗВРАТА ======
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"{config.EMOJI['apartment']} К началу",
            callback_data='start'
        )
    ]])

    # ====== 6. ОТПРАВЛЯЕМ ПОДТВЕРЖДЕНИЕ ======
    delta_date = data['checkout_date'] - data['checkin_date']
    room_address = data.get('address', '')

    await callback.message.answer_photo(
        photo=photo,
        caption=f"{config.EMOJI['apartment']} <b>{room_address}</b>\n\n"
                f"{config.EMOJI['calendar']} Заезд: {data['checkin_date'].strftime('%d.%m.%Y %H:%M')}\n"
                f"{config.EMOJI['calendar']} Выезд: {data['checkout_date'].strftime('%d.%m.%Y %H:%M')}\n"
                f"{config.EMOJI['time']} Период: {delta_date}\n\n"
                f"{config.EMOJI['confirm']} Бронирование подтверждено!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    # ====== 7. ОЧИЩАЕМ STATE И ЛОГИРУЕМ ======
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("orderinfo_"))
async def order_info_handler(callback: CallbackQuery, state: FSMContext):
    # ✅ Сразу отвечаем
    try:
        await callback.answer()
    except:
        pass
    """Информация по существующему бронированию"""

    order_id = callback.data.split("_")[2]
    await state.clear()

    order = take_order(order_id)
    if not order:
        await callback.message.answer(f"{config.EMOJI['warning']} Бронирование не найдено")
        return

    # Получаем данные брони
    apartment_id = order['apartment_id']
    guest_name = order['guest_name']
    guest_phone = order['guest_phone']
    checkin_date = order['checkin_date']
    checkout_date = order['checkout_date']
    qr_code = order['qr_code']
    status = order['status']
    created_at = order['created_at']

    # Получаем информацию о квартире
    door_info = doors_search1(apartment_id)
    if door_info:
        address = door_info['address']
        # Получаем таймзону квартиры
        apt_tz_str = door_info.get('timezone', 'Europe/Moscow')
        apt_tz = pytz.timezone(apt_tz_str)

        # Конвертируем время в таймзону квартиры
        checkin_local = checkin_date.astimezone(apt_tz)
        checkout_local = checkout_date.astimezone(apt_tz)

        print(f"📦 [order_info] таймзона квартиры: {apt_tz_str}")
    else:
        address = "адрес не найден"
        checkin_local = checkin_date
        checkout_local = checkout_date
        print(f"⚠️ Квартира apartment_id={apartment_id} не найдена")

    # Генерируем QR-код
    qrcode_image(qr_code)
    photo = FSInputFile('qrcode.png')

    # Кнопки действий
    btn1 = InlineKeyboardButton(
        text=f"{config.EMOJI['delete']} Удалить ордер",
        callback_data=f'delorder_{order["id"]}'
    )
    btn2 = InlineKeyboardButton(
        text=f"{config.EMOJI['door']} Открыть дверь",
        callback_data='start'
    )
    btn3 = InlineKeyboardButton(
        text=f"{config.EMOJI['apartment']} К началу",
        callback_data='start'
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2], [btn3]])

    # Рассчитываем период
    delta_date = checkout_local - checkin_local
    delta_str = str(delta_date)

    # Формируем подпись с локальным временем
    caption = (
        f"{config.EMOJI['apartment']} <b>{address}</b>\n\n"
        f"{config.EMOJI['calendar']} Заезд: {checkin_local.strftime('%d.%m.%Y %H:%M')}\n"
        f"{config.EMOJI['calendar']} Выезд: {checkout_local.strftime('%d.%m.%Y %H:%M')}\n"
        f"{config.EMOJI['time']} Период: {delta_str}\n"
        f"{config.EMOJI['id']} Статус: {status}\n"
    )
    await callback.message.delete()
    await callback.message.answer_photo(
        photo=photo,
        caption=caption,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("delorder_"))
async def del_order_confirm_handler(callback: CallbackQuery):
    """Подтверждение удаления бронирования"""
    try:
        await callback.answer()
    except:
        pass

    order_id = callback.data.split("_")[1]

    btn1 = InlineKeyboardButton(
        text=f"{config.EMOJI['confirm']} Да, удалить",
        callback_data=f'delorder1_{order_id}'
    )
    btn2 = InlineKeyboardButton(
        text=f"{config.EMOJI['cancel']} Нет",
        callback_data='start'
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2]])

    await callback.message.answer(
        text=f"{config.EMOJI['delete']} <b>УДАЛЕНИЕ БРОНИРОВАНИЯ</b>\n\n"
             f"Вы уверены?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("delorder1_"))
async def del_order_execute_handler(callback: CallbackQuery):
    """Непосредственное удаление бронирования"""
    try:
        await callback.answer()
    except:
        pass

    order_id = callback.data.split("_")[1]

    del_order(order_id)

    btn1 = InlineKeyboardButton(
        text=f"{config.EMOJI['apartment']} К началу",
        callback_data='start'
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1]])

    await callback.message.answer(
        text=f"{config.EMOJI['confirm']} Бронирование удалено",
        reply_markup=keyboard
    )