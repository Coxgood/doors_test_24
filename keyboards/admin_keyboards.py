# keyboards/admin_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config


def admin_panel_keyboard(is_root: bool = False):
    buttons = []

    if is_root:
        buttons.append([InlineKeyboardButton(
            text="➕ Пригласить администратора",
            callback_data="invite_admin"
        )])
        # Новая кнопка для управления пользователями
        buttons.append([InlineKeyboardButton(
            text="📋 Управление пользователями",
            callback_data="user_management"
        )])

    buttons.append([InlineKeyboardButton(
        text="➕ Пригласить собственника",
        callback_data="invite_owner"
    )])

    buttons.append([InlineKeyboardButton(
        text="📋 Мои приглашения",
        callback_data="my_invites"
    )])

    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="start"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
