# middlewares/role.py
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
import logging

from database import get_user_role

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RoleMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id

        # 🔍 Подробная отладка
        logger.info(f"🔍 [RoleMiddleware] Получен event от user_id: {user_id}")
        logger.info(f"🔍 [RoleMiddleware] Тип event: {type(event).__name__}")

        # Получаем username если есть
        username = getattr(event.from_user, 'username', None)
        if username:
            logger.info(f"🔍 [RoleMiddleware] Username: @{username}")

        # Получаем роль из БД
        logger.info(f"🔍 [RoleMiddleware] Вызов get_user_role для {user_id}")
        role = get_user_role(user_id)
        logger.info(f"🔍 [RoleMiddleware] Роль из БД: {role}")

        # Если роль не найдена, ставим 'guest'
        if role is None:
            logger.warning(f"⚠️ [RoleMiddleware] Роль для {user_id} не найдена, установлен 'guest'")
            data['user_role'] = 'guest'
        else:
            data['user_role'] = role
            logger.info(f"✅ [RoleMiddleware] Установлена роль: {role}")

        # Передаем управление дальше
        logger.info(f"🔍 [RoleMiddleware] Передача управления хендлеру")
        result = await handler(event, data)
        logger.info(f"🔍 [RoleMiddleware] Хендлер выполнен")

        return result