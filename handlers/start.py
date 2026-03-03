from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import config
from database import (
    get_user_role,
    get_user_id_by_telegram,
    get_connection,
    check_invite,
    use_invite
)
from states import Form

router = Router()


@router.callback_query(F.data == "users_menu")
async def users_menu_handler(callback: CallbackQuery, user_role: str):
    """Меню выбора роли для приглашения"""

    if user_role not in ['root', 'admin']:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    is_root = (user_role == 'root')

    buttons = []

    # 👑 Админ (только для root)
    if is_root:
        buttons.append([InlineKeyboardButton(
            text="👑 Пригласить администратора",
            callback_data="confirm_invite_admin"
        )])

    # 🏠 Владелец (для root и admin)
    buttons.append([InlineKeyboardButton(
        text="🏠 Пригласить собственника",
        callback_data="confirm_invite_owner"
    )])

    # 📋 Менеджер (заглушка)
    buttons.append([InlineKeyboardButton(
        text="📋 Пригласить менеджера",
        callback_data="invite_manager_soon"
    )])

    # 🧹 Клинер (заглушка)
    buttons.append([InlineKeyboardButton(
        text="🧹 Пригласить клинера",
        callback_data="invite_cleaner_soon"
    )])

    # 📋 Мои приглашения
    buttons.append([InlineKeyboardButton(
        text="📋 Мои приглашения",
        callback_data="my_invites"
    )])

    # 🔙 Назад
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="start"
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "👥 <b>Приглашение пользователя</b>\n\n"
        f"Выберите роль для приглашения:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

def get_main_menu_keyboard(role: str, user_id: int) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру главного меню"""

    buttons = [
        [InlineKeyboardButton(
            text=f"{config.EMOJI['calendar']} Бронирование",
            callback_data=f"order_{user_id}"
        )]
    ]

    # Раздел Квартиры для разных ролей
    if role in ['root', 'admin']:
        buttons.append([InlineKeyboardButton(
            text=f"{config.EMOJI['apartment']} Активные заявки",
            callback_data="admin_requests"
        )])

    elif role in ['owner', 'manager']:
        buttons.append([InlineKeyboardButton(
            text=f"{config.EMOJI['apartment']} Мои заявки",
            callback_data="my_requests"
        )])

    # Кнопка создания заявки
    if role in ['owner', 'admin', 'root']:
        buttons.append([InlineKeyboardButton(
            text=f"{config.EMOJI['apartment']} ➕ Заявка на квартиру",
            callback_data="new_apartment_request"
        )])

    # 👥 CОЗДАТЬ ПРИГЛАШЕНИЕ  (для root/admin)
    if role in ['root', 'admin']:
        buttons.append([InlineKeyboardButton(
            text=f"👥 Управление пользователями",
            callback_data="users_menu"
        )])


    # Кнопка профиля для всех
    buttons.append([InlineKeyboardButton(
        text=f"{config.EMOJI['info']} Профиль",
        callback_data="profile"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Стартовое сообщение с обработкой инвайтов"""
    args = message.text.split()

    # ЕСЛИ ЕСТЬ КОД ПРИГЛАШЕНИЯ
    if len(args) > 1:
        code = args[1]
        invite = check_invite(code)

        if not invite:
            await message.answer(f"{config.EMOJI['warning']} Ссылка недействительна")
            return

        # Регистрируем пользователя
        db = get_connection()
        cursor = db.cursor()

        # Проверяем, есть ли уже пользователь
        cursor.execute("SELECT id FROM users WHERE telegram_id = %s", (message.from_user.id,))
        existing = cursor.fetchone()

        if existing:
            # Обновляем существующего
            cursor.execute('''
                UPDATE users 
                SET role = %s, first_name = %s, last_name = %s, created_by = %s
                WHERE telegram_id = %s
            ''', (invite['role'], message.from_user.first_name or '',
                  message.from_user.last_name or '', invite['created_by'], message.from_user.id))
            user_id = existing['id']
        else:
            # Создаём нового
            cursor.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, role, created_by)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (message.from_user.id, message.from_user.first_name or '',
                  message.from_user.last_name or '', invite['role'], invite['created_by']))
            user_id = cursor.fetchone()['id']

        # Активируем инвайт
        cursor.execute('''
            UPDATE invites 
            SET is_used = TRUE, used_by = %s, used_at = NOW()
            WHERE code = %s
        ''', (user_id, code))

        db.commit()
        db.close()

        await message.answer(
            f"{config.EMOJI['confirm']} <b>Добро пожаловать!</b>\n"
            f"Вы зарегистрированы как {invite['role']}.",
            parse_mode="HTML"
        )
        return

    # Обычный вход без инвайта
    await state.clear()

    user_id = get_user_id_by_telegram(message.from_user.id)
    user_role = get_user_role(message.from_user.id)

    keyboard = get_main_menu_keyboard(user_role, message.from_user.id)

    await message.answer(
        f"{config.EMOJI['info']} Здравствуйте, {message.from_user.first_name}!\n"
        f"Ваша роль: {user_role}",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "start")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    try:
        await callback.answer()
    except:
        pass

    await state.clear()

    user_id = get_user_id_by_telegram(callback.from_user.id)
    user_role = get_user_role(callback.from_user.id)

    keyboard = get_main_menu_keyboard(user_role, callback.from_user.id)

    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=keyboard
    )
    await callback.message.delete()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показывает профиль пользователя"""
    user_id = get_user_id_by_telegram(callback.from_user.id)
    user_role = get_user_role(callback.from_user.id)

    text = (
        f"{config.EMOJI['info']} <b>Ваш профиль</b>\n\n"
        f"Роль: {user_role}\n"
        f"ID: {callback.from_user.id}\n"
        f"Имя: {callback.from_user.full_name}\n"
        f"Внутренний ID: {user_id}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"{config.EMOJI['cancel']} Назад",
            callback_data="start"
        )
    ]])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "my_invites")
async def my_invites_handler(callback: CallbackQuery):
    """Показывает активные приглашения текущего пользователя"""

    from database import get_active_invites
    from datetime import datetime

    invites = get_active_invites(callback.from_user.id)

    if not invites:
        await callback.answer("📭 У вас нет активных приглашений", show_alert=True)
        return

    text = "⏳ <b>Ваши активные приглашения</b>\n\n"
    bot_username = (await callback.bot.get_me()).username

    for inv in invites:
        # inv: (id, code, created_by, role, created_at, expires_at, used_by, used_at, is_used)
        code = inv[1]  # код
        role = inv[3]  # роль
        expires_at = inv[5]  # срок действия

        role_emoji = "👑" if role == 'admin' else "👔"

        # обрезаем микросекунды, если есть
        clean_date = expires_at.split('.')[0]
        expires = datetime.strptime(clean_date, "%Y-%m-%d %H:%M:%S")
        expires_str = expires.strftime("%d.%m.%Y %H:%M")

        link = f"https://t.me/{bot_username}?start={code}"

        text += f"{role_emoji} {role}\n🔗 <code>{link}</code>\n⏳ до {expires_str}\n\n"

    # ✅ ИСПРАВЛЕНО: возврат в меню приглашений
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"{config.EMOJI['cancel']} Назад", callback_data="invites_menu")
    ]])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()