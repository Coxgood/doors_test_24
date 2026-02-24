# middlewares/role.py
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable

from database import get_user_role

class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        # получаем роль из БД (функцию напишем ниже)
        role = get_user_role(user_id)
        data['user_role'] = role or 'guest'
        return await handler(event, data)