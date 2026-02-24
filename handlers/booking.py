# handlers/booking.py
from datetime import date, datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import config
from database import room_list, room_search, get_user_id_by_telegram
from utils import orders_list
from states import Form

router = Router()


# ====== СПИСОК КВАРТИР ======
@router.callback_query(F.data.startswith("order_"))
async def apartments_list(callback: CallbackQuery, state: FSMContext):
    """Показывает список квартир для бронирования"""

    # Сразу отвечаем на callback
    await callback.answer()

    # Получаем telegram_id из callback
    telegram_id = callback.data.split("_")[1]

    # Получаем внутренний ID пользователя
    user_id = get_user_id_by_telegram(telegram_id)

    if not user_id:
        print("❌ Пользователь не найден")
        await callback.message.answer("⚠️ Вы не зарегистрированы в системе")
        return

    # Сохраняем user_id в state
    await state.update_data(user_id=user_id)

    # Получаем список квартир
    apartments = room_list(user_id)

    if not apartments:
        await callback.message.answer("🏠 У вас нет доступных квартир")
        return
    # дата в колбэк
    today = date.today().strftime("%Y-%m-%d")

    # Формируем кнопки
    buttons = []
    for apt in apartments:
        # apt - кортеж: (apartment_id, owner_id, address, ...)
        apartment_id = apt[0]
        address = apt[2]

        callback_data = f'calendarCheckin_{today}_{apartment_id}'
        btn = [InlineKeyboardButton(
            text=f"{config.EMOJI['apartment']} {address}",
            callback_data=callback_data
        )]
        buttons.append(btn)

    # Кнопка в главное меню
    buttons.append([InlineKeyboardButton(
        text=f"{config.EMOJI['cancel']} В главное меню",
        callback_data='start'
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Устанавливаем состояние
    await state.set_state(Form.door_id)

    await callback.message.answer(
        f"{config.EMOJI['apartment']} <b>Выберите квартиру для бронирования:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    print("=" * 60 + "\n")


# ====== КАЛЕНДАРЬ ЗАЕЗДА ======
@router.callback_query(F.data.startswith("calendarCheckin_"))
async def calendar_checkin(callback: CallbackQuery, state: FSMContext):
    """Показывает календарь для выбора даты заезда"""
    # Сразу отвечаем на callback
    await callback.answer()

    data = callback.data.split("_")
    door_id = int(data[2])

    # Определяем режим: первый вход или переключение месяца
    if len(data) > 2:
        start_date_str = data[1]
        ymd = start_date_str.split('-')
        start_day = date(int(ymd[0]), int(ymd[1]), 1)  # всегда 1-е число
    else:
        start_day = date.today()

    state_data = await state.get_data()
    if 'user_id' not in state_data:
        await callback.message.delete()
        await callback.message.answer("⚠️ Данные устарели. Начните заново.")
        await state.clear()
        return

    user_id = state_data.get('user_id')
    await state.update_data(user_id=user_id, door_id=door_id)

    # Получаем данные календаря (8-10 недель)
    months, months1 = orders_list(door_id, start_day.strftime('%Y-%m-%d'))

    # Получаем адрес квартиры
    apt_info = room_search(door_id)
    if apt_info:
        address = apt_info[config.APARTMENT_ADDRESS]
    else:
        address = "🏠 Адрес не найден"
        print(f"⚠️ Квартира с ID {door_id} не найдена")

    await state.update_data(address=address)

    # ЕДИНАЯ КЛАВИАТУРА
    rows = []

    # Проходим по всем месяцам
    for month_idx, month_weeks in enumerate(months):
        # Заголовок месяца
        if month_weeks and month_weeks[0]:
            month_name = config.MONTHS[month_weeks[0][0][3]]
            year = month_weeks[0][0][2]
            rows.append([InlineKeyboardButton(
                text=f"{month_name} {year}",
                callback_data="ignore"
            )])

        # Недели месяца
        for week in month_weeks:
            btns = []
            for day in week:
                # day = (display_text, callback_data, year, month)
                display_text = day[0]
                callback_data = day[1]

                btns.append(InlineKeyboardButton(
                    text=display_text,
                    callback_data=callback_data
                ))
            rows.append(btns)


    # Кнопки других месяцев
    if months1:
        rows.append([InlineKeyboardButton(
            text="📅 Другие месяцы",
            callback_data="ignore"
        )])

        month_buttons = []
        for month in months1:
            month_parts = month.split('-')
            btn_text = f"{config.MONTHS[int(month_parts[1])]} {month_parts[0]}"
            callback_data = f'calendarCheckin_{month_parts[0]}-{month_parts[1]}-{month_parts[2]}_{door_id}'
            month_buttons.append(InlineKeyboardButton(
                text=btn_text,
                callback_data=callback_data
            ))

        # Разбиваем по 3 кнопки в ряд
        for i in range(0, len(month_buttons), 3):
            rows.append(month_buttons[i:i + 3])

    # Кнопка возврата к списку квартир
    rows.append([InlineKeyboardButton(
        text=f"{config.EMOJI['cancel']} К списку квартир",
        callback_data="back_to_apartments"
    )])


    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)

    # Устанавливаем состояние для обработки нажатий
    await state.set_state(Form.checkin_date)

    # Отправляем или обновляем сообщение
    try:
        await callback.message.edit_text(
            text=f"📅 <b>Шаг 1/5 • Выберите дату заселения</b>\n{address}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except:
        # Если не получается отредактировать, отправляем новое
        await callback.message.answer(
            text=f"📅 <b>Шаг 1/5 • Выберите дату заселения</b>\n{address}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    print("=" * 60 + "\n")



# ====== ВОЗВРАТ К СПИСКУ КВАРТИР ======
@router.callback_query(F.data == "back_to_apartments")
async def back_to_apartments(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку квартир"""

    # Сразу отвечаем на callback
    await callback.answer()

    # Получаем данные из state
    state_data = await state.get_data()
    user_id = state_data.get('user_id')

    if not user_id:
        print("❌ Нет user_id в state")
        user_id = callback.from_user.id
        print(f"📱 Берём из callback: {user_id}")

    # Получаем список квартир
    apartments = room_list(user_id)


    if not apartments:
        await callback.message.answer("🏠 У вас нет доступных квартир")
        return

    # Формируем кнопки
    buttons = []
    for apt in apartments:
        apartment_id = apt[0]
        address = apt[2]

        callback_data = f'calendarCheckin_{apartment_id}'
        btn = [InlineKeyboardButton(
            text=f"{config.EMOJI['apartment']} {address}",
            callback_data=callback_data
        )]
        buttons.append(btn)

    # Кнопка в главное меню
    buttons.append([InlineKeyboardButton(
        text=f"{config.EMOJI['cancel']} В главное меню",
        callback_data='start'
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    # Устанавливаем состояние
    await state.set_state(Form.door_id)
    print(f"🔧 Установлено состояние: Form.door_id")

    await callback.message.edit_text(
        f"{config.EMOJI['apartment']} <b>Выберите квартиру:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    print("=" * 60 + "\n")