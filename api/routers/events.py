"""
Роутер для приёма всех событий от ESP32.
Сохраняет в БД и при необходимости создаёт команды.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import logging
from typing import Union

from ..core.database import get_db
from ..core.commands import check_and_create_commands
from ..models.event import Event

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/events",
             summary="Принять событие от ESP32",
             description="Универсальный эндпоинт для всех событий от устройства",
             response_model=dict)
async def receive_event(
        event: Event,
        background_tasks: BackgroundTasks,
        db=Depends(get_db)
):
    """
    Принимает событие от ESP32, сохраняет в БД,
    и при необходимости создаёт команды для устройства.

    Триггеры:
    - Датчик двери → door_open, door_close, door_open_long
    - Дорбелл → qr_scan_attempt, qr_scan_success, qr_scan_fail
    - Сервисная кнопка → service_button_press, service_mode_enter
    - Сеть → wifi_connected, mqtt_connected, internet_check_fail
    """
    logger.info(f"📨 Получено событие от {event.device_id}: {event.event_type}")

    try:
        # 1. Сохраняем событие в БД
        await db.execute("""
            INSERT INTO esp_events (device_id, event_type, payload, created_at)
            VALUES ($1, $2, $3, $4)
        """, event.device_id, event.event_type, event.payload.dict(), event.timestamp)

        # 2. Обновляем last_seen устройства
        await db.execute("""
            INSERT INTO esp_devices (device_id, last_seen, last_ip)
            VALUES ($1, NOW(), $2)
            ON CONFLICT (device_id) DO UPDATE
            SET last_seen = NOW(), last_ip = $2
        """, event.device_id, event.client_host)

        # 3. В зависимости от типа события — доп. действия
        background_tasks.add_task(
            process_event_background,
            event.device_id,
            event.event_type,
            event.payload.dict()
        )

        # 4. Проверяем, есть ли команды для устройства
        commands = await get_pending_commands(db, event.device_id)

        return {
            "status": "ok",
            "event_id": "будет ID из БД",
            "commands": commands if commands else []
        }

    except Exception as e:
        logger.error(f"❌ Ошибка обработки события: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_event_background(device_id: str, event_type: str, payload: dict):
    """Фоновая обработка событий"""
    logger.info(f"🔄 Фоновая обработка: {device_id} {event_type}")

    # Если это qr_scan_success — открываем дверь
    if event_type == "qr_scan_success":
        # Тут можно сразу дернуть MQTT
        pass

    # Если door_open_long — уведомляем овнера
    if event_type == "door_open_long":
        # Найти овнера по device_id и отправить уведомление
        pass


@router.post("/events/batch", summary="Пакетная отправка событий (при восстановлении связи)")
async def receive_events_batch(
        events: list[Event],
        db=Depends(get_db)
):
    """Принимает несколько событий сразу (когда ESP32 был офлайн)"""
    logger.info(f"📦 Получен пакет из {len(events)} событий")

    for event in events:
        await db.execute("""
            INSERT INTO esp_events (device_id, event_type, payload, created_at)
            VALUES ($1, $2, $3, $4)
        """, event.device_id, event.event_type, event.payload.dict(), event.timestamp)

    return {"status": "ok", "received": len(events)}