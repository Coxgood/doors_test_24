# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.



import calendar
import datetime
from datetime import date, datetime
import logging
import asyncio

from utils1 import (
    doors_search,
    user_search,
    generate_password,
    del_order,
    new_order,
    doors_search1,
    qrcode_image,
    orders_list,
    take_order,
    chek_timein,
    back_time,
    margin_day)

from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Dispatcher, types, F

from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.filters.callback_data import CallbackData


bot = Bot('8505890066:AAFpwBViDkAIVytAJgGuwgel82vGRlhLmuo')
dp = Dispatcher()

name_months = ('херень','январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь')
name_weekdays = ('понедельник','вторник','среда','четверг','пятница','суббота','воскресенье')
signal_sign = ('🍎','🍏','🍑','📙','📗','📒','📓','🍀','🍁','🍂','⚪','❗','❕')


class UserAction(CallbackData, prefix="user"): action: str;  user_id: int
class Form(StatesGroup):
    user_id = State()
    door_id = State()
    chekin_date = State()
    chekout_date = State()
    chekin_pass = State()



@dp.message(CommandStart())# ,F.data.startswith("start"))
async def cmd_start(message: Message, state: FSMContext):
    order_txt = ('order_' + str(message.from_user.id) )
    buttons = [[InlineKeyboardButton(text="order", callback_data=order_txt)]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    status = user_search(message.from_user.id)
    #print(status)
    await state.set_state(Form.door_id)
    await state.clear()
    await message.reply(f'Hi', reply_markup=keyboard)
    #await message.reply(f'Hi {status[6]} {message.from_user.first_name} {message.from_user.id}', reply_markup=keyboard)

@dp.callback_query(F.data.startswith("start"))
async def apartments_list1(callback: types.CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    await state.clear()
    cb_text = ('order_'+user_id)
    btn = [[InlineKeyboardButton(text='календарь бронирования', callback_data=cb_text)]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=btn)
    await callback.message.answer(f'здраствуйте {str(callback.from_user.first_name)}', reply_markup=keyboard)


#  1 - бронирования выбор квартиры
@dp.callback_query(F.data.startswith("order_"))
async def apartments_list(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.data.split("_")[1]  # Получаем id user
    list = doors_search(user_id)
    await callback.answer()
    await state.update_data(user_id=user_id)
    await state.set_state(Form.door_id)
    buttons = []
    for door in list:
        callback1 = ('chekinday_' + str(door[0]))
        btn = [InlineKeyboardButton(text=door[3], callback_data=callback1)]
        buttons.append(btn)
    key = ([InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Отмена", callback_data='start')])
    buttons.append(key)
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(f'выберите адрес {user_id}', reply_markup=keyboard)


#  2 - check in day
@dp.callback_query(F.data.startswith("chekinday_"))
async def chekin_date(callback: types.CallbackQuery, state: FSMContext):
    door_id = int(callback.data.split("_")[1])  # id квартиры в БД
    await callback.answer()
    await state.update_data(door_id=door_id)
    months=orders_list(door_id)
    address = doors_search1(door_id)[3]
    for weeks in months:
        btnss=[]
        for week in weeks:
            btns = []
            #print('week------')
            for day in week:
                #print(f' {day[0]}', end ='')
                btn = (InlineKeyboardButton(text=str(day[0]),   callback_data=str(day[1])))
                #await callback.message.answer(f' кнопки {day[0],day[1]}')
                btns.append(btn)
            btnss.append(btns)
        keyboard = InlineKeyboardMarkup(inline_keyboard=btnss)
        await callback.message.answer(text=f'{config.MONTHS[weeks[0][0][3]]}-{weeks[0][0][2]} {address} дата заселения', reply_markup=keyboard)

    key = ([InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Отмена", callback_data='start')])
    keyboard1 = InlineKeyboardMarkup(inline_keyboard=[key])
    await callback.message.answer(f'0тменить ордер', reply_markup=keyboard1)


# заглушка на пустую дату
@dp.callback_query(F.data == "donttouchthis")
async def process_callback_delete(callback: CallbackQuery):
    await callback.answer(text="❗ЧТО ТУТ У ВАС ПРОИСХОДИТ!!???❗", show_alert=False)



#  3 - check in time
@dp.callback_query(F.data.startswith("chekintime_"))
async def chekin_time(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    date1 = callback.data.split("_")
    date = date1[1].split("-")

    times = ('8:00','12:00','18:00','22:00'); btns = []
    for time in times:
        hour_min = time.split(":")
        btn = (InlineKeyboardButton(text=time, callback_data='chekoutday_'+ date[0]+'_'+date[1]+'_'+date[2]+'_'+hour_min[0])); btns.append(btn)
    key = ([InlineKeyboardButton(text='отмена ордера', callback_data='start')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[btns,key])
    await callback.message.answer(text=f"выберете время заселения {date[2]}-{config.MONTHS[int(date[1])]}-{date[0]}", reply_markup=keyboard)



#  3 - выбор времени в частично занятый день
@dp.callback_query(F.data.startswith("chektimein_"))
async def chek_time_in(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = callback.data.split("_"); del data[0]
    mask = chek_timein (data[0],data[1])

    print(f'mask{mask}')

    btn1 = [(InlineKeyboardButton(text=mask[0][0], callback_data=mask[0][1]))]
    btn2 = [(InlineKeyboardButton(text=mask[1][0], callback_data=mask[1][1]))]
    btn3 = [(InlineKeyboardButton(text=mask[2][0], callback_data=mask[2][1]))]
    btn4 = [(InlineKeyboardButton(text=mask[3][0], callback_data=mask[3][1]))]
    btn5 = [(InlineKeyboardButton(text=mask[4][0], callback_data=mask[4][1]))]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[btn1,btn2,btn3,btn4,btn5])


    await callback.message.answer(text=f"выберете время заселения", reply_markup=keyboard)
    key = ([InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Отмена", callback_data='start')])
    keyboard1 = InlineKeyboardMarkup(inline_keyboard=[key])
    await callback.message.answer(f'0тменить ордер', reply_markup=keyboard1)


#  4 - check out day
@dp.callback_query(F.data.startswith("chekoutday_"))
async def chekout_date(callback: types.CallbackQuery, state: FSMContext):
    chekin_day = callback.data.split("_"); del chekin_day[0]
    await callback.answer()


    chekin_date = datetime(int(chekin_day[0]), int(chekin_day[1]), int(chekin_day[2]), int(chekin_day[3]))
    data = await state.get_data()
    await state.update_data(chekin_date=chekin_date)

    months = margin_day(chekin_day, data['door_id'])#data['door_id']

    for weeks in months:
        btnss=[]
        for week in weeks:
            btns = []
            #print('week------')
            for day in week:
                #print(f' {day[0]}', end ='')
                btn = (InlineKeyboardButton(text=str(day[0]),   callback_data=str(day[1])))
                #await callback.message.answer(f' кнопки {day[0],day[1]}')
                btns.append(btn)
            btnss.append(btns)
        keyboard = InlineKeyboardMarkup(inline_keyboard=btnss)
        await callback.message.answer(text=f' {config.MONTHS[weeks[0][0][3]]}-{weeks[0][0][2]} (заселение {chekin_date}). выбирете дату выселения', reply_markup=keyboard)

    key = ([InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Отмена", callback_data='start')])
    keyboard1 = InlineKeyboardMarkup(inline_keyboard=[key])
    await callback.message.answer(f'0тменить ордер', reply_markup=keyboard1)



#  5 - check out time
@dp.callback_query(F.data.startswith("chekouttime_"))
async def chekout_time(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = callback.data.split("_"); del data[0]
    date = data[0].split("-")
    times = ('8:00','12:00','18:00','22:00'); btns = []
    for time in times:
        hour_min = time.split(":")
        btn = (InlineKeyboardButton(text=time, callback_data='orderchek_'+ date[0]+'_'+date[1]+'_'+date[2]+'_'+hour_min[0])); btns.append(btn)
    key = ([InlineKeyboardButton(text='отмена ордера', callback_data='start')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[btns, key])
    await callback.message.answer(text=f"выберете время заселения {date[2]}-{config.MONTHS[int(date[1])]}-{date[0]}", reply_markup=keyboard)


#  5 - check out time выбор временив выселения в частично занятый день
@dp.callback_query(F.data.startswith("chektimeout_"))
async def chek_timeout(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    data = callback.data.split('_'); del data[0]
    date1 = data[0].split(' '); date = date1[0].split('-')
    clock =int(str(date1[1].split(':')[0]))
    state = await state.get_data()# data['door_id']
    bt = back_time(data, state['door_id'])

    print (f'bt __{bt} clock __{clock}')
    times = ('8:00','12:00','18:00','22:00'); btns = []
    for time in times:
        if bt <= int(time.split(':')[0]) <= clock:
            hour_min = time.split(":")
            btn = (InlineKeyboardButton(text=time, callback_data='orderchek_'+ date[0]+'_'+date[1]+'_'+date[2]+'_'+hour_min[0])); btns.append(btn)


    key = ([InlineKeyboardButton(text='отмена ордера', callback_data='start')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[btns, key])


    await callback.message.answer(text=f"выберете время заселения {date[2]}-{config.MONTHS[int(date[1])]}-{date[0]}", reply_markup=keyboard)


# 6 order cheking проверка ордера получение QR
@dp.callback_query(F.data.startswith("orderchek_"))
async def order_chek(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    chekout_day = callback.data.split("_"); del chekout_day[0]
    dt_chekout = datetime(int(chekout_day[0]), int(chekout_day[1]), int(chekout_day[2]), int(chekout_day[3]))

    await state.update_data(chekout_date=dt_chekout)
    qr_code = generate_password()
    await state.update_data(chekin_pass=qr_code)

    btn1 = (InlineKeyboardButton(text='да' , callback_data='accept_order'))
    btn2 = (InlineKeyboardButton(text='нет', callback_data='start'))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1,btn2]])
    data = await state.get_data()
    room_address = doors_search1(data['door_id'])
    delta_time = data['chekout_date'] - data['chekin_date']
    await callback.message.answer(text=f"адрес  ({room_address[3]})\nзаселение {data['chekin_date']} \nвыселение {data['chekout_date']} \nприбывание {delta_time}\n подтвердить бронирование", reply_markup=keyboard)


# 6 order info получение информации по существующему ордеру
@dp.callback_query(F.data.startswith("orderinfo_"))
async def orderinfo(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    order_id = callback.data.split("_")[2]  # id квартиры в БД
    print(f'order_id {callback.data}')
    await state.clear()
    order = take_order(order_id)
    address = doors_search1(order[3])[3]

    qr_code = order[6]
    qrcode_image(qr_code)
    photo = FSInputFile('../qrcode.png')
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
        caption=f"адрес {address} \nзаселение {order[4]} \nвыселение {order[5]} \nприбывание {delta_date}\n",
        reply_markup=keyboard)


@dp.callback_query(F.data.startswith("delorder_"))
async def delorder(callback: types.CallbackQuery):
    await callback.answer()
    order_id = callback.data.split("_")[1]  # id квартиры в БД
    btn1 = InlineKeyboardButton(text='❗   ДА   ❗', callback_data=f'delorder1_{order_id}')
    btn2 = InlineKeyboardButton(text='нет', callback_data='start')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2]])
    await callback.message.answer(text=f" УДАЛЕНИЕ ОРДЕРА", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("delorder1_"))
async def delorder1(callback: types.CallbackQuery):
    order_id = callback.data.split("_")[1]  # id квартиры в БД
    del_order(order_id)
    btn1 = InlineKeyboardButton(text=f"{config.EMOJI['apartment']} К началу", callback_data='start')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1]])
    await callback.message.answer(text=f" одер удален ", reply_markup=keyboard)





# 6 order accepting
@dp.callback_query(F.data.startswith("accept_order"))
async def accept_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    curren_date = str(datetime.now())
    room_address = doors_search1(data['door_id'])#  ; address= room_address[3]


    qr_code = data['chekin_pass']
    qrcode_image(qr_code)
    photo = FSInputFile('../qrcode.png')
    order_info = (curren_date, int(data['user_id']), data['door_id'], data['chekin_date'].strftime("%d-%m-%Y %H:%M"), data['chekout_date'].strftime("%d-%m-%Y %H:%M"), data['chekin_pass'], 'description')

    new_order(order_info)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[(InlineKeyboardButton(text=f"{config.EMOJI['apartment']} К началу", callback_data='start'))]])
    await state.clear()
    delta_date = data['chekout_date'] - data['chekin_date']
    await callback.message.answer_photo(
        photo=photo,
        caption=f"адрес  ({room_address[3]})\nзаселение {data['chekin_date']} \nвыселение {data['chekout_date']} \nприбывание {delta_date}\n",
        reply_markup=keyboard)





async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')
