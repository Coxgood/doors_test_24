"""
Команды, которые овнер может отправить устройству через бота.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.mqtt import mqtt_client
from ..models.command import OpenDoorCommand

router = APIRouter()
logger = logging.getLogger(__name__)


class OpenDoorCommand(BaseModel):
    device_id: str
    duration: int = 5
    source: str = "owner"  # owner, guest, admin


@router.post("/commands/open", summary="Открыть дверь")
async def open_door(
        command: OpenDoorCommand,
        db=Depends(get_db)
):
    """
    Команда открыть дверь.
    Если устройство в режиме внимания — отправляет MQTT мгновенно.
    Если спит — создаёт задачу (исполнится при пробуждении).
    """
    # Проверяем статус устройства
    device = await db.fetchrow("""
        SELECT mode, attention_mode_until 
        FROM esp_devices 
        WHERE device_id = $1
    """, command.device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Если устройство спит — отклоняем (согласно твоему правилу)
    if device['mode'] == 'sleep':
        logger.warning(f"❌ Попытка открыть спящее устройство {command.device_id}")

        # Логируем попытку
        await db.execute("""
            INSERT INTO esp_events (device_id, event_type, payload)
            VALUES ($1, 'command_rejected', $2)
        """, command.device_id, {"reason": "device_sleeping", "command": "open"})

        return {
            "status": "error",
            "reason": "device_sleeping",
            "message": "Устройство спит. Сначала войдите в режим внимания."
        }

    # Если в режиме внимания — отправляем MQTT
    if device['mode'] == 'attention' and device['attention_mode_until'] > datetime.utcnow():
        mqtt_client.publish(
            f"doors24/command/{command.device_id}",
            {"command": "open_door", "duration": command.duration}
        )

        logger.info(f"✅ MQTT команда open отправлена {command.device_id}")

        return {
            "status": "ok",
            "method": "mqtt",
            "message": "Дверь открывается"
        }

    # Если устройство просыпается — создаём задачу
    await db.execute("""
        INSERT INTO esp_tasks (device_id, task_type, parameters, expires_at)
        VALUES ($1, 'open_door', $2, NOW() + INTERVAL '5 minutes')
    """, command.device_id, {"duration": command.duration})

    logger.info(f"📝 Задача open_door создана для {command.device_id}")

    return {
        "status": "ok",
        "method": "task",
        "message": "Команда будет выполнена при следующем пробуждении устройства"
    }