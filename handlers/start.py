# handlers/start.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from datetime import datetime

import config
from database import get_user_role, get_active_invites
from states import Form

router = Router()


def get_main_menu_keyboard(role: str, user_id: int) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру главного меню"""

    # Кнопка бронирования — для всех
    buttons = [
        [InlineKeyboardButton(
            text=f"{config.EMOJI['calendar']} Бронирование",
            callback_data=f"order_{user_id}"
        )]
    ]

    # 👇 МЕНЯЕМ ЭТОТ БЛОК
    # Было: Пользователи — для root, admin, owner
    # Стало: Приглашения — для root, admin, owner
    if role in ['root', 'admin', 'owner']:
        buttons.append([InlineKeyboardButton(
            text=f"{config.EMOJI['guest']} Приглашения",
            callback_data="invites_menu"  # было "user_management"
        )])

    # Профиль — для всех (оставляем)
    buttons.append([InlineKeyboardButton(
        text=f"{config.EMOJI['info']} Профиль",
        callback_data="profile"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user_role: str):
    """Стартовое сообщение (только при первом входе)"""
    args = message.text.split()

    # ЕСЛИ ЕСТЬ КОД ПРИГЛАШЕНИЯ
    if len(args) > 1:
        code = args[1]

        from database import check_invite, use_invite, get_connection
        invite = check_invite(code)

        if not invite:
            await message.answer(f"{config.EMOJI['warning']} Ссылка недействительна или истекла.")
            return

        # регистрируем пользователя
        db = get_connection()
        cursor = db.cursor()

        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (message.from_user.id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE users 
                SET role = ?, first_name = ?, last_name = ?
                WHERE telegram_id = ?
            ''', (invite[3], message.from_user.first_name or '', message.from_user.last_name or '',
                  message.from_user.id))
            user_id = existing[0]
        else:
            cursor.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, role)
                VALUES (?, ?, ?, ?)
            ''', (message.from_user.id, message.from_user.first_name or '', message.from_user.last_name or '',
                  invite[3]))
            user_id = cursor.lastrowid

        cursor.execute('''
            UPDATE invites 
            SET is_used = 1, used_by = ?, used_at = datetime('now')
            WHERE code = ?
        ''', (user_id, code))

        db.commit()
        db.close()

        await message.answer(
            f"{config.EMOJI['confirm']} <b>Добро пожаловать!</b>\n"
            f"Вы зарегистрированы как {invite[3]}.",
            parse_mode="HTML"
        )
        return

    # Обычный /start (ТОЛЬКО ОДИН РАЗ!)
    await state.clear()
    keyboard = get_main_menu_keyboard(user_role, message.from_user.id)
    await message.answer(
        f"{config.EMOJI['info']} Здравствуйте, {message.from_user.first_name}!\n"
        f"Ваша роль: {user_role}",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "start")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext, user_role: str):
    """Возврат в главное меню (новым сообщением)"""
    await state.clear()

    keyboard = get_main_menu_keyboard(user_role, callback.from_user.id)

    # Отвечаем новым сообщением (вместо редактирования)
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "invites_menu")
async def show_invites_menu(callback: CallbackQuery, user_role: str):
    """Меню приглашений"""

    # Базовая клавиатура для всех
    buttons = []

    if user_role == 'root':
        buttons = [
            [InlineKeyboardButton(text="👑 Администратор", callback_data="confirm_invite_admin")],
            [InlineKeyboardButton(text="🏠 Владелец", callback_data="confirm_invite_owner")],
            [InlineKeyboardButton(text="📋 Менеджер", callback_data="invite_manager_soon")],
            [InlineKeyboardButton(text="🧹 Клинер", callback_data="invite_cleaner_soon")],
            [InlineKeyboardButton(text="🔧 Инсталлер", callback_data="invite_installer_soon")],
        ]
    elif user_role == 'admin':
        buttons = [
            [InlineKeyboardButton(text="🏠 Владелец", callback_data="confirm_invite_owner")],
            [InlineKeyboardButton(text="📋 Менеджер", callback_data="invite_manager_soon")],
            [InlineKeyboardButton(text="🧹 Клинер", callback_data="invite_cleaner_soon")],
            [InlineKeyboardButton(text="🔧 Инсталлер", callback_data="invite_installer_soon")],
        ]
    elif user_role == 'owner':
        buttons = [
            [InlineKeyboardButton(text="📋 Менеджер", callback_data="invite_manager_soon")],
            [InlineKeyboardButton(text="🧹 Клинер", callback_data="invite_cleaner_soon")],
        ]
    else:
        await callback.answer("У вас нет доступа к приглашениям", show_alert=True)
        return

    # Кнопки для всех
    buttons.append([InlineKeyboardButton(text="⏳ Мои приглашения", callback_data="my_invites")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="start")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        f"🔹 <b>Создание приглашений</b>\n\n"
        f"Ваша роль: {user_role}\n"
        f"Выберите роль нового пользователя:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, user_role: str):
    # ✅ Сразу отвечаем
    try:
        await callback.answer()
    except:
        pass


    text = (
        f"{config.EMOJI['info']} <b>Ваш профиль</b>\n\n"
        f"Роль: {user_role}\n"
        f"ID: {callback.from_user.id}\n"
        f"Имя: {callback.from_user.full_name}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"{config.EMOJI['cancel']} Назад",
            callback_data="start"
        )
    ]])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


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