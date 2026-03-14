"""
Роутер для управления устройствами:
- регистрация
- привязка к квартире
- статус
- сервисный режим
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.device import DeviceStatus, DeviceRegistration, DeviceClaim

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/devices/register", summary="Регистрация нового устройства")
async def register_device(
        registration: DeviceRegistration,
        db=Depends(get_db)
):
    """
    ESP32 регистрируется при первом запуске.
    Передаёт MAC, chip_id, firmware.
    Сервер выдаёт уникальный device_id.
    """
    # Проверяем, не регистрировалось ли уже это устройство
    existing = await db.fetchrow(
        "SELECT device_id FROM esp_devices WHERE mac = $1 OR chip_id = $2",
        registration.mac, registration.chip_id
    )

    if existing:
        # Уже есть — возвращаем существующий ID
        logger.info(f"♻️ Устройство уже зарегистрировано: {existing['device_id']}")
        return {
            "status": "ok",
            "device_id": existing['device_id'],
            "existing": True
        }

    # Генерируем новый device_id (ESP32_XX)
    count = await db.fetchval("SELECT COUNT(*) FROM esp_devices")
    device_id = f"ESP32_{count + 1:02d}"

    # Сохраняем
    await db.execute("""
        INSERT INTO esp_devices (device_id, mac, chip_id, firmware_version, registered_at)
        VALUES ($1, $2, $3, $4, NOW())
    """, device_id, registration.mac, registration.chip_id, registration.firmware)

    logger.info(f"✅ Новое устройство зарегистрировано: {device_id}")

    return {
        "status": "ok",
        "device_id": device_id,
        "existing": False
    }


@router.post("/devices/claim", summary="Привязка устройства к квартире")
async def claim_device(
        claim: DeviceClaim,
        db=Depends(get_db)
):
    """
    Овнер привязывает ESP32 к своей квартире.
    Нужен device_id, apartment_id и токен (из бота).
    """
    # Проверяем, что квартира принадлежит овнеру
    apt = await db.fetchrow(
        "SELECT owner_id FROM apartments WHERE apartment_id = $1",
        claim.apartment_id
    )

    if not apt or apt['owner_id'] != claim.owner_id:
        raise HTTPException(status_code=403, detail="Not your apartment")

    # Привязываем
    await db.execute("""
        UPDATE esp_devices 
        SET apartment_id = $1, claimed_at = NOW()
        WHERE device_id = $2
    """, claim.apartment_id, claim.device_id)

    logger.info(f"🔗 Устройство {claim.device_id} привязано к квартире {claim.apartment_id}")

    return {"status": "ok", "device_id": claim.device_id, "apartment_id": claim.apartment_id}


@router.get("/devices/{device_id}/status", summary="Статус устройства")
async def get_device_status(
        device_id: str,
        db=Depends(get_db)
):
    """
    Возвращает текущий статус устройства:
    - онлайн/офлайн
    - режим (сон/внимание)
    - последние события
    """
    device = await db.fetchrow("""
        SELECT 
            device_id,
            apartment_id,
            firmware_version,
            last_seen,
            mode,
            attention_mode_until,
            battery_level,
            config
        FROM esp_devices 
        WHERE device_id = $1
    """, device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Считаем онлайн/офлайн (последний сигнал < 5 мин)
    is_online = device['last_seen'] > datetime.utcnow() - timedelta(minutes=5)

    # Последние 5 событий
    events = await db.fetch("""
        SELECT event_type, payload, created_at 
        FROM esp_events 
        WHERE device_id = $1 
        ORDER BY created_at DESC 
        LIMIT 5
    """, device_id)

    return {
        "device_id": device['device_id'],
        "apartment_id": device['apartment_id'],
        "status": "online" if is_online else "offline",
        "mode": device['mode'],
        "firmware": device['firmware_version'],
        "last_seen": device['last_seen'],
        "battery": device['battery_level'],
        "recent_events": [
            {"type": e['event_type'], "time": e['created_at']}
            for e in events
        ]
    }


@router.post("/devices/{device_id}/attention", summary="Включить режим внимания")
async def set_attention_mode(
        device_id: str,
        duration: int = 180,
        db=Depends(get_db)
):
    """
    Переводит устройство в режим внимания на N секунд.
    В этом режиме ESP32 не спит и мгновенно реагирует на команды.
    """
    # Проверяем, что устройство существует
    device = await db.fetchrow(
        "SELECT device_id FROM esp_devices WHERE device_id = $1",
        device_id
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Создаём задачу для ESP32
    await db.execute("""
        INSERT INTO esp_tasks (device_id, task_type, parameters, priority, expires_at)
        VALUES ($1, 'attention_mode', $2, 100, NOW() + INTERVAL '5 minutes')
    """, device_id, {"duration": duration})

    # Обновляем статус в БД
    await db.execute("""
        UPDATE esp_devices 
        SET mode = 'attention', attention_mode_until = NOW() + INTERVAL '1 second' * $2
        WHERE device_id = $1
    """, device_id, duration)

    logger.info(f"🔔 Режим внимания для {device_id} на {duration} сек")

    return {
        "status": "ok",
        "device_id": device_id,
        "mode": "attention",
        "until": datetime.utcnow() + timedelta(seconds=duration)
    }