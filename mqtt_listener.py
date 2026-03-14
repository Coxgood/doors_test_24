#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# 👇 ВСТАВЬ СЮДА РЕАЛЬНЫЙ IP ТВОЕГО СЕРВЕРА
BROKER = "192.168.1.100"  # замени на свой IP
PORT = 1883
TOPIC = "doors24/#"


def on_connect(client, userdata, flags, rc, properties=None):
    """При подключении к брокеру"""
    print(f"✅ Подключен к MQTT брокеру (код: {rc})")
    client.subscribe(TOPIC)
    print(f"👂 Слушаем топик: {TOPIC}")


def on_message(client, userdata, msg):
    """При получении сообщения"""
    topic = msg.topic
    payload = msg.payload.decode()

    print(f"\n📨 [{datetime.now().strftime('%H:%M:%S')}] Получено:")
    print(f"   Топик: {topic}")
    print(f"   Сообщение: {payload}")

    try:
        data = json.loads(payload)
        print(f"   📊 Данные: {data}")
        if "qr_code" in data:
            print(f"   🔍 Найден QR: {data['qr_code']}")
    except json.JSONDecodeError:
        print(f"   📝 Просто текст (не JSON)")


def main():
    # Используем новую версию API
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🚀 MQTT слушатель запущен")
    print(f"Брокер: {BROKER}:{PORT}")
    print("-" * 50)

    client.connect(BROKER, PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Слушатель остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")