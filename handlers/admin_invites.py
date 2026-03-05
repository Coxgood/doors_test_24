# handlers/admin_invites.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import random
import string
from datetime import datetime, timedelta

import config
from database import create_invite, check_invite, use_invite, get_connection, get_user_id_by_telegram

router = Router()


def generate_invite_code(length=8):
    """Генерирует уникальный код приглашения"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ====== ПОДТВЕРЖДЕНИЕ ПРИГЛАШЕНИЯ ======
@router.callback_query(F.data.startswith("confirm_invite_"))
async def confirm_invite(callback: CallbackQuery, user_role: str):
    """Подтверждение создания инвайта"""

    role = callback.data.replace("confirm_invite_", "")

    # Проверка прав
    if role == 'admin' and user_role != 'root':
        await callback.answer("❌ Только ROOT может приглашать админов", show_alert=True)
        return

    if role == 'owner' and user_role not in ['root', 'admin']:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    role_names = {
        'admin': '👑 Администратор',
        'owner': '🏠 Владелец',
        'manager': '📋 Менеджер',
        'cleaner': '🧹 Клинер',
        'installer': '🔧 Инсталлер'
    }

    role_name = role_names.get(role, role)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"create_invite_{role}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="users_menu")
    ]])

    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение</b>\n\n"
        f"Вы собираетесь создать приглашение для:\n"
        f"{role_name}\n\n"
        f"✅ Ссылка будет действительна 1 день\n"
        f"🔐 Использовать можно только 1 раз",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ====== СОЗДАНИЕ ПРИГЛАШЕНИЯ (УЛУЧШЕННАЯ ВЕРСИЯ) ======
@router.callback_query(F.data.startswith("create_invite_"))
async def create_invite_handler(callback: CallbackQuery, user_role: str):
    """Создание приглашения"""

    role = callback.data.replace("create_invite_", "")

    # Проверка прав
    if role == 'admin' and user_role != 'root':
        await callback.answer("❌ Только ROOT может приглашать админов", show_alert=True)
        return

    if role == 'owner' and user_role not in ['root', 'admin']:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    # Генерируем код
    code = generate_invite_code()
    expires_at = datetime.now() + timedelta(days=1)

    # Получаем внутренний ID пользователя
    user_id = get_user_id_by_telegram(callback.from_user.id)
    if not user_id:
        await callback.answer("❌ Ошибка: пользователь не найден", show_alert=True)
        return

    # Сохраняем в БД
    create_invite(code, user_id, role, expires_at.strftime('%Y-%m-%d %H:%M:%S'))

    bot_username = (await callback.bot.get_me()).username
    print(f"🔍 bot_username = {bot_username}")  # для отладки
    if not bot_username:
        bot_username = "doortest8716_bot"  # запасной вариант

    bot_username = (await callback.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={code}"
    expires_str = expires_at.strftime("%d.%m.%Y %H:%M")

    role_names = {
        'admin': '👑 Администратор',
        'owner': '🏠 Владелец',
        'manager': '📋 Менеджер',
        'cleaner': '🧹 Клинер',
        'installer': '🔧 Инсталлер'
    }

    # Удаляем предыдущее сообщение с подтверждением
    await callback.message.delete()

    # Вместо обычной ссылки — кнопки для отправки
    await callback.message.answer(
        f"✅ <b>ПРИГЛАШЕНИЕ СОЗДАНО</b>\n\n"
        f"{role_names.get(role, role)}\n"
        f"📅 Действителен до: {expires_str}\n\n"
        f"👇 <b>Отправьте ссылку приглашаемому:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[

            # Кнопка для отправки другу (открывает список чатов)
            [InlineKeyboardButton(text="📤 Отправить приглашение", switch_inline_query=invite_link)],

            # Кнопки навигации
            [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="users_menu")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="start")]
        ])
    )

    await callback.answer()


# ====== ЗАГЛУШКИ ДЛЯ БУДУЩИХ РОЛЕЙ ======
@router.callback_query(F.data == "invite_manager_soon")
async def invite_manager_soon(callback: CallbackQuery):
    """Приглашение менеджера (заглушка)"""
    await callback.answer(
        "🚧 Функция в разработке\nМенеджеры появятся позже",
        show_alert=True
    )


@router.callback_query(F.data == "invite_cleaner_soon")
async def invite_cleaner_soon(callback: CallbackQuery):
    """Приглашение клинера (заглушка)"""
    await callback.answer(
        "🧹 Клинеры будут доступны\nпосле внедрения системы уборки",
        show_alert=True
    )


@router.callback_query(F.data == "invite_installer_soon")
async def invite_installer_soon(callback: CallbackQuery):
    """Приглашение инсталлера (заглушка)"""
    await callback.answer(
        "🔧 Инсталлеры появятся\nна этапе установки ESP32",
        show_alert=True
    )


# ====== МЕНЮ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ ======
@router.callback_query(F.data == "users_menu")
async def users_menu_handler(callback: CallbackQuery, user_role: str):
    """Меню управления пользователями"""

    if user_role not in ['root', 'admin']:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    is_root = (user_role == 'root')

    buttons = []

    if is_root:
        buttons.append([InlineKeyboardButton(
            text="👑 Пригласить администратора",
            callback_data="confirm_invite_admin"
        )])

    buttons.append([InlineKeyboardButton(
        text="🏠 Пригласить собственника",
        callback_data="confirm_invite_owner"
    )])

    buttons.append([InlineKeyboardButton(
        text="📋 Пригласить менеджера",
        callback_data="invite_manager_soon"
    )])

    buttons.append([InlineKeyboardButton(
        text="🧹 Пригласить клинера",
        callback_data="invite_cleaner_soon"
    )])

    buttons.append([InlineKeyboardButton(
        text="📋 Мои приглашения",
        callback_data="my_invites"
    )])

    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="start"
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n"
        f"Выберите роль для приглашения:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
