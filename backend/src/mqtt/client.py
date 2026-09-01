"""MQTT 客户端封装。"""

from __future__ import annotations

import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

from src.config.settings import get_mqtt_settings
from src.database.connection import get_engine
from src.mqtt.message_handler import MqttMessageHandler

logger = logging.getLogger(__name__)


class SmartFarmMqttClient:
    """连接 EMQX 并处理简单的设备消息。"""

    def __init__(self, handler: MqttMessageHandler | None = None) -> None:
        settings = get_mqtt_settings()
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.username_pw_set(settings.username, settings.password)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self.host = settings.host
        self.port = settings.port
        self.keepalive = settings.keepalive
        self.last_message: dict[str, Any] | None = None
        self.connected = False
        self._handler = handler or MqttMessageHandler(get_engine())

    def connect(self) -> None:
        """与 Broker 建立连接。"""
        # 使用异步连接：MQTT 临时不可用时，REST API 仍可提供查询能力；
        # paho 会在网络循环中持续尝试连接。
        self._client.connect_async(self.host, self.port, self.keepalive)
        self._client.loop_start()

    def disconnect(self) -> None:
        """断开连接并停止事件循环。"""
        self._client.loop_stop()
        self._client.disconnect()

    def subscribe(self, topic: str) -> None:
        """订阅主题。"""
        self._client.subscribe(topic, qos=0)

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """发布 JSON 消息。"""
        if not self.connected:
            raise RuntimeError("MQTT Broker 尚未连接")
        result = self._client.publish(topic, json.dumps(payload, ensure_ascii=False), qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT 发布失败，错误码: {result.rc}")

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        """连接成功后订阅业务主题。"""
        logger.info("MQTT connected to %s:%s", self.host, self.port)
        self.connected = True
        self.subscribe("farm/telemetry/#")
        self.subscribe("farm/status/#")
        self.subscribe("farm/command_result/#")

    def _on_disconnect(
        self, client: mqtt.Client, userdata: Any, disconnect_flags: Any,
        reason_code: Any, properties: Any = None,
    ) -> None:
        self.connected = False
        logger.warning("MQTT disconnected from %s:%s: %s", self.host, self.port, reason_code)

    def handle_message(self, topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        """统一处理 MQTT 消息，并将合法消息持久化。"""
        self.last_message = {"topic": topic, **payload}
        result = self._handler.handle(topic, payload)
        logger.info("MQTT message on %s processed: %s", topic, result)
        return {**self.last_message, **result}

    def _on_message(self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:
        """将消息流转给业务处理逻辑。"""
        try:
            payload = json.loads(message.payload.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            payload = {"raw": message.payload.decode("utf-8", errors="replace")}

        try:
            self.handle_message(message.topic, payload)
        except Exception as error:
            # 单条坏消息不能中断 paho 的网络循环。
            logger.exception("Ignored MQTT message on %s: %s", message.topic, error)


def create_mqtt_client() -> SmartFarmMqttClient:
    """工厂函数，供 FastAPI startup 使用。"""
    return SmartFarmMqttClient()
