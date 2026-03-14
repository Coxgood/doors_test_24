"""
Pydantic модели для команд ESP32.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class OpenDoorCommand(BaseModel):
    """Команда открыть дверь"""
    device_id: str = Field(..., description="ID устройства (ESP32_01)")
    duration: int = Field(5, ge=1, le=30, description="Время открытия в секундах")
    source: str = Field("owner", description="Источник команды: owner, admin, guest")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время команды")

class BlinkCommand(BaseModel):
    """Команда мигнуть светодиодом"""
    device_id: str = Field(..., description="ID устройства")
    times: int = Field(3, ge=1, le=10, description="Количество миганий")
    interval: int = Field(200, ge=50, le=1000, description="Интервал в мс")

class AttentionModeCommand(BaseModel):
    """Команда войти в режим внимания"""
    device_id: str = Field(..., description="ID устройства")
    duration: int = Field(180, ge=30, le=600, description="Длительность в секундах")

class SyncQRCommand(BaseModel):
    """Команда синхронизации QR-кодов"""
    device_id: str = Field(..., description="ID устройства")
    qr_list: list[str] = Field(..., description="Список активных QR-кодов")
    full_sync: bool = Field(True, description="Полная замена или инкрементальная")

class RebootCommand(BaseModel):
    """Команда перезагрузки"""
    device_id: str = Field(..., description="ID устройства")
    delay: int = Field(0, ge=0, le=30, description="Задержка перед перезагрузкой (сек)")

# Объединённый тип команды (для ответа)
Command = OpenDoorCommand | BlinkCommand | AttentionModeCommand | SyncQRCommand | RebootCommand