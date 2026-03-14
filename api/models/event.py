"""
Pydantic модели для всех событий от ESP32.
Основаны на триггерах: датчик двери, дорбелл, сервисная кнопка.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import re

class BaseEvent(BaseModel):
    """Базовое событие от ESP32"""
    device_id: str = Field(..., description="ID устройства (ESP32_01, ESP32_02...)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время события")

# ===== Триггер 1: Датчик двери =====
class DoorEvent(BaseEvent):
    """События от датчика двери (геркон/магнитный контакт)"""
    event_type: str = Field(..., pattern='^(door_open|door_close|door_open_long|door_open_resolved)$')
    payload: Dict[str, Any] = Field(..., description="Данные события")

# ===== Триггер 2: Дорбелл (QR-сканер) =====
class QRScanEvent(BaseEvent):
    """События от GM60 — сканирование QR-кода"""
    event_type: str = Field(..., pattern='^(qr_scan_attempt|qr_scan_success|qr_scan_fail)$')
    payload: Dict[str, Any] = Field(..., description="Данные сканирования")

# ===== Триггер 3: Сервисная кнопка =====
class ServiceButtonEvent(BaseEvent):
    """События от сервисной кнопки (скрытая, внутри)"""
    event_type: str = Field(..., pattern='^(service_button_press|service_mode_enter|service_mode_exit|factory_reset)$')
    payload: Dict[str, Any] = Field(..., description="Данные")

# ===== Сетевые события =====
class NetworkEvent(BaseEvent):
    """События сети — WiFi, MQTT, интернет"""
    event_type: str = Field(..., pattern='^(wifi_connected|wifi_disconnected|wifi_connect_fail|mqtt_connected|mqtt_disconnected|internet_check_success|internet_check_fail|wifi_fallback_mode)$')
    payload: Dict[str, Any] = Field(..., description="Данные")

# ===== События регистрации =====
class RegistrationEvent(BaseEvent):
    """Регистрация и привязка устройства"""
    event_type: str = Field(..., pattern='^(device_registration_start|device_registration_success|device_registration_fail|device_claim_attempt|device_claim_success|device_claim_fail)$')
    payload: Dict[str, Any] = Field(..., description="Данные")

# ===== Системные события =====
class SystemEvent(BaseEvent):
    """Системные события — boot, sleep, ota"""
    event_type: str = Field(..., pattern='^(boot|sleep|wakeup|reset|time_sync|config_update|ota_start|ota_success|ota_fail|memory_low)$')
    payload: Dict[str, Any] = Field(..., description="Данные")

# ===== Объединённый тип события =====
Event = DoorEvent | QRScanEvent | ServiceButtonEvent | NetworkEvent | RegistrationEvent | SystemEvent