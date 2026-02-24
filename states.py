# states.py
from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    user_id = State()
    door_id = State()
    checkin_date = State()
    checkout_date = State()
    checkin_pass = State()
    address = State()