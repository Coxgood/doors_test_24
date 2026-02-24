
import random
import string
from calendar import month
import qrcode
import sqlite3
import asyncio
import calendar
import datetime
from datetime import date, datetime, timedelta


def generate_password(length=12): # гененрируем пароль доступа
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def qrcode_image(password):# гененрируем картинку QR
    img = qrcode.make(password)
    type(img)
    img.save("qrcode.png")

def user_search (user_id_n):# поиск пользователя по БД
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    line = ("SELECT * FROM users WHERE door_id = '" + str(user_id_n) + "'")
    cursor.execute(line)
    user_info = (cursor.fetchone())
    db.commit()
    return (user_info)
    #user_search(message.from_user.id)

def room_list (user_id_n):# поиск пользователя по БД
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    line = ("SELECT * FROM doors WHERE user_id = '" + str(user_id_n) + "'")
    cursor.execute(line)
    doors_info = (cursor.fetchall())
    db.commit()
    return (doors_info)

def room_search (door_id_n):# поиск пользователя по БД
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    line = ("SELECT * FROM doors WHERE door_id = '" + str(door_id_n) + "'")
    cursor.execute(line)
    doors_info = (cursor.fetchone())
    db.commit()
    return (doors_info)

def doors_search1 (door_id_n):# поиск пользователя по БД
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    line = ("SELECT * FROM doors WHERE door_id = '" + str(door_id_n) + "'")
    cursor.execute(line)
    doors_info = (cursor.fetchone())
    db.commit()
    return (doors_info)

def take_order (order_id):
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    cursor.execute("SELECT * FROM orders_book WHERE id='"+ str(order_id) + "'")
    db.commit()
    order = (cursor.fetchone())
    return (order)

def del_order(order_id):
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    cursor.execute("DELETE FROM orders_book WHERE id =" + str(order_id))
    db.commit()

def new_order (order_info):
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    cursor.execute("INSERT INTO orders_book (date_time,user_id,room_id,date_chekin,date_chekout,qr_code,description) VALUES"  + str(order_info))
    db.commit()


def margin_day(chekin, room_id):
    # chekin_date = datetime(2026, 3, 02)

    str_date = (f'{chekin[0]}-{chekin[1]}-{chekin[2]} {chekin[3]}:00')
    chekin_date = datetime.strptime(str_date, '%Y-%m-%d %H:%M')

    # выгрузка ордеров с DB
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    line = ("SELECT * FROM orders_book WHERE room_id = '" + str(room_id) + "'")
    cursor.execute(line)
    ord_reqDB = (cursor.fetchall())
    db.commit()
    margin_date = datetime(3970, 1, 1)


    # определение крайней даты регистрации даты выселени
    if len(ord_reqDB) > 0:
        inday_list = []
        for ord in ord_reqDB:
            inday2 = [ord[0],datetime.strptime(ord[4], "%d-%m-%Y %H:%M")]
            inday_list.append(inday2)
        inday_list = sorted(inday_list, key=lambda x: x[1])
        for inday in inday_list:
            if inday[1] >= chekin_date: margin_date = inday[1]; break
    else: margin_date = datetime(3970, 1, 1)

    b_date = datetime.strptime(str(chekin_date), "%Y-%m-%d %H:%M:%S")
    e_date = datetime.strptime(str(margin_date), "%Y-%m-%d %H:%M:%S")
    b1_date = b_date.replace(hour=0, minute=0, second=0, microsecond=0).date()
    e1_date = e_date.replace(hour=0, minute=0, second=0, microsecond=0).date()

    # формируем календарь с крайней датой выселения
    if chekin_date.day > 16: m = 1;
    else: m = 0
    cal = calendar.Calendar(firstweekday=0)
    months = []
    for i in range(0, 3 + m):
        month1 = chekin_date.month + i; year1 = chekin_date.year
        if month1 > 12: year1 = year1 + 1; month1 = 1;
        weeks1 = cal.monthdatescalendar(year1, month1); weeks = []
        for week1 in weeks1:
            week = []
            for day1 in week1:
                if day1 == b1_date: b_hour = chekin_date.hour;
                else: b_hour = 2
                btn_txt = (f'  {str(day1.day)}   ')
                callback = ('checkouttime_' + str(day1) + '_' + str(b_hour) + '_23')
                day = (btn_txt, callback, year1, month1)
                if day1.month != month1: day = [' ', 'donttouchthis', year1, month1]
                if day1 > margin_date.date() : day = [' ', 'donttouchthis', year1, month1]
                if day1 <  chekin_date.date(): day = [' ', 'donttouchthis', year1, month1]
                if day1 == margin_date.date():
                    if day1 == b1_date: b_hour = chekin_date.hour;
                    else: b_hour = 2
                    btn_txt = (f'  {str(day1.day)}❕  ')
                    callback = ('checkouttime_' + str(day1) + '_' + str(b_hour) + '_' + str(margin_date.hour))
                    day = (btn_txt, callback, year1, month1)

                week.append(day)
            if week1[6] >= chekin_date.date() and  week1[0] <= margin_date.date(): weeks.append(week)
        if weeks1[0][0] < margin_date.date(): months.append(weeks)
        #for q in weeks: print(f'q_______{q}')
    return (months)


def check_timein(date1, room_id):

    date1 = date1.split(' ')[0]
    #date2 = [2026, 2, 13]
    date2 = date1.split('-')
    date = datetime.strptime(date1, '%Y-%m-%d')

    checkout_mask  = [[1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [1, 1, 1, 0, 0], [1, 1, 1, 1, 0]]
    checkin_mask   = [[0, 1, 1, 1, 1], [0, 0, 1, 1, 1], [0, 0, 0, 1, 1], [0, 0, 0, 0, 1]]

    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    line = ("SELECT * FROM orders_book WHERE room_id = '" + str(room_id) + "'")
    cursor.execute(line)
    ord_reqDB = (cursor.fetchall())
    db.commit()

    orders = []# из выборки ордеров из DB оставляем только те chekin или chekout попадают на эту дату
    for order in ord_reqDB:

        chekin_date = datetime.strptime(order[4], "%d-%m-%Y %H:%M")
        chekout_date = datetime.strptime(order[5], "%d-%m-%Y %H:%M")
        ord = (order[0], chekin_date, chekout_date, 0)

        if chekin_date.date() == date.date(): orders.append(ord)
        elif chekout_date.date() == date.date(): orders.append(ord)
        elif chekout_date.date() == chekin_date.date() == date.date(): orders.append(ord)
    orders = sorted(orders, key=lambda x: x[1])

    orders1 = []
    for order in orders:
        chekin_date = order[1]; chekout_date = order[2]
        h_in = str((str(order[1]).split(' '))[1]).split(':')[0]
        h_ou = str((str(order[2]).split(' '))[1]).split(':')[0]

        if chekin_date.date() == date.date():
            if h_in == '08': mask =checkin_mask[0]
            if h_in == '12': mask =checkin_mask[1]
            if h_in == '18': mask =checkin_mask[2]
            if h_in == '22': mask =checkin_mask[3]
            #print(f'CHEK-IN -- {mask}')
        if chekout_date.date() == date.date():
            if h_ou == '08': mask =checkout_mask[0]
            if h_ou == '12': mask =checkout_mask[1]
            if h_ou == '18': mask =checkout_mask[2]
            if h_ou == '22': mask =checkout_mask[3]
            #print(f'CHEK-OUT-- {mask}')

        if chekin_date.date() == chekout_date.date() == date.date():
            if h_in == '08': mask1 = checkin_mask[0]
            if h_in == '12': mask1 = checkin_mask[1]
            if h_in == '18': mask1 = checkin_mask[2]
            if h_in == '22': mask1 = checkin_mask[3]
            if h_ou == '08': mask2 =checkout_mask[0]
            if h_ou == '12': mask2 =checkout_mask[1]
            if h_ou == '18': mask2 =checkout_mask[2]
            if h_ou == '22': mask2 =checkout_mask[3]
            mask = []
            for i in range (0,5): mask.append(mask1[i]*mask2[i])
        for i in range(0, 5): mask[i] = mask[i] * order[0]
        ord = (order[0], order[1], order[2], mask)
        orders1.append(ord)
    d_mask = [0, 0, 0, 0, 0]
    day_mask = [0, 0, 0, 0, 0]

    for order in orders1:
        for i in range(0, 5):
            d_mask[i] = d_mask[i] + order[3][i]
    time_marker1 = ('00:00>08:00','08:00','12:00','18:00','22:00')
    time_marker2 = ('>08:00❗','08:00❗','12:00❗','18:00❗','22:00❗')
    callback_time = ('00','08','12','18','22')

    for i in range (0,5):
        if d_mask[i] == 0:
            btn_txt = time_marker1[i]
            callback = f'checkoutday_{date2[0]}_{date2[1]}_{date2[2]}_{callback_time[i]}'
        if d_mask[i] !=  0:
            btn_txt = time_marker2[i]
            callback = f'orderinfo_{date2[0]}-{date2[1]}-{date2[2]}_{d_mask[i]}'
        day_mask[i] = [btn_txt,callback]
    return (day_mask)


def orders_list(room_id):
    # запрос ордеров в DB
    db = sqlite3.connect('doors_ctrl_test.db')
    cursor = db.cursor()  # курсор
    line = ("SELECT * FROM orders_book WHERE room_id = '" + str(room_id) + "'")
    cursor.execute(line)
    ord_reqDB = (cursor.fetchall())
    db.commit()

    # раскладка ордеров по занятым дням
    start_day = date.today()
    ordes_list = []
    for reqest in ord_reqDB:
        inday =  datetime.strptime((reqest[4]), "%d-%m-%Y %H:%M")
        outday = datetime.strptime((reqest[5]), "%d-%m-%Y %H:%M")
        inday1 =  inday.replace (hour=0, minute=0, second=0, microsecond=0)
        outday1 = outday.replace(hour=0, minute=0, second=0, microsecond=0)
        delta_time = (outday1 - inday1).days
        cur_day = inday.date()

        for i in range(1, delta_time+2):
            if 1 < i < delta_time+1:  btn_txt = (f'{str(cur_day.day)}❗'); callback = ('orderinfo_'   + str(cur_day)+"_"+str(reqest[0]))
            if i == 1:                btn_txt = (f'{str(cur_day.day)}❕'); callback = ('checktimein_' + str(cur_day)+"_"+str(reqest[3]))
            if i == delta_time+1:     btn_txt = (f'{str(cur_day.day)}❕'); callback = ('checktimein_' + str(cur_day)+"_"+str(reqest[3]))

            ordes_list.append([cur_day,(reqest[0]),btn_txt, callback])
            cur_day = inday.date() + timedelta(days=i)

    ordes_list = sorted(ordes_list, key=lambda x: x[0])

    # раскладка ордеров в недельный календарь
    if start_day.day > 16: m = 1
    else: m = 0
    cal = calendar.Calendar(firstweekday=0)
    ordes_list.append([(datetime(1970, 1, 1)), 0, 4])
    months = []
    for i in range(0, 3 + m):
        month1 = start_day.month + i; year1 = start_day.year
        if month1 > 12: year1 = year1 + 1; month1 = 1;
        weeks1 = cal.monthdatescalendar(year1, month1); weeks = []
        for week1 in weeks1:
            week = []
            for day1 in week1:
                j = 0; day=[]
                for day2 in ordes_list:
                    btn_txt = (f'  {str(day1.day)}   ')
                    callback = ('checktimein_' + str(day1)+"_"+str(room_id))
                    #callback = ('checktimein_' + str(day1)+"_"+str(reqest[3]))
                    day = (btn_txt, callback, year1, month1)
                    if day1 == day2[0] and month1 == day2[0].month :
                        day = (day2[2],day2[3], year1 ,month1)
                        del ordes_list[j]; break
                    if day1.month != month1: day = [' ', 'donttouchthis', year1, month1]
                    if start_day > day1    : day = [' ', 'donttouchthis', year1, month1]
                    j = j + 1
                week.append(day)
            if week1[6] >= start_day: weeks.append(week)
        months.append(weeks)
    return (months)
