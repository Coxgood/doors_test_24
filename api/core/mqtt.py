"""
MQTT клиент для отправки команд ESP32.
"""
import paho.mqtt.client as mqtt
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MQTTClient:
    """Синглтон для MQTT подключения"""

    _instance = None
    _client = None
    _connected = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        """Инициализация MQTT клиента"""
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish

        # Настройки для HiveMQ Cloud (если используем облако)
        self.broker = "c602b5e6b31c4164959caddbb5b20559.s1.eu.hivemq.cloud"
        self.port = 8883
        self.username = "server_listener"
        self.password = "GlDxzFUy6V"

        # Включаем TLS
        self._client.tls_set()
        self._client.username_pw_set(self.username, self.password)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Колбэк подключения"""
        if rc == 0:
            self._connected = True
            logger.info("✅ MQTT клиент подключён к брокеру")
        else:
            self._connected = False
            logger.error(f"❌ Ошибка MQTT подключения: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Колбэк отключения"""
        self._connected = False
        logger.warning("⚠️ MQTT клиент отключён")

    def _on_publish(self, client, userdata, mid, rc, properties=None):
        """Колбэк публикации"""
        logger.debug(f"📤 MQTT сообщение {mid} отправлено")

    def connect(self):
        """Подключение к брокеру"""
        if not self._connected:
            try:
                self._client.connect(self.broker, self.port, 60)
                self._client.loop_start()
            except Exception as e:
                logger.error(f"❌ Ошибка подключения MQTT: {e}")

    def disconnect(self):
        """Отключение от брокера"""
        if self._connected:
            self._client.loop_stop()
            self._client.disconnect()

    def publish(self, topic: str, payload: dict, qos: int = 1):
        """
        Отправить команду устройству.

        Args:
            topic: Топик (например, doors24/command/ESP32_01)
            payload: Словарь с командой
            qos: Quality of Service (0, 1, 2)
        """
        if not self._connected:
            logger.warning("⚠️ MQTT не подключён, пробую подключиться...")
            self.connect()

        try:
            msg = json.dumps(payload)
            result = self._client.publish(topic, msg, qos=qos)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✅ Команда отправлена в {topic}: {payload}")
                return True
            else:
                logger.error(f"❌ Ошибка отправки: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка публикации MQTT: {e}")
            return False


# Создаём глобальный экземпляр
mqtt_client = MQTTClient()