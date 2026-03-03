# utils.py
import calendar
import random
import string
import pytz
from datetime import datetime, timedelta, timezone
from database import get_connection, get_bookings_with_local_time
import config
import qrcode

# ========== ГЕНЕРАЦИЯ ==========

def generate_password(length=12):
    """Генерирует пароль доступа"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def qrcode_image(password):
    """Генерирует картинку QR"""
    img = qrcode.make(password)
    img.save("qrcode.png")


# ========== КАЛЕНДАРЬ ==========
def orders_list(door_id, start_day):
    """
    Возвращает данные для календаря бронирований
    start_day - дата начала показа (обычно сегодня или первое число месяца)
    """

    # Получаем брони с правильной таймзоной
    bookings, apt_tz = get_bookings_with_local_time(door_id)

    # Текущая дата в таймзоне квартиры
    today = datetime.now(apt_tz).replace(hour=0, minute=0, second=0, microsecond=0)

    # Дата начала показа (приводим к таймзоне квартиры)
    start = datetime.strptime(start_day, "%Y-%m-%d").replace(tzinfo=apt_tz)

    # Рассчитываем дату окончания показа (8 недель от start)
    end_date = start + timedelta(weeks=8)

    # Словарь с данными для дней
    day_data = {}

    for booking in bookings:
        order_id = booking['id']
        checkin = booking['checkin']
        checkout = booking['checkout']

        current = checkin
        while current.date() <= checkout.date():
            date_str = current.strftime("%Y-%m-%d")

            if current.date() < start.date() or current.date() > end_date.date():
                current += timedelta(days=1)
                continue

            if current.date() == checkin.date() and current.date() == checkout.date():
                # Один день - частично занят
                day_data[date_str] = ('partial', date_str, door_id)
            elif current.date() == checkin.date():
                # День заезда
                if checkin.hour >= 12:
                    day_data[date_str] = ('partial', date_str, door_id)
                else:
                    day_data[date_str] = ('full', order_id)
            elif current.date() == checkout.date():
                # День выезда
                day_data[date_str] = ('partial', date_str, door_id)
            else:
                # Дни между
                day_data[date_str] = ('full', order_id)

            current += timedelta(days=1)

    # Формируем календарь (максимум 8 недель)
    months = []
    current_date = start.replace(day=1)
    total_weeks = 0
    max_weeks = 10
    first_month_done = False

    while total_weeks < max_weeks:
        cal = calendar.monthcalendar(current_date.year, current_date.month)
        weeks = []
        month_has_days = False

        for week in cal:
            week_days = []
            week_has_days = False

            for day in week:
                if day == 0:
                    week_days.append((' ', 'ignore', current_date.year, current_date.month))
                else:
                    date_str = f"{current_date.year}-{current_date.month:02d}-{day:02d}"
                    day_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                    # Для второго месяца показываем все дни
                    if len(months) == 1:
                        if day_date < today.date():
                            week_days.append((' ', 'ignore', current_date.year, current_date.month))
                        else:
                            week_has_days = True
                            month_has_days = True

                            if date_str in day_data:
                                data = day_data[date_str]
                                if data[0] == 'full':
                                    display = f"{day}❗"
                                    callback = f"orderinfo_{date_str}_{data[1]}"
                                else:  # partial
                                    display = f"{day}❕"
                                    callback = f"checktimein_{data[1]}_{data[2]}"
                            else:
                                display = str(day)
                                callback = f"checktimein_{date_str}_{door_id}"

                            week_days.append((display, callback, current_date.year, current_date.month))

                    else:  # первый месяц
                        if day_date < start.date() or day_date < today.date():
                            week_days.append((' ', 'ignore', current_date.year, current_date.month))
                        elif day_date > end_date.date() and not first_month_done:
                            week_days.append((' ', 'ignore', current_date.year, current_date.month))
                        else:
                            week_has_days = True
                            month_has_days = True

                            if date_str in day_data:
                                data = day_data[date_str]
                                if data[0] == 'full':
                                    display = f"{day}❗"
                                    callback = f"orderinfo_{date_str}_{data[1]}"
                                else:  # partial
                                    display = f"{day}❕"
                                    callback = f"checktimein_{data[1]}_{data[2]}"
                            else:
                                display = str(day)
                                callback = f"checktimein_{date_str}_{door_id}"

                            week_days.append((display, callback, current_date.year, current_date.month))

            if week_has_days:
                weeks.append(week_days)

        if month_has_days:
            if total_weeks + len(weeks) <= max_weeks:
                months.append(weeks)
                total_weeks += len(weeks)
            else:
                remaining = max_weeks - total_weeks
                months.append(weeks[:remaining])
                total_weeks = max_weeks
                break

            if len(months) == 1:
                first_month_done = True

        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    # Формируем список будущих месяцев
    future_months = []
    next_month = current_date

    for i in range(6):
        future_months.append(next_month.strftime("%Y-%m-%d"))
        if next_month.month == 12:
            next_month = next_month.replace(year=next_month.year + 1, month=1)
        else:
            next_month = next_month.replace(month=next_month.month + 1)

    return months, future_months


def margin_day(chekin, room_id):
    """Возвращает доступные даты для выселения"""
    str_date = f'{chekin[0]}-{chekin[1]}-{chekin[2]} {chekin[3]}:00'
    chekin_date = datetime.strptime(str_date, '%Y-%m-%d %H:%M')

    # Получаем брони с правильной таймзоной
    bookings, apt_tz = get_bookings_with_local_time(room_id)

    # Приводим chekin_date к таймзоне квартиры
    chekin_date = apt_tz.localize(chekin_date)

    margin_date = datetime(3970, 1, 1, tzinfo=apt_tz)

    # Собираем все события (заезды и выезды) в местном времени
    events = []

    for booking in bookings:
        events.append(('checkin', booking['checkin'], booking['id']))
        events.append(('checkout', booking['checkout'], booking['id']))

    for i, ev in enumerate(events):
        event_type, event_date, event_id = ev

    # Сортируем по дате
    events.sort(key=lambda x: x[1])

    # Находим ближайшее событие
    same_day_events = [e for e in events if e[1].date() == chekin_date.date()]

    for event_type, event_date, event_id in same_day_events:
        if event_type == 'checkout' and event_date > chekin_date:
            margin_date = event_date
            break

    if margin_date.year == 3970:
        for event_type, event_date, event_id in events:
            if event_type == 'checkin' and event_date >= chekin_date:
                margin_date = event_date
                break

    b1_date = chekin_date.date()
    e1_date = margin_date.date()

    if chekin_date.day > 16:
        m = 1
    else:
        m = 0

    cal = calendar.Calendar(firstweekday=0)
    months = []

    for i in range(0, 2 + m):
        month1 = chekin_date.month + i
        year1 = chekin_date.year
        if month1 > 12:
            year1 += 1
            month1 = 1
        weeks1 = cal.monthdatescalendar(year1, month1)
        weeks = []
        for week1 in weeks1:
            week = []
            for day1 in week1:
                if day1.month != month1:
                    day = (' ', 'donttouchthis', year1, month1)
                    week.append(day)
                    continue

                if day1 == b1_date:
                    b_hour = chekin_date.hour
                else:
                    b_hour = 2

                btn_txt = f'  {day1.day}   '
                callback = f'checkouttime_{day1}_{b_hour}_23'
                day = (btn_txt, callback, year1, month1)

                if day1 > margin_date.date():
                    day = (' ', 'donttouchthis', year1, month1)
                if day1 < chekin_date.date():
                    day = (' ', 'donttouchthis', year1, month1)
                if day1 == margin_date.date():
                    btn_txt = f'  {day1.day}❕  '
                    callback = f'checkouttime_{day1}_{b_hour}_{margin_date.hour}'
                    day = (btn_txt, callback, year1, month1)

                week.append(day)

            if any(day[0] != ' ' for day in week):
                weeks.append(week)

        if weeks:
            months.append(weeks)

    # Убираем дубликаты
    unique_months = []
    seen = set()
    for month_weeks in months:
        if month_weeks and month_weeks[0] and month_weeks[0][0]:
            year = month_weeks[0][0][2]
            month = month_weeks[0][0][3]
            key = f"{year}-{month}"
            if key not in seen:
                seen.add(key)
                unique_months.append(month_weeks)

    return unique_months


def check_timein(date1, door_id):
    date1 = date1.split(' ')[0]
    date2 = date1.split('-')

    # Получаем брони с правильной таймзоной
    bookings, apt_tz = get_bookings_with_local_time(door_id)

    # Целевая дата в таймзоне квартиры
    naive_date = datetime.strptime(date1, '%Y-%m-%d')
    target_date = apt_tz.localize(naive_date)

    checkout_mask = [[1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [1, 1, 1, 0, 0], [1, 1, 1, 1, 0]]
    checkin_mask = [[0, 1, 1, 1, 1], [0, 0, 1, 1, 1], [0, 0, 0, 1, 1], [0, 0, 0, 0, 1]]

    orders = []
    for booking in bookings:
        checkin_date = booking['checkin']
        checkout_date = booking['checkout']
        ord_data = (booking['id'], checkin_date, checkout_date, 0)

        if checkin_date.date() == target_date.date():
            orders.append(ord_data)
        if checkout_date.date() == target_date.date():
            orders.append(ord_data)
        if checkin_date.date() == checkout_date.date() == target_date.date():
            orders.append(ord_data)

    orders = sorted(orders, key=lambda x: x[1])

    orders1 = []
    for order in orders:
        checkin_date = order[1]
        checkout_date = order[2]
        h_in = str(order[1].time()).split(':')[0]
        h_out = str(order[2].time()).split(':')[0]

        mask = None
        if checkin_date.date() == target_date.date():
            if h_in == '08':
                mask = checkin_mask[0]
            elif h_in == '12':
                mask = checkin_mask[1]
            elif h_in == '18':
                mask = checkin_mask[2]
            elif h_in == '22':
                mask = checkin_mask[3]

        if checkout_date.date() == target_date.date():
            if h_out == '08':
                mask = checkout_mask[0]
            elif h_out == '12':
                mask = checkout_mask[1]
            elif h_out == '18':
                mask = checkout_mask[2]
            elif h_out == '22':
                mask = checkout_mask[3]

        if checkin_date.date() == checkout_date.date() == target_date.date():
            # Однодневная бронь
            mask1 = None
            mask2 = None

            if h_in == '08':
                mask1 = checkin_mask[0]
            elif h_in == '12':
                mask1 = checkin_mask[1]
            elif h_in == '18':
                mask1 = checkin_mask[2]
            elif h_in == '22':
                mask1 = checkin_mask[3]

            if h_out == '08':
                mask2 = checkout_mask[0]
            elif h_out == '12':
                mask2 = checkout_mask[1]
            elif h_out == '18':
                mask2 = checkout_mask[2]
            elif h_out == '22':
                mask2 = checkout_mask[3]

            if mask1 and mask2:
                mask = [mask1[i] * mask2[i] for i in range(5)]

        if mask:
            for i in range(5):
                mask[i] *= order[0]
            orders1.append((order[0], order[1], order[2], mask))

    d_mask = [0, 0, 0, 0, 0]
    for order in orders1:
        for i in range(5):
            d_mask[i] += order[3][i]

    time_marker1 = ('00:00>08:00', '08:00', '12:00', '18:00', '22:00')
    time_marker2 = ('>08:00❗', '08:00❗', '12:00❗', '18:00❗', '22:00❗')
    callback_time = ('00', '08', '12', '18', '22')

    day_mask = []
    for i in range(5):
        if d_mask[i] == 0:
            btn_txt = time_marker1[i]
            callback = f'checkoutday_{date2[0]}-{date2[1]}-{date2[2]}-{callback_time[i]}_{door_id}'
        else:
            btn_txt = time_marker2[i]
            callback = f'orderinfo_{date2[0]}-{date2[1]}-{date2[2]}_{d_mask[i]}'
        day_mask.append([btn_txt, callback])

    return day_mask