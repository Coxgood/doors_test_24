"""
Асинхронное подключение к PostgreSQL.
"""
import asyncpg
from asyncpg import Pool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://doors_user:GlDxzFUy6V@localhost/doors_db")

class Database:
    pool: Pool = None

    async def connect(self):
        """Создаём пул соединений"""
        self.pool = await asyncpg.create_pool(DATABASE_URL)

    async def disconnect(self):
        """Закрываем пул"""
        if self.pool:
            await self.pool.close()

    async def execute(self, query, *args):
        """Выполнить запрос без возврата данных"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query, *args):
        """Получить несколько строк"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query, *args):
        """Получить одну строку"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query, *args):
        """Получить одно значение"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

db = Database()

async def init_db():
    """Инициализация БД при старте"""
    await db.connect()
    print("✅ База данных подключена")

async def get_db():
    """Dependency для FastAPI"""
    return db