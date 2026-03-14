"""
Pydantic модели для устройств ESP32.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import re


class DeviceRegistration(BaseModel):
    """Регистрация нового устройства"""
    mac: str = Field(..., description="MAC-адрес устройства")
    chip_id: str = Field(..., description="ID чипа ESP32")
    firmware: str = Field(..., description="Версия прошивки")

    @validator('mac')
    def validate_mac(cls, v):
        if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', v):
            raise ValueError('Неверный формат MAC-адреса')
        return v.upper()


class DeviceClaim(BaseModel):
    """Привязка устройства к квартире"""
    device_id: str = Field(..., description="ID устройства (ESP32_01)")
    apartment_id: int = Field(..., description="ID квартиры")
    owner_id: int = Field(..., description="ID владельца")
    token: Optional[str] = Field(None, description="Токен для привязки")


class DeviceStatus(BaseModel):
    """Текущий статус устройства"""
    device_id: str
    apartment_id: Optional[int] = None
    status: str = "offline"  # online/offline
    mode: str = "sleep"  # sleep/attention/sync
    firmware: Optional[str] = None
    last_seen: Optional[datetime] = None
    battery: Optional[int] = None
    rssi: Optional[int] = None
    uptime: Optional[int] = None


class DeviceConfig(BaseModel):
    """Конфигурация устройства"""
    sleep_interval: int = Field(300, ge=60, le=3600, description="Интервал сна в секундах")
    attention_timeout: int = Field(180, ge=30, le=600, description="Таймаут режима внимания")
    mqtt_broker: Optional[str] = None
    mqtt_port: Optional[int] = 8883