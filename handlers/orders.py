# handlers/orders.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime

import config  # 👈 ИМПОРТИРУЕМ config, а не constants
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
    print(f"📦 [accept_order] ДО: {data}")

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
    from datetime import datetime
    import random
    import string

    booking_number = f"BKG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id}"

    checkin_str = data['checkin_date'].strftime("%Y-%m-%d %H:%M")
    checkout_str = data['checkout_date'].strftime("%Y-%m-%d %H:%M")
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

    print(f"📦 Сохраняем бронь: {order_info}")
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
    print(f"📦 [accept_order] УСПЕХ! Бронь создана")
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

    # ИСПОЛЬЗУЕМ КОНСТАНТЫ ИЗ CONFIG
    print(f"📦 [order_info] Данные из БД: {order}")
    print(f"📦 [order_info] Длина кортежа: {len(order)}")

    apartment_id = order[config.BOOKING_APARTMENT_ID]
    guest_name = order[config.BOOKING_GUEST_NAME]
    guest_phone = order[config.BOOKING_GUEST_PHONE]
    checkin_date = order[config.BOOKING_CHECKIN_DATE]
    checkout_date = order[config.BOOKING_CHECKOUT_DATE]
    qr_code = order[config.BOOKING_QR_CODE]
    status = order[config.BOOKING_STATUS]
    created_at = order[config.BOOKING_CREATED_AT]

    print(f"📦 [order_info] apartment_id={apartment_id}, guest_name={guest_name}, status={status}")

    # Получаем адрес квартиры
    door_info = doors_search1(apartment_id)
    if door_info:
        print(f"📦 [order_info] door_info: {door_info}")
        # Используем константу для адреса
        address = door_info[config.APARTMENT_ADDRESS]
    else:
        address = "адрес не найден"
        print(f"⚠️ Квартира apartment_id={apartment_id} не найдена")

    # Генерируем QR-код
    qrcode_image(qr_code)
    photo = FSInputFile('qrcode.png')

    # Кнопки действий
    btn1 = InlineKeyboardButton(
        text=f"{config.EMOJI['delete']} Удалить ордер",
        callback_data=f'delorder_{order[config.BOOKING_ID]}'
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

    # Преобразуем строки в datetime
    try:
        checkin_time = datetime.strptime(checkin_date, "%Y-%m-%d %H:%M")
        checkout_time = datetime.strptime(checkout_date, "%Y-%m-%d %H:%M")
        delta_date = checkout_time - checkin_time
        delta_str = str(delta_date)
    except Exception as e:
        print(f"⚠️ Ошибка преобразования даты: {e}")
        delta_str = "не определен"

    await callback.message.answer_photo(
        photo=photo,
        caption=f"{config.EMOJI['apartment']} <b>{address}</b>\n\n"
                f"{config.EMOJI['calendar']} Заезд: {checkin_date}\n"
                f"{config.EMOJI['calendar']} Выезд: {checkout_date}\n"
                f"{config.EMOJI['time']} Период: {delta_str}\n"
                f"{config.EMOJI['id']} Статус: {status}\n",
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