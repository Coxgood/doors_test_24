"""
Модуль для работы с командами ESP32.
Проверка очереди команд, создание новых задач.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def check_and_create_commands(device_id: str, event_type: str, payload: dict):
    """
    Проверяет, нужно ли создать команду для устройства на основе события.
    Вызывается из events.py после сохранения события.
    """
    logger.info(f"🔍 Проверка команд для {device_id} после события {event_type}")

    # Здесь будет логика создания команд
    # Например, если это qr_scan_success — можно сразу открыть дверь
    # Если door_open_long — отправить уведомление

    return None


async def get_pending_commands(db, device_id: str):
    """
    Возвращает список ожидающих команд для устройства.
    """
    commands = await db.fetch("""
        SELECT id, command, parameters 
        FROM esp_tasks 
        WHERE device_id = $1 
          AND status = 'pending'
          AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY priority DESC, created_at ASC
        LIMIT 5
    """, device_id)

    # Помечаем как отправленные
    if commands:
        task_ids = [cmd['id'] for cmd in commands]
        await db.execute("""
            UPDATE esp_tasks 
            SET status = 'sent', sent_at = NOW() 
            WHERE id = ANY($1)
        """, task_ids)

    return [dict(cmd) for cmd in commands]