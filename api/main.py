import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import logging

# Абсолютные импорты от корня проекта
from api.routers import events, devices, commands, debug
from api.core.database import init_db
from api.core.logger import setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Создаём приложение
app = FastAPI(
    title="Doors24 IoT API",
    description="API для управления ESP32, приёма событий и отдачи команд",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры (теперь с префиксом api)
app.include_router(events.router, prefix="/api", tags=["ESP32 Events"])
app.include_router(devices.router, prefix="/api", tags=["Devices"])
app.include_router(commands.router, prefix="/api", tags=["Commands"])
app.include_router(debug.router, prefix="/api", tags=["Debug"])

@app.on_event("startup")
async def startup():
    logger.info(" API запускается...")
    await init_db()
    logger.info(" База данных подключена")

@app.on_event("shutdown")
async def shutdown():
    logger.info(" API останавливается...")

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Doors24 IoT API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["Root"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }