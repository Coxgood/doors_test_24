# main_new.py
import asyncio
import logging
from aiogram import Bot, Dispatcher

import config
from database import init_db
from handlers import start, booking, calendar, time, orders
from middlewares.role import RoleMiddleware
from handlers import admin_invites


# Инициализация бота
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Сначала подключаем middleware
dp.message.middleware(RoleMiddleware())
dp.callback_query.middleware(RoleMiddleware())

# Потом все остальные роутеры
dp.include_router(admin_invites.router)
#dp.include_router(user_management.router)
dp.include_router(booking.router)
dp.include_router(calendar.router)
dp.include_router(time.router)
dp.include_router(orders.router)

# start.router — самым последним!
dp.include_router(start.router)


async def main():
    """Запуск бота"""
    init_db()
    print(f"✅ Бот запущен с токеном: {config.BOT_TOKEN[:10]}...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('👋 Бот остановлен')