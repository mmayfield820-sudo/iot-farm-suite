"""将 MQTT 消息校验后写入领域数据。"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine


logger = logging.getLogger(__name__)


class MqttMessageHandler:
    """处理设备遥测、心跳和灌溉指令执行结果。"""

    _DEVICE_TYPES = {
        "temperature": "TEMPERATURE_SENSOR",
        "humidity": "SOIL_MOISTURE_SENSOR",
    }

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def handle(self, topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        """校验主题和消息体；非法或未知设备消息不会写入数据库。"""
        parts = topic.split("/")
        if len(parts) != 3 or parts[0] != "farm":
            raise ValueError("不支持的 MQTT 主题")
        message_kind, mqtt_device_id = parts[1], parts[2]
        if message_kind not in {"telemetry", "status", "command_result"}:
            raise ValueError("不支持的 MQTT 消息类型")
        if payload.get("deviceId") != mqtt_device_id:
            raise ValueError("主题中的 deviceId 与消息体不一致")

        if message_kind == "telemetry":
            return self._save_telemetry(mqtt_device_id, payload)
        if message_kind == "status":
            return self._save_status(mqtt_device_id, payload)
        return self._save_command_result(mqtt_device_id, payload)

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if not isinstance(value, str):
            raise ValueError("ts 必须为 ISO 8601 时间字符串")
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError as error:
            raise ValueError("ts 不是有效的 ISO 8601 时间") from error

    def _find_device(self, connection: Any, mqtt_device_id: str) -> dict[str, Any]:
        row = connection.execute(
            text(
                "SELECT device_id, device_type, plot_id FROM devices "
                "WHERE mqtt_device_id = :mqtt_device_id"
            ),
            {"mqtt_device_id": mqtt_device_id},
        ).mappings().first()
        if row is None:
            raise ValueError("未注册的 MQTT 设备")
        return dict(row)

    @staticmethod
    def _mark_seen(connection: Any, device_id: int, at: datetime, online: bool) -> None:
        connection.execute(
            text(
                "UPDATE devices SET status = :status, "
                "last_heartbeat = CASE "
                "WHEN last_heartbeat IS NULL OR last_heartbeat < :reported_at "
                "THEN :reported_at ELSE last_heartbeat END "
                "WHERE device_id = :device_id"
            ),
            {
                "device_id": device_id,
                "status": "ONLINE" if online else "OFFLINE",
                "reported_at": at,
            },
        )

    def _save_telemetry(self, mqtt_device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        metric_type = payload.get("type")
        if metric_type not in self._DEVICE_TYPES:
            raise ValueError("遥测 type 只能是 temperature 或 humidity")
        if not isinstance(payload.get("msgId"), str) or not payload["msgId"]:
            raise ValueError("遥测消息缺少 msgId")
        try:
            value = float(payload["value"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("遥测消息 value 必须为数值") from error
        if metric_type == "humidity" and not 0 <= value <= 100:
            raise ValueError("湿度必须在 0 到 100 之间")
        reported_at = self._parse_timestamp(payload.get("ts"))

        with self._engine.begin() as connection:
            device = self._find_device(connection, mqtt_device_id)
            if device["device_type"] != self._DEVICE_TYPES[metric_type]:
                raise ValueError("遥测类型与已注册设备类型不一致")
            if device["plot_id"] is None:
                raise ValueError("设备尚未绑定地块")
            self._mark_seen(connection, device["device_id"], reported_at, True)
            result = connection.execute(
                text(
                    "INSERT IGNORE INTO device_telemetry "
                    "(device_id, message_id, metric_type, metric_value, reported_at) "
                    "VALUES (:device_id, :message_id, :metric_type, :metric_value, :reported_at)"
                ),
                {
                    "device_id": device["device_id"], "message_id": payload["msgId"],
                    "metric_type": metric_type, "metric_value": value,
                    "reported_at": reported_at,
                },
            )
            if metric_type == "humidity" and result.rowcount:
                self._create_low_moisture_alert(connection, device, value)
        return {"kind": "telemetry", "accepted": True, "duplicate": not bool(result.rowcount)}

    @staticmethod
    def _create_low_moisture_alert(connection: Any, device: dict[str, Any], value: float) -> None:
        """同一设备已有未处理低湿度告警时不重复创建。"""
        connection.execute(
            text(
                "INSERT INTO alerts "
                "(plot_id, device_id, alert_type, alert_description, alert_value, alert_threshold) "
                "SELECT :plot_id, :device_id, 'LOW_MOISTURE', "
                "'土壤湿度低于地块阈值', :value, c.soil_moisture_threshold "
                "FROM threshold_configs c WHERE c.plot_id = :plot_id "
                "AND :value < c.soil_moisture_threshold "
                "AND NOT EXISTS (SELECT 1 FROM alerts a WHERE a.device_id = :device_id "
                "AND a.alert_type = 'LOW_MOISTURE' AND a.alert_status = 'UNHANDLED')"
            ),
            {"plot_id": device["plot_id"], "device_id": device["device_id"], "value": value},
        )

    def _save_status(self, mqtt_device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload.get("online"), bool):
            raise ValueError("状态消息 online 必须为布尔值")
        reported_at = self._parse_timestamp(payload.get("ts"))
        with self._engine.begin() as connection:
            device = self._find_device(connection, mqtt_device_id)
            self._mark_seen(connection, device["device_id"], reported_at, payload["online"])
        return {"kind": "status", "accepted": True}

    def _save_command_result(self, mqtt_device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        command_id, result = payload.get("commandId"), payload.get("result")
        if not isinstance(command_id, str) or not command_id.startswith("CMD") or not command_id[3:].isdigit():
            raise ValueError("commandId 格式应为 CMD0001")
        if result not in {"success", "failed", "timeout"}:
            raise ValueError("result 必须为 success、failed 或 timeout")
        reported_at = self._parse_timestamp(payload.get("ts"))
        with self._engine.begin() as connection:
            device = self._find_device(connection, mqtt_device_id)
            self._mark_seen(connection, device["device_id"], reported_at, True)
            updated = connection.execute(
                text(
                    "UPDATE irrigation_records SET status = :status, executed_at = :executed_at "
                    "WHERE record_id = :record_id AND device_id = :device_id AND status = 'PENDING'"
                ),
                {"status": result.upper(), "executed_at": reported_at,
                 "record_id": int(command_id[3:]), "device_id": device["device_id"]},
            ).rowcount
            if updated and result == "failed":
                connection.execute(
                    text(
                        "INSERT INTO alerts "
                        "(plot_id, device_id, alert_type, alert_description) "
                        "VALUES (:plot_id, :device_id, 'IRRIGATION_FAILED', '灌溉设备执行指令失败')"
                    ),
                    {"plot_id": device["plot_id"], "device_id": device["device_id"]},
                )
        return {"kind": "command_result", "accepted": bool(updated)}
