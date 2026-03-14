"""
Роутер для отладки и тестирования.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
import logging

from ..core.database import get_db

router = APIRouter(prefix="/debug", tags=["Отладка"])
logger = logging.getLogger(__name__)


@router.get("/events/last/{count}", summary="Последние N событий")
async def get_last_events(count: int = 10, db=Depends(get_db)):
    """
    Возвращает последние N событий от ESP32.
    """
    events = await db.fetch("""
        SELECT id, device_id, event_type, payload, created_at
        FROM esp_events
        ORDER BY id DESC
        LIMIT $1
    """, count)

    return [dict(e) for e in events]


@router.get("/events/by-device/{device_id}", summary="События по устройству")
async def get_device_events(device_id: str, limit: int = 20, db=Depends(get_db)):
    """
    Возвращает события для конкретного устройства.
    """
    events = await db.fetch("""
        SELECT id, event_type, payload, created_at
        FROM esp_events
        WHERE device_id = $1
        ORDER BY id DESC
        LIMIT $2
    """, device_id, limit)

    return [dict(e) for e in events]


@router.get("/devices/status", summary="Статус всех устройств")
async def get_all_devices_status(db=Depends(get_db)):
    """
    Показывает статус всех зарегистрированных устройств.
    """
    devices = await db.fetch("""
        SELECT 
            device_id,
            apartment_id,
            firmware_version,
            last_seen,
            mode,
            battery_level
        FROM esp_devices
        ORDER BY last_seen DESC NULLS LAST
    """)

    result = []
    for d in devices:
        is_online = d['last_seen'] > datetime.now() - timedelta(minutes=5) if d['last_seen'] else False
        result.append({
            "device_id": d['device_id'],
            "apartment_id": d['apartment_id'],
            "status": "online" if is_online else "offline",
            "mode": d['mode'] or "unknown",
            "firmware": d['firmware_version'],
            "last_seen": d['last_seen'],
            "battery": d['battery_level']
        })

    return result


@router.get("/stats", summary="Статистика системы")
async def get_stats(db=Depends(get_db)):
    """
    Общая статистика по системе.
    """
    # Количество событий за последний час
    events_hour = await db.fetchval("""
        SELECT COUNT(*) FROM esp_events 
        WHERE created_at > NOW() - INTERVAL '1 hour'
    """)

    # Количество устройств
    devices_count = await db.fetchval("SELECT COUNT(*) FROM esp_devices")

    # Количество онлайн устройств (были активны за последние 5 мин)
    online_count = await db.fetchval("""
        SELECT COUNT(*) FROM esp_devices 
        WHERE last_seen > NOW() - INTERVAL '5 minutes'
    """)

    # Типы событий
    event_types = await db.fetch("""
        SELECT event_type, COUNT(*) 
        FROM esp_events 
        GROUP BY event_type 
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)

    return {
        "events_last_hour": events_hour,
        "devices_total": devices_count,
        "devices_online": online_count,
        "top_events": [{"type": e['event_type'], "count": e['count']} for e in event_types],
        "timestamp": datetime.now().isoformat()
    }


@router.delete("/events/clear", summary="Очистить все события (осторожно!)")
async def clear_all_events(confirm: bool = False, db=Depends(get_db)):
    """
    Удаляет все события из esp_events.
    Требует подтверждения confirm=true.
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="Требуется подтверждение: ?confirm=true")

    count = await db.fetchval("SELECT COUNT(*) FROM esp_events")
    await db.execute("DELETE FROM esp_events")

    logger.warning(f"🗑️ Удалено {count} событий")

    return {"status": "ok", "deleted": count}