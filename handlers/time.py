# handlers/time.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime

import config
from database import room_search
from utils import check_timein, margin_day, generate_password
from states import Form

router = Router()


@router.callback_query(F.data.startswith("checktimein_"))
async def check_time_in_handler(callback: CallbackQuery, state: FSMContext):
    # ✅ Сразу отвечаем
    try:
        await callback.answer()
    except:
        pass

    # ====== 1. ПРОВЕРЯЕМ СОСТОЯНИЕ ======
    data = await state.get_data()

    # Что должно быть в state на этом этапе
    required_keys = ['user_id', 'door_id', 'address']
    missing = [key for key in required_keys if key not in data]

    if missing:
        print(f"⚠️ Ошибка: отсутствуют {missing} в state")

        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(
            f"{config.EMOJI['warning']} Данные устарели. Начните с выбора квартиры.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"{config.EMOJI['apartment']} К выбору квартир",
                    callback_data="start"
                )
            ]])
        )
        await state.clear()
        return

    # ====== 2. СОХРАНЯЕМ USER_ID ======
    user_id = data.get('user_id')
    await state.update_data(user_id=user_id)

    # ====== 3. РАЗБИРАЕМ CALLBACK ======
    parts = callback.data.split("_")
    date_str = parts[1]
    door_id_str = parts[2]

    # Проверка door_id
    if door_id_str == 'None' or not door_id_str.isdigit():
        print(f"❌ Ошибка: door_id_str = {door_id_str}")
        await callback.message.answer("❌ Ошибка: некорректный ID квартиры. Попробуйте снова.")
        return

    door_id = int(door_id_str)

    # ====== 4. ПОЛУЧАЕМ МАСКУ ВРЕМЕНИ ======
    mask = check_timein(date_str, door_id)

    date_parts = date_str.split('-')
    mark = mask[0][1].split('_')[0]

    # ====== 5. ФОРМИРУЕМ КНОПКИ ======
    btns = []
    for m in mask:
        btn = InlineKeyboardButton(text=m[0], callback_data=m[1])
        btns.append(btn)

    if mark == 'checkoutday':
        del btns[0]

    key = [InlineKeyboardButton(
        text=f"{config.EMOJI['cancel']} К списку квартир",
        callback_data='start'
    )]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[btns, key])

    # ====== ПОЛУЧАЕМ АДРЕС ======
    address = data.get('address', '')

    # ====== 6. ОТПРАВЛЯЕМ СООБЩЕНИЕ ======
    await callback.message.answer(
        text=(
            f"{config.EMOJI['time']} <b>Шаг 2/5 • Выберите время заселения</b>\n"
            f"{address}\n"
            f"{date_parts[2]}-{config.MONTHS[int(date_parts[1])]}-{date_parts[0]}"
        ),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("checkoutday_"))
async def checkout_date_handler(callback: CallbackQuery, state: FSMContext):
    # ✅ Сразу отвечаем
    try:
        await callback.answer()
    except:
        pass


    parts = callback.data.split("_")
    parts = parts[1:]

    date = parts[0].split("-")
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])
    hour = int(date[3])

    door_id = int(parts[1])


    if month < 1 or month > 12:
        await callback.message.answer("❌ Ошибка в дате. Попробуйте снова.")
        return

    checkin_date = datetime(year, month, day, hour)

    # Проверка state
    data = await state.get_data()
    required_keys = ['user_id', 'door_id']
    missing = [key for key in required_keys if key not in data]


    if missing:
        await callback.message.delete()
        await callback.message.answer("⚠️ Данные устарели. Начните заново.")
        await state.clear()
        return

    user_id = data.get('user_id')
    await state.update_data(user_id=user_id, checkin_date=checkin_date, door_id=door_id)


    # Получаем доступные даты для выселения
    checkin_day = [year, month, day, hour]
    months = margin_day(checkin_day, door_id)
    address = data.get('address', '')

    rows = []

    # ===== ПЕРВЫЙ МЕСЯЦ =====
    if len(months) > 0:
        weeks = months[0]
        month_name = config.MONTHS[weeks[0][0][3]]
        year = weeks[0][0][2]

        rows.append([InlineKeyboardButton(
            text=f"{month_name} {year}",
            callback_data="ignore"
        )])

        for week in weeks:
            btns = []
            for day in week:
                btns.append(InlineKeyboardButton(
                    text=str(day[0]),
                    callback_data=str(day[1])
                ))
            rows.append(btns)

    # ===== ВТОРОЙ МЕСЯЦ =====
    if len(months) > 1:
        weeks = months[1]
        month_name = config.MONTHS[weeks[0][0][3]]
        year = weeks[0][0][2]

        rows.append([InlineKeyboardButton(
            text=f"{month_name} {year}",
            callback_data="ignore"
        )])

        for week in weeks:
            btns = []
            for day in week:
                btns.append(InlineKeyboardButton(
                    text=str(day[0]),
                    callback_data=str(day[1])
                ))
            rows.append(btns)

    # ===== КНОПКА ВОЗВРАТА =====
    rows.append([InlineKeyboardButton(
        text=f"{config.EMOJI['cancel']} К списку квартир",
        callback_data="start"  # или back_to_apartments?
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    # Отправляем одно сообщение с адресом и шагом
    await callback.message.answer(
        text=(
            f"📅 <b>Шаг 3/5 • Выберите дату выселения</b>\n"
            f"{address}\n"
            f"Заселение: {checkin_date.strftime('%d.%m.%Y %H:%M')}"
        ),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("checkouttime_"))
async def checkout_time_handler(callback: CallbackQuery, state: FSMContext):
    """Выбор времени выселения"""
    # ✅ Сразу отвечаем
    try:
        await callback.answer()
    except:
        pass


    # ====== 1. ПРОВЕРЯЕМ СОСТОЯНИЕ ======
    data = await state.get_data()

    # ====== 2. РАЗБИРАЕМ CALLBACK ======
    parts = callback.data.split("_")

    if len(parts) < 4:
        print(f"❌ Ошибка: недостаточно данных")
        await callback.answer("❌ Ошибка формата")
        return

    date_str = parts[1]        # "2026-03-11"
    min_hour = int(parts[2])    # 2 (минимальный доступный час)
    max_hour = int(parts[3])    # 23 (максимальный доступный час)


    # ====== 3. ПРОВЕРЯЕМ STATE ======
    required_keys = ['user_id', 'door_id', 'address', 'checkin_date']
    missing = [key for key in required_keys if key not in data]

    if missing:
        print(f"⚠️ Ошибка: отсутствуют {missing} в state")
        await callback.message.answer(
            f"{config.EMOJI['warning']} Данные устарели. Начните с выбора квартиры."
        )
        await state.clear()
        return

    # ====== 4. ФОРМИРУЕМ КНОПКИ ======
    btns = []
    time_slots = config.TIME_SLOTS  # [8, 12, 18, 22]

    for slot in time_slots:
        if min_hour < slot['hour'] <= max_hour:
            # Слот доступен
            btn_text = slot['display']
            # ✅ ИСПРАВЛЕНО: правильный формат с пробелом и минутами
            callback_data = f"orderchek_{date_str} {slot['hour']}:00"
        else:
            # Слот недоступен
            btn_text = slot['display_busy']
            callback_data = 'donttouchthis'

        btn = InlineKeyboardButton(text=btn_text, callback_data=callback_data)
        btns.append(btn)

    # Кнопка возврата
    key = [InlineKeyboardButton(
        text=f"{config.EMOJI['cancel']} К списку квартир",
        callback_data='start'
    )]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[btns, key])

    # ====== 5. ОТПРАВЛЯЕМ СООБЩЕНИЕ ======
    address = data.get('address', '')
    checkin_date = data['checkin_date'].strftime('%d.%m.%Y %H:%M')

    await callback.message.answer(
        text=(
            f"{config.EMOJI['time']} <b>Шаг 4/5 • Выберите время выселения</b>\n"
            f"{address}\n"
            f"Заселение: {checkin_date}\n"
            f"Выбранная дата: {date_str}"
        ),
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    # ====== 6. ЛОГИРУЕМ ======
    data = await state.get_data()
    await callback.answer()


@router.callback_query(F.data.startswith("orderchek_"))
async def order_check_handler(callback: CallbackQuery, state: FSMContext):
    """Подтверждение бронирования"""

    # ====== 1. ПРОВЕРЯЕМ СОСТОЯНИЕ ======
    data = await state.get_data()

    # Что должно быть в state на этом этапе
    required_keys = ['user_id', 'door_id', 'address', 'checkin_date']
    missing = [key for key in required_keys if key not in data]

    if missing:
        print(f"⚠️ Ошибка: отсутствуют {missing} в state")

        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(
            f"{config.EMOJI['warning']} Данные устарели. Начните с выбора квартиры.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"{config.EMOJI['apartment']} К выбору квартир",
                    callback_data="start"
                )
            ]])
        )
        await state.clear()
        await callback.answer()
        return

    # ====== 2. СОХРАНЯЕМ USER_ID ======
    user_id = data.get('user_id')
    await state.update_data(user_id=user_id)

    # ====== 3. РАЗБИРАЕМ CALLBACK ======
    try:
        data1 = callback.data.split("_")[1:]
        if len(data1) < 1:
            raise ValueError("Недостаточно данных")

        dt_checkout = datetime.strptime(data1[0], "%Y-%m-%d %H:%M")

    except Exception as e:
        print(f"❌ Ошибка парсинга callback: {e}")
        await callback.message.answer("❌ Ошибка в данных. Попробуйте снова.")
        return

    # ====== 4. ОБНОВЛЯЕМ STATE ======
    await state.update_data(checkout_date=dt_checkout)

    qr_code = generate_password()
    await state.update_data(checkin_pass=qr_code)

    # ====== 5. ПОЛУЧАЕМ АКТУАЛЬНЫЕ ДАННЫЕ ======
    data = await state.get_data()

    # ====== 6. ФОРМИРУЕМ КНОПКИ ======
    btn1 = InlineKeyboardButton(
        text=f"{config.EMOJI['confirm']} Да",
        callback_data='accept_order'
    )
    btn2 = InlineKeyboardButton(
        text=f"{config.EMOJI['cancel']} Нет",
        callback_data='start'
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2]])

    # ====== 7. РАССЧИТЫВАЕМ ПЕРИОД ======
    delta_time = data['checkout_date'] - data['checkin_date']
    days = delta_time.days
    hours = delta_time.seconds // 3600

    # ====== 8. ОТПРАВЛЯЕМ СООБЩЕНИЕ ======
    await callback.message.answer(
        text=(
            f"{config.EMOJI['apartment']} <b>{data.get('address', '')}</b>\n\n"
            f"{config.EMOJI['calendar']} Заселение: {data['checkin_date'].strftime('%d.%m.%Y %H:%M')}\n"
            f"{config.EMOJI['calendar']} Выселение: {data['checkout_date'].strftime('%d.%m.%Y %H:%M')}\n"
            f"{config.EMOJI['time']} Период: {days} дн. {hours} ч.\n\n"
            f"✅ <b>Шаг 5/5 • Подтверждение</b>\n"
            f"Забронировать квартиру?"
        ),
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    # ====== 9. ЛОГИРУЕМ ИТОГ ======
    data = await state.get_data()
    await callback.answer()

@router.callback_query(F.data == "donttouchthis")
async def dont_touch_handler(callback: CallbackQuery):
    """Заглушка для недоступных дат"""
    await callback.answer(
        text=f"{config.EMOJI['warning']} Это время недоступно",
        show_alert=False
    )