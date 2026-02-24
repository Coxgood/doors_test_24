# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.



import calendar
import datetime
from datetime import date, datetime
import logging
import asyncio

from utils import (
    room_search,
    room_list,
    take_order,
    doors_search1,
    generate_password,
    qrcode_image,
    orders_list,
    check_timein,
    margin_day,
    new_order,
    del_order,
    )

from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Dispatcher, types, F

from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackData


bot = Bot('8505890066:AAFpwBViDkAIVytAJgGuwgel82vGRlhLmuo')
dp = Dispatcher()

config.MONTHS = ('херень','январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь')
name_weekdays = ('понедельник','вторник','среда','четверг','пятница','суббота','воскресенье')
signal_sign = ('🍎','🍏','🍑','📙','📗','📒','📓','🍀','🍁','🍂','⚪','❗','❕')


class UserAction(CallbackData, prefix="user"): action: str;  user_id: int
class Form(StatesGroup):
    user_id = State()
    door_id = State()
    checkin_date = State()
    checkout_date = State()
    checkin_pass = State()
    addres = State()



@dp.message(CommandStart())# ,F.data.startswith("start"))
async def cmd_start(message: Message, state: FSMContext):
    order_txt = ('order_' + str(message.from_user.id) )

    btn1 = InlineKeyboardButton(text="помещения", callback_data='start')
    btn2 = InlineKeyboardButton(text="регистрация", callback_data=order_txt)
    keyboard = InlineKeyboardMarkup(inline_keyboard = [[btn1,btn2]])
    await state.set_state(Form.door_id)
    await state.clear()
    await message.reply(f'Hi', reply_markup=keyboard)

@dp.callback_query(F.data.startswith("start"))
async def apartments_list1(callback: types.CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    await state.clear()
    btn = [[InlineKeyboardButton(text='календарь бронирования', callback_data=('order_'+user_id))]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=btn)
    await callback.message.answer(f'здраствуйте {str(callback.from_user.first_name)}', reply_markup=keyboard)

#  1 - бронирование выбор квартиры
@dp.callback_query(F.data.startswith("order_"))
async def apartments_list(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split("_")[1]  # Получаем id user
    list = room_list(user_id)
    await callback.answer()
    await state.update_data(user_id=user_id)
    await state.set_state(Form.door_id)
    buttons = []
    for door in list:
        callback1 = ('calendarCheckin_' + str(door[0]))
        btn = [InlineKeyboardButton(text=door[3], callback_data=callback1)]
        buttons.append(btn)
    key = ([InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Отмена", callback_data='start')])
    buttons.append(key)
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(f'выберите адрес', reply_markup=keyboard)

#  2 - календарь бронтрования
@dp.callback_query(F.data.startswith("calendarCheckin_"))
async def calendar_checkin(callback: types.CallbackQuery, state: FSMContext):
    door_id = int(callback.data.split("_")[1])  # id квартиры в БД
    await callback.answer()
    await state.update_data(door_id=door_id)
    months = orders_list(door_id)
    addres = room_search(door_id)[3]
    await state.update_data(addres=addres)
    for weeks in months:
        btnss=[]
        for week in weeks:
            btns = []
            #print('week------')
            for day in week:
                #print(f' {day[0]}', end ='')
                btn = (InlineKeyboardButton(text=str(day[0]), callback_data=str(day[1])))
                #await callback.message.answer(f' кнопки {day[0],day[1]}')
                btns.append(btn)
            btnss.append(btns)
        keyboard = InlineKeyboardMarkup(inline_keyboard=btnss)
        await callback.message.answer(text=f'{config.MONTHS[weeks[0][0][3]]}-{weeks[0][0][2]} ({addres}) дата заселения', reply_markup=keyboard)

    key = ([InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Отмена", callback_data='start')])
    keyboard1 = InlineKeyboardMarkup(inline_keyboard=[key])
    await callback.message.answer(f'0тменить ордер', reply_markup=keyboard1)

#  3 - выбор времени в частично занятый день
@dp.callback_query(F.data.startswith("checktimein_"))
async def chek_time_in(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = callback.data.split("_"); del data[0]
    mask = check_timein (data[0],data[1])
    date2 = data[0].split('-');mark = mask[0][1].split('_')[0]
    btns = []
    for m in mask:
        btn = (InlineKeyboardButton(text=m[0], callback_data=m[1]))
        btns.append(btn)
    if mark == 'checkoutday': del btns[0]
    key = ([InlineKeyboardButton(text='отменить ордер', callback_data='start')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[btns,key])
    await callback.message.answer(text=f"выберете время заселения {date2[2]}-{config.MONTHS[int(date2[1])]}-{date2[0]}", reply_markup=keyboard)


#  4 - check out day
@dp.callback_query(F.data.startswith("checkoutday_"))
async def chekout_date(callback: types.CallbackQuery, state: FSMContext):
    checkin_day = callback.data.split("_"); del checkin_day[0]
    await callback.answer()

    checkin_date = datetime(int(checkin_day[0]), int(checkin_day[1]), int(checkin_day[2]), int(checkin_day[3]))
    data = await state.get_data()
    await state.update_data(checkin_date=checkin_date)
    months = margin_day(checkin_day, data['door_id'])#data['door_id']

    for weeks in months:
        btnss=[]
        for week in weeks:
            btns = []
            for day in week:
                btn = (InlineKeyboardButton(text=str(day[0]),   callback_data=str(day[1])))
                btns.append(btn)
            btnss.append(btns)
        keyboard = InlineKeyboardMarkup(inline_keyboard=btnss)
        await callback.message.answer(text=f' {config.MONTHS[weeks[0][0][3]]}-{weeks[0][0][2]} (заселение {checkin_date}). выбирете дату выселения', reply_markup=keyboard)

    key = ([InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Отмена", callback_data='start')])
    keyboard1 = InlineKeyboardMarkup(inline_keyboard=[key])
    await callback.message.answer(f'0тменить ордер', reply_markup=keyboard1)


#  5 - check out time
@dp.callback_query(F.data.startswith("checkouttime_"))
async def checkout_time(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = callback.data.split("_"); del data[0]; btns = []
    time = (8,12,18,22); time1 = ('08:00', '12:00', '18:00', '22:00'); time2 = ('8:00❕', '12:00❕', '18:00❕', '22:00❕')
    for i in range(0,4):
        if int(data[1]) < time[i] <= int(data[2]):
            btn = (InlineKeyboardButton(text=time1[i], callback_data=f'orderchek_{data[0]} {time1[i]}'))
        else:
            btn = (InlineKeyboardButton(text=time2[i], callback_data='donttouchthis'))
        btns.append(btn)
    key = ([InlineKeyboardButton(text='отменить ордер', callback_data='start')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[btns,key])
    await callback.message.answer(text=f"выберете время заселения", reply_markup=keyboard )


@dp.callback_query(F.data.startswith("orderchek_"))
async def order_chek(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data1 = callback.data.split("_"); del data1[0]
    dt_chekout = datetime.strptime(data1[0], "%Y-%m-%d %H:%M")

    await state.update_data(checkout_date=dt_chekout)
    qr_code = generate_password()
    await state.update_data(checkin_pass=qr_code)
    data = await state.get_data()

    btn1 = (InlineKeyboardButton(text='да', callback_data='accept_order'))
    btn2 = (InlineKeyboardButton(text='нет', callback_data='start'))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2]])

    delta_time = data['checkout_date'] - data['checkin_date']
    await callback.message.answer(text=f"адрес  ({data['addres']})\nзаселение {data['checkin_date']} \nвыселение {data['checkout_date']} \nприбывание {delta_time} \n подтвердить бронирование", reply_markup=keyboard)


# 6 order accepting
@dp.callback_query(F.data.startswith("accept_order"))
async def accept_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curren_date = str(datetime.now())
    room_addres = data['addres'] #  ; addres= room_addres[3]
    qr_code = data['checkin_pass']
    qrcode_image(qr_code)
    photo = FSInputFile('qrcode.png')
    order_info = (curren_date, int(data['user_id']),
                  data['door_id'],
                  data['checkin_date'].strftime("%d-%m-%Y %H:%M"),
                  data['checkout_date'].strftime("%d-%m-%Y %H:%M"),
                  data['checkin_pass'],
                  'description')
    new_order(order_info)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[(InlineKeyboardButton(text=f"{config.EMOJI['apartment']} К началу", callback_data='start'))]])
    delta_date = data['checkout_date'] - data['checkin_date']
    await callback.message.answer_photo(
        photo=photo,
        caption=f"адрес  ({room_addres})\nзаселение {data['checkin_date']} \nвыселение {data['checkout_date']} \nприбывание {delta_date}\n",
        reply_markup=keyboard)


# 6 order info получение информации по существующему ордеру
@dp.callback_query(F.data.startswith("orderinfo_"))
async def orderinfo(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    order_id = callback.data.split("_")[2]  # id квартиры в БД
    await state.clear()
    order = take_order(order_id)
    addres = doors_search1(order[3])[3]

    qr_code = order[6]
    qrcode_image(qr_code)
    photo = FSInputFile('qrcode.png')
    btn1 = InlineKeyboardButton(text='❗удалить ордер❗', callback_data=f'delorder_{order_id}')
    btn2 = InlineKeyboardButton(text='открыть дверь', callback_data='start')
    btn3 = InlineKeyboardButton(text=f"{config.EMOJI['apartment']} К началу", callback_data='start')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1,btn2],[btn3]])
    await state.clear()
    chekintime = datetime.strptime((order[4]), "%d-%m-%Y %H:%M")
    chekouttime = datetime.strptime((order[5]), "%d-%m-%Y %H:%M")
    delta_date = chekouttime - chekintime

    await callback.message.answer_photo(
        photo=photo,
        caption=f"адрес {addres} \nзаселение {order[4]} \nвыселение {order[5]} \nприбывание {delta_date}\n",
        reply_markup=keyboard)


# удаление ордера
@dp.callback_query(F.data.startswith("delorder_"))
async def delorder(callback: types.CallbackQuery):
    await callback.answer()
    order_id = callback.data.split("_")[1]  # id квартиры в БД
    btn1 = InlineKeyboardButton(text='❗   ДА   ❗', callback_data=f'delorder1_{order_id}')
    btn2 = InlineKeyboardButton(text='нет', callback_data='start')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2]])
    await callback.message.answer(text=f" УДАЛЕНИЕ ОРДЕРА", reply_markup=keyboard)

# удаление ордера
@dp.callback_query(F.data.startswith("delorder1_"))
async def delorder1(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]  # id квартиры в БД
    del_order(order_id)
    btn1 = InlineKeyboardButton(text=f"{config.EMOJI['apartment']} К началу", callback_data='start')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1]])
    await callback.message.answer(text=f" одер удален ", reply_markup=keyboard)

# заглушка на пустую дату
@dp.callback_query(F.data == "donttouchthis")
async def process_callback_delete(callback: CallbackQuery):
    await callback.answer(text="❗ЧТО ТУТ У ВАС ПРОИСХОДИТ!!???❗", show_alert=False)


async def main():
    await dp.start_polling(bot)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')
