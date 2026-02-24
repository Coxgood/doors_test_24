# handlers/calendar.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

import config
from database import room_search
from utils import orders_list

router = Router()


@router.callback_query(F.data.startswith("show_month_"))
async def show_month_handler(callback: CallbackQuery, state: FSMContext):
    """Показать календарь для выбранного месяца"""
    await callback.answer()

    try:
        # Разбираем callback: show_month_1_2026_3
        parts = callback.data.split("_")
        door_id = int(parts[2])
        year = int(parts[3])
        month = int(parts[4])

        # Получаем адрес квартиры
        door_info = room_search(door_id)
        if not door_info:
            await callback.message.answer(f"{config.EMOJI['warning']} Квартира не найдена")
            return

        address = door_info[3]

        # Формируем дату начала (первое число выбранного месяца)
        start_date = f"{year}-{month:02d}-01"

        # Получаем календарь с выбранного месяца
        months, months1 = orders_list(door_id, start_date)

        # Удаляем старые сообщения (опционально)
        await callback.message.delete()

        # Показываем 2 месяца
        for weeks in months:
            btnss = []
            for week in weeks:
                btns = []
                for day in week:
                    btn = InlineKeyboardButton(
                        text=str(day[0]),
                        callback_data=str(day[1])
                    )
                    btns.append(btn)
                btnss.append(btns)

            keyboard = InlineKeyboardMarkup(inline_keyboard=btnss)
            month_name = config.MONTHS[weeks[0][0][3]]
            year = weeks[0][0][2]

            await callback.message.answer(
                text=f"{config.EMOJI['calendar']} <b>{month_name} {year}</b>\n"
                     f"{config.EMOJI['apartment']} {address}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        # Кнопки с другими месяцами (по 3 в ряд)
        if months1:
            month_buttons = []
            for month_str in months1:
                month_parts = month_str.split('-')
                btn_text = f"{config.MONTHS[int(month_parts[1])]} {month_parts[0]}"
                callback_data = f'show_month_{door_id}_{month_parts[0]}-{month_parts[1]}-{month_parts[2]}'
                month_buttons.append(
                    InlineKeyboardButton(text=btn_text, callback_data=callback_data)
                )

            # Раскладываем по 3 в ряд
            rows = []
            for i in range(0, len(month_buttons), 3):
                rows.append(month_buttons[i:i + 3])

            # Кнопка отмены
            rows.append([InlineKeyboardButton(
                text=f"{config.EMOJI['cancel']} Отмена",
                callback_data='start'
            )])

            keyboard_next = InlineKeyboardMarkup(inline_keyboard=rows)
            await callback.message.answer(
                text=f"{config.EMOJI['calendar']} <b>Другие месяцы:</b>",
                reply_markup=keyboard_next,
                parse_mode="HTML"
            )

    except Exception as e:
        print(f"Ошибка в show_month_handler: {e}")
        await callback.message.answer(f"{config.EMOJI['warning']} Произошла ошибка")