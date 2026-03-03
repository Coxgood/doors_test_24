# handlers/admin_invites.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton  # 👈 добавить
from aiogram.filters import Command
import random
import string
from datetime import datetime, timedelta

import config
from database import create_invite, check_invite, use_invite, get_connection


router = Router()


def generate_invite_code(length=8):
    """Генерирует уникальный код приглашения"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))



# ====== ВХОД В АДМИН-ПАНЕЛЬ ======
@router.message(Command("admin"))
@router.message(F.text == "👑 Админ-панель")
async def cmd_admin(message: Message, user_role: str):
    if user_role not in ['root', 'admin']:
        await message.answer(f"{config.EMOJI['warning']} У вас нет доступа.")
        return

    is_root = (user_role == 'root')
    await message.answer(
        f"{config.EMOJI['admin']} <b>Админ-панель</b>\n\n"
        f"Ваша роль: {user_role}",
        reply_markup=admin_panel_keyboard(is_root),
        parse_mode="HTML"
    )


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
        InlineKeyboardButton(text="❌ Отмена", callback_data="invites_menu")
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


# ====== СОЗДАНИЕ ПРИГЛАШЕНИЯ ======
@router.callback_query(F.data.startswith("create_invite_"))
async def create_invite_handler(callback: CallbackQuery, user_role: str):
    """Создание приглашения"""

    role = callback.data.replace("create_invite_", "")

    # Проверка прав
    if role == 'admin' and user_role != 'root':
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    if role == 'owner' and user_role not in ['root', 'admin']:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    # Генерируем код
    code = generate_invite_code()
    expires_at = datetime.now() + timedelta(days=1)

    # Сохраняем в БД
    create_invite(code, callback.from_user.id, role, expires_at.strftime('%Y-%m-%d %H:%M:%S'))

    bot_username = (await callback.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={code}"
    expires_str = expires_at.strftime("%d.%m.%Y")

    role_names = {
        'admin': '👑 Администратор',
        'owner': '🏠 Владелец',
        'manager': '📋 Менеджер',
        'cleaner': '🧹 Клинер',
        'installer': '🔧 Инсталлер'
    }

    # Отдельное сообщение со ссылкой (БЕЗ КНОПОК)
    await callback.message.answer(
        f"✅ <b>ПРИГЛАШЕНИЕ СОЗДАНО</b>\n\n"
        f"{role_names.get(role, role)}\n"
        f"📅 Действителен до: {expires_str}\n\n"
        f"🔗 <b>ССЫЛКА:</b>\n"
        f"<code>{invite_link}</code>",
        parse_mode="HTML"
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


# ====== ОБРАБОТЧИК КНОПКИ "АДМИН-ПАНЕЛЬ" ======
@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery, user_role: str):
    if user_role not in ['root', 'admin']:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    is_root = (user_role == 'root')

    await callback.message.edit_text(
        f"{config.EMOJI['admin']} <b>Админ-панель</b>\n\n"
        f"Ваша роль: {user_role}",
        reply_markup=admin_panel_keyboard(is_root),
        parse_mode="HTML"
    )
    await callback.answer()