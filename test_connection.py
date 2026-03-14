#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime

# ===== ТВОИ ДАННЫЕ ИЗ HIVEMQ CLOUD =====
BROKER = "c602b5e6b31c4164959caddbb5b20559.s1.eu.hivemq.cloud"
PORT = 8883
TOPIC = "doors24/#"
USERNAME = "server_listener"
PASSWORD = "GlDxzFUy6V"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def on_connect(client, userdata, flags, rc, properties=None):
    """При подключении к брокеру"""
    if rc == 0:
        print("✅ Подключен к HiveMQ Cloud")
        client.subscribe(TOPIC)
        print(f"👂 Слушаем топик: {TOPIC}")
    else:
        print(f"❌ Ошибка подключения, код: {rc}")


def on_message(client, userdata, msg):
    """При получении сообщения"""
    topic = msg.topic
    payload = msg.payload.decode()

    # Логируем
    logging.info(f"Топик: {topic} | Сообщение: {payload}")

    print(f"\n📨 [{datetime.now().strftime('%H:%M:%S')}] Получено:")
    print(f"   Топик: {topic}")
    print(f"   Сообщение: {payload}")


def main():
    # Создаём клиента
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    # Включаем TLS
    client.tls_set()

    # Устанавливаем логин и пароль
    client.username_pw_set(USERNAME, PASSWORD)

    # Обработчики
    client.on_connect = on_connect
    client.on_message = on_message

    print("🚀 MQTT слушатель для HiveMQ Cloud запущен")
    print(f"Брокер: {BROKER}:{PORT}")
    print("-" * 50)

    # Подключаемся
    client.connect(BROKER, PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Слушатель остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")