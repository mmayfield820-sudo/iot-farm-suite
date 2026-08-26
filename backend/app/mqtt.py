from __future__ import annotations

import json
import logging
import math
import os
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import paho.mqtt.client as mqtt
from sqlalchemy import text

from .db import engine, utc_isoformat


logger = logging.getLogger(__name__)
_TELEMETRY_TYPES = {"temperature", "humidity"}
_CONTROL_ACK_RESULTS = {"ok", "failed"}
_SWITCH_VALUES = {"on", "off"}


@dataclass(frozen=True)
class Reading:
    device_id: int
    value: float
    timestamp: datetime
    received_at: datetime


class MqttService:
    def __init__(self) -> None:
        self.host = os.getenv("MQTT_HOST", "127.0.0.1")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.pair_timeout_seconds = int(
            os.getenv("TELEMETRY_PAIR_TIMEOUT_SECONDS", "30")
        )
        self.command_ack_timeout_seconds = int(
            os.getenv("COMMAND_ACK_TIMEOUT_SECONDS", "30")
        )
        self._readings: dict[int, dict[str, Reading]] = {}
        self._reading_lock = threading.Lock()
        self._command_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._sweeper: threading.Thread | None = None
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="smart-farm-backend",
        )
        username = os.getenv("MQTT_USERNAME", "")
        if username:
            self.client.username_pw_set(username, os.getenv("MQTT_PASSWORD", ""))
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self) -> None:
        self._stop_event.clear()
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.client.connect_async(self.host, self.port, keepalive=60)
        self.client.loop_start()
        self._sweeper = threading.Thread(
            target=self._expire_unpaired_readings,
            name="mqtt-reading-sweeper",
            daemon=True,
        )
        self._sweeper.start()

    def stop(self) -> None:
        self._stop_event.set()
        self.client.loop_stop()
        self.client.disconnect()
        if self._sweeper is not None:
            self._sweeper.join(timeout=2)

    def _on_connect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _flags: Any,
        reason_code: Any,
        _properties: Any,
    ) -> None:
        if reason_code != 0:
            logger.error("MQTT connection refused: %s", reason_code)
            return
        self.client.subscribe(
            [
                ("sensor/+/data", 1),
                ("sensor/state", 1),
                ("sensor/heartbeat", 1),
                ("sensor/ack", 1),
            ]
        )
        logger.info("Connected to MQTT broker %s:%s", self.host, self.port)

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _disconnect_flags: Any,
        reason_code: Any,
        _properties: Any,
    ) -> None:
        if reason_code != 0 and not self._stop_event.is_set():
            logger.warning("MQTT disconnected; reconnecting: %s", reason_code)

    def _on_message(self, _client: mqtt.Client, _userdata: Any, message: Any) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            if not isinstance(payload, dict):
                return
            parts = message.topic.split("/")
            if len(parts) == 3 and parts[0] == "sensor" and parts[2] == "data":
                topic_uuid = self._parse_device_uuid(parts[1])
                payload_uuid = self._parse_device_uuid(payload.get("deviceId"))
                if payload_uuid != topic_uuid:
                    logger.warning("Rejected data with mismatched topic and deviceId")
                    return
                self._handle_telemetry(topic_uuid, payload)
            elif message.topic == "sensor/state":
                self._handle_state(payload)
            elif message.topic == "sensor/heartbeat":
                self._handle_heartbeat(payload)
            elif message.topic == "sensor/ack":
                self._handle_ack(payload)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            logger.warning("Rejected malformed MQTT message on %s: %s", message.topic, error)
        except Exception:
            logger.exception("Failed to process MQTT message on %s", message.topic)

    def _handle_state(self, payload: dict[str, Any]) -> None:
        device_uuid = self._parse_device_uuid(payload["deviceId"])
        self._parse_sequence(payload["seq"], "seq")
        timestamp = self._parse_timestamp(payload["ts"])
        self._parse_switch(payload["switch"])
        if payload.get("reason") not in {"local", "remote", "auto", "heartbeat"}:
            raise ValueError("unsupported state reason")
        if not isinstance(payload.get("values"), dict):
            raise ValueError("state values must be an object")
        with engine.begin() as connection:
            self._touch_device(connection, device_uuid, timestamp)

    def _handle_heartbeat(self, payload: dict[str, Any]) -> None:
        self._parse_sequence(payload["seq"], "seq")
        timestamp = self._parse_timestamp(payload["ts"])
        if payload.get("type") != "snapshot":
            raise ValueError("heartbeat type must be snapshot")
        sensors = payload["sensors"]
        if not isinstance(sensors, list):
            raise ValueError("sensors must be an array")
        with engine.begin() as connection:
            for snapshot in sensors:
                if not isinstance(snapshot, dict):
                    raise ValueError("heartbeat sensor entries must be objects")
                if not snapshot.get("deviceId"):
                    raise ValueError("heartbeat sensor deviceId is required")
                self._parse_switch(snapshot["switch"])
                if not isinstance(snapshot.get("name"), str) or not snapshot["name"].strip():
                    raise ValueError("heartbeat sensor name is required")
                if not isinstance(snapshot.get("values"), dict):
                    raise ValueError("heartbeat sensor values must be an object")
                self._touch_device(
                    connection,
                    self._parse_device_uuid(snapshot["deviceId"]),
                    timestamp,
                )

    def _handle_telemetry(self, device_uuid: str, payload: dict[str, Any]) -> None:
        payload_device_uuid = self._parse_device_uuid(payload["deviceId"])
        if payload_device_uuid != device_uuid:
            raise ValueError("topic UUID and payload deviceId differ")
        metric_type, value = self._parse_telemetry_value(payload)
        if metric_type == "humidity" and not 0 <= value <= 100:
            raise ValueError("humidity must be between 0 and 100")
        if not math.isfinite(value):
            raise ValueError("telemetry metric must be finite")
        message_id = self._parse_message_id(payload["msgId"])
        timestamp = self._parse_timestamp(payload["timestamp"])

        with engine.begin() as connection:
            device = self._find_device(
                connection,
                device_uuid,
                metric_type,
            )
            if device is None:
                logger.warning("Ignored telemetry from unknown or mismatched device %s", device_uuid)
                return

            inserted = connection.execute(
                text(
                    """
                    INSERT IGNORE INTO mqtt_telemetry_message (device_id, message_id)
                    VALUES (:device_id, :message_id)
                    """
                ),
                {"device_id": device["device_id"], "message_id": message_id},
            )
            if inserted.rowcount == 0:
                return

            connection.execute(
                text(
                    """
                    UPDATE device
                    SET status = 'online', last_heartbeat = :last_heartbeat
                    WHERE device_id = :device_id
                    """
                ),
                {
                    "last_heartbeat": timestamp,
                    "device_id": device["device_id"],
                },
            )

        reading = Reading(
            device_id=device["device_id"],
            value=value,
            timestamp=timestamp,
            received_at=datetime.now(UTC).replace(tzinfo=None),
        )
        self._store_reading(device["plot_id"], metric_type, reading)

    def _handle_ack(self, payload: dict[str, Any]) -> None:
        action = payload.get("action")
        if action == "control":
            self._handle_command_result(payload)
        elif action == "query":
            self._handle_query_ack(payload)
        elif action == "queryAll":
            self._handle_query_all_ack(payload)
        elif action == "error":
            logger.warning("Simulator rejected MQTT command: %s", payload.get("message"))
        else:
            raise ValueError("unsupported ACK action")

    def _handle_command_result(self, payload: dict[str, Any]) -> None:
        self._parse_sequence(payload["seq"], "seq")
        device_uuid = self._parse_device_uuid(payload["deviceId"])
        command_id = str(self._parse_sequence(payload["cmdSeq"], "cmdSeq"))
        result = payload["result"]
        if result not in _CONTROL_ACK_RESULTS:
            raise ValueError("unsupported control ACK result")
        switch = self._parse_switch(payload["switch"])
        timestamp = datetime.now(UTC).replace(tzinfo=None)

        with engine.begin() as connection:
            device = self._find_device(connection, device_uuid, "irrigation")
            if device is None:
                logger.warning("Ignored command result from unknown device %s", device_uuid)
                return
            self._touch_device(connection, device_uuid, timestamp, device)

            updated = connection.execute(
                text(
                    """
                    UPDATE irrigation_record
                    SET status = :status, executed_at = :executed_at
                    WHERE command_id = :command_id
                      AND device_id = :device_id
                      AND action_type = :action_type
                      AND status = 'pending'
                    """
                ),
                {
                    "status": "success" if result == "ok" else "failed",
                    "executed_at": timestamp,
                    "command_id": command_id,
                    "device_id": device["device_id"],
                    "action_type": switch,
                },
            )
            if updated.rowcount == 0:
                logger.warning("Ignored result for unknown or completed command %s", command_id)
                return

            if result == "failed":
                self._open_alert(
                    connection,
                    plot_id=device["plot_id"],
                    device_id=device["device_id"],
                    alert_type="irrigation_failed",
                    description=f"Irrigation command {command_id} failed",
                    timestamp=timestamp,
                )

    def publish_control_command(
        self,
        *,
        device_uuid: str,
        switch: str,
        operator_id: int | None = None,
        activation_type: str = "manual",
    ) -> dict[str, Any]:
        """Publish an irrigation command and wait for the device ACK to settle it."""
        device_uuid = self._parse_device_uuid(device_uuid)
        switch = self._parse_switch(switch)
        if activation_type not in {"manual", "auto"}:
            raise ValueError("activation_type must be manual or auto")
        requested_at = datetime.now(UTC).replace(tzinfo=None)

        with self._command_lock, engine.begin() as connection:
            device = self._find_device(connection, device_uuid, "irrigation")
            if device is None:
                raise ValueError("irrigation device not found")
            max_sequence = connection.execute(
                text(
                    """
                    SELECT COALESCE(MAX(CAST(command_id AS UNSIGNED)), 0)
                    FROM irrigation_record
                    WHERE command_id REGEXP '^[0-9]+$'
                    """
                )
            ).scalar_one()
            sequence = int(max_sequence) + 1
            command_id = str(sequence)
            connection.execute(
                text(
                    """
                    INSERT INTO irrigation_record (
                        command_id, plot_id, device_id, action_type,
                        activation_type, operator_id, requested_at, status
                    ) VALUES (
                        :command_id, :plot_id, :device_id, :action_type,
                        :activation_type, :operator_id, :requested_at, 'pending'
                    )
                    """
                ),
                {
                    "command_id": command_id,
                    "plot_id": device["plot_id"],
                    "device_id": device["device_id"],
                    "action_type": switch,
                    "activation_type": activation_type,
                    "operator_id": operator_id,
                    "requested_at": requested_at,
                },
            )

        payload = {
            "seq": sequence,
            "ts": int(requested_at.replace(tzinfo=UTC).timestamp() * 1000),
            "deviceId": device_uuid,
            "switch": switch,
        }
        result = self.client.publish("sensor/cmd", json.dumps(payload), qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        UPDATE irrigation_record
                        SET status = 'failed', executed_at = :executed_at
                        WHERE command_id = :command_id AND status = 'pending'
                        """
                    ),
                    {"command_id": command_id, "executed_at": datetime.now(UTC).replace(tzinfo=None)},
                )
            raise RuntimeError(f"MQTT publish failed: {result.rc}")
        result.wait_for_publish()
        return {
            "commandId": command_id,
            "seq": sequence,
            "deviceUuid": device_uuid,
            "switch": switch,
            "status": "pending",
            "requestedAt": utc_isoformat(requested_at),
        }

    def _handle_query_ack(self, payload: dict[str, Any]) -> None:
        self._parse_sequence(payload["seq"], "seq")
        device_uuid = self._parse_device_uuid(payload["deviceId"])
        self._parse_sequence(payload["cmdSeq"], "cmdSeq")
        self._parse_switch(payload["switch"])
        with engine.begin() as connection:
            self._touch_device(
                connection,
                device_uuid,
                datetime.now(UTC).replace(tzinfo=None),
            )

    def _handle_query_all_ack(self, payload: dict[str, Any]) -> None:
        self._parse_sequence(payload["seq"], "seq")
        self._parse_sequence(payload["cmdSeq"], "cmdSeq")
        sensors = payload["sensors"]
        if not isinstance(sensors, list):
            raise ValueError("queryAll sensors must be an array")
        timestamp = datetime.now(UTC).replace(tzinfo=None)
        with engine.begin() as connection:
            for sensor in sensors:
                if not isinstance(sensor, dict):
                    continue
                self._touch_device(
                    connection,
                    self._parse_device_uuid(sensor["deviceId"]),
                    timestamp,
                )

    def _store_reading(self, plot_id: int, metric_type: str, reading: Reading) -> None:
        with self._reading_lock:
            readings = self._readings.setdefault(plot_id, {})
            readings[metric_type] = reading
            temperature = readings.get("temperature")
            humidity = readings.get("humidity")
            if temperature is None or humidity is None:
                return
            if abs((temperature.timestamp - humidity.timestamp).total_seconds()) > self.pair_timeout_seconds:
                return
            del self._readings[plot_id]

        self._save_report(plot_id, temperature, humidity)

    def _save_report(
        self, plot_id: int, temperature: Reading, humidity: Reading
    ) -> None:
        report_time = max(temperature.timestamp, humidity.timestamp)
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO plot_report (
                        plot_id, soil_moisture_device_id, temperature_device_id,
                        plot_moisture, temperature, report_datetime
                    )
                    VALUES (
                        :plot_id, :humidity_device_id, :temperature_device_id,
                        :humidity, :temperature, :report_datetime
                    )
                    """
                ),
                {
                    "plot_id": plot_id,
                    "humidity_device_id": humidity.device_id,
                    "temperature_device_id": temperature.device_id,
                    "humidity": humidity.value,
                    "temperature": temperature.value,
                    "report_datetime": report_time,
                },
            )

            threshold = connection.execute(
                text(
                    """
                    SELECT soil_moisture_threshold
                    FROM threshold_config
                    WHERE plot_id = :plot_id
                    """
                ),
                {"plot_id": plot_id},
            ).scalar()

            if threshold is not None and humidity.value < float(threshold):
                self._open_alert(
                    connection,
                    plot_id=plot_id,
                    device_id=humidity.device_id,
                    alert_type="low_moisture",
                    description="Soil moisture is below the configured threshold",
                    timestamp=report_time,
                    value=humidity.value,
                    threshold=float(threshold),
                )
            else:
                connection.execute(
                    text(
                        """
                        UPDATE alert
                        SET alert_status = 'recovered', handled_at = :handled_at
                        WHERE plot_id = :plot_id
                          AND alert_type = 'low_moisture'
                          AND alert_status = 'active'
                        """
                    ),
                    {"plot_id": plot_id, "handled_at": report_time},
                )

    def _expire_unpaired_readings(self) -> None:
        while not self._stop_event.wait(5):
            try:
                now = datetime.now(UTC).replace(tzinfo=None)
                expired: list[tuple[int, str, Reading]] = []
                with self._reading_lock:
                    for plot_id, readings in list(self._readings.items()):
                        for metric_type, reading in list(readings.items()):
                            if (now - reading.received_at).total_seconds() >= self.pair_timeout_seconds:
                                expired.append((plot_id, metric_type, reading))
                                del readings[metric_type]
                        if not readings:
                            del self._readings[plot_id]

                for plot_id, metric_type, _reading in expired:
                    missing_type = (
                        "humidity" if metric_type == "temperature" else "temperature"
                    )
                    self._record_missing_reading_alert(plot_id, missing_type, now)
                self._expire_pending_commands(now)
            except Exception:
                logger.exception("Failed to run MQTT timeout checks")

    def _expire_pending_commands(self, timestamp: datetime) -> None:
        cutoff = timestamp.timestamp() - self.command_ack_timeout_seconds
        cutoff_datetime = datetime.fromtimestamp(cutoff, UTC).replace(tzinfo=None)
        with engine.begin() as connection:
            pending = connection.execute(
                text(
                    """
                    SELECT record_id, command_id, plot_id, device_id
                    FROM irrigation_record
                    WHERE status = 'pending' AND requested_at < :cutoff
                    """
                ),
                {"cutoff": cutoff_datetime},
            ).mappings().all()
            for command in pending:
                updated = connection.execute(
                    text(
                        """
                        UPDATE irrigation_record
                        SET status = 'timeout', executed_at = :timestamp
                        WHERE record_id = :record_id AND status = 'pending'
                        """
                    ),
                    {"timestamp": timestamp, "record_id": command["record_id"]},
                )
                if updated.rowcount:
                    self._open_alert(
                        connection,
                        plot_id=command["plot_id"],
                        device_id=command["device_id"],
                        alert_type="irrigation_failed",
                        description=f"Irrigation command {command['command_id']} timed out",
                        timestamp=timestamp,
                    )

    def _record_missing_reading_alert(
        self, plot_id: int, missing_type: str, timestamp: datetime
    ) -> None:
        with engine.begin() as connection:
            missing_device = connection.execute(
                text(
                    """
                    SELECT device_id
                    FROM device
                    WHERE plot_id = :plot_id AND device_type = :device_type
                    """
                ),
                {"plot_id": plot_id, "device_type": missing_type},
            ).mappings().first()
            self._open_alert(
                connection,
                plot_id=plot_id,
                device_id=missing_device["device_id"] if missing_device else None,
                alert_type="device_fault",
                description=f"Missing paired {missing_type} reading",
                timestamp=timestamp,
            )

    def _open_alert(
        self,
        connection: Any,
        *,
        plot_id: int,
        device_id: int | None,
        alert_type: str,
        description: str,
        timestamp: datetime,
        value: float | None = None,
        threshold: float | None = None,
    ) -> None:
        existing = connection.execute(
            text(
                """
                SELECT alert_id
                FROM alert
                WHERE plot_id = :plot_id
                  AND device_id <=> :device_id
                  AND alert_type = :alert_type
                  AND alert_status = 'active'
                LIMIT 1
                """
            ),
            {
                "plot_id": plot_id,
                "device_id": device_id,
                "alert_type": alert_type,
            },
        ).scalar()
        if existing is None:
            connection.execute(
                text(
                    """
                    INSERT INTO alert (
                        plot_id, device_id, alert_type, alert_description,
                        alert_value, alert_threshold, alert_datetime, alert_status
                    )
                    VALUES (
                        :plot_id, :device_id, :alert_type, :description,
                        :value, :threshold, :timestamp, 'active'
                    )
                    """
                ),
                {
                    "plot_id": plot_id,
                    "device_id": device_id,
                    "alert_type": alert_type,
                    "description": description,
                    "value": value,
                    "threshold": threshold,
                    "timestamp": timestamp,
                },
            )

    @staticmethod
    def _find_device(
        connection: Any,
        device_uuid: str,
        device_type: str | None = None,
    ) -> Any:
        device = connection.execute(
            text(
                """
                SELECT device_id, device_code, device_type, plot_id
                FROM device
                WHERE device_uuid = :device_uuid
                """
            ),
            {"device_uuid": device_uuid},
        ).mappings().first()
        if device is None:
            return None
        if device_type is not None and device["device_type"] != device_type:
            return None
        return device

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("ts/timestamp must be a Unix milliseconds timestamp")
        if value <= 0:
            raise ValueError("ts/timestamp must be positive")
        return datetime.fromtimestamp(value / 1000, UTC).replace(tzinfo=None)

    @staticmethod
    def _parse_device_uuid(value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("deviceId must be a UUID string")
        try:
            return str(UUID(value))
        except (ValueError, AttributeError) as error:
            raise ValueError("deviceId must be a valid UUID") from error

    @staticmethod
    def _parse_sequence(value: Any, field: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
        return value

    @staticmethod
    def _parse_switch(value: Any) -> str:
        if value not in _SWITCH_VALUES:
            raise ValueError("switch must be on or off")
        return value

    @staticmethod
    def _parse_message_id(value: Any) -> str:
        if not isinstance(value, (str, int)) or isinstance(value, bool):
            raise ValueError("msgId must be a string or integer")
        message_id = str(value).strip()
        if not message_id or len(message_id) > 100:
            raise ValueError("msgId must contain 1 to 100 characters")
        return message_id

    @staticmethod
    def _parse_telemetry_value(payload: dict[str, Any]) -> tuple[str, float]:
        metric_fields = {
            "temperature": "temperature",
            "plot_moisture": "humidity",
        }
        present = [field for field in metric_fields if field in payload]
        if len(present) != 1:
            raise ValueError("telemetry must contain exactly one metric")
        raw_value = payload[present[0]]
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise ValueError("telemetry metric must be numeric")
        return metric_fields[present[0]], float(raw_value)

    def _touch_device(
        self,
        connection: Any,
        device_uuid: str,
        timestamp: datetime,
        device: Any = None,
    ) -> Any:
        device = device or self._find_device(connection, device_uuid)
        if device is None:
            logger.warning("Ignored message from unknown device %s", device_uuid)
            return None
        connection.execute(
            text(
                """
                UPDATE device
                SET status = 'online', last_heartbeat = :last_heartbeat
                WHERE device_id = :device_id
                """
            ),
            {"last_heartbeat": timestamp, "device_id": device["device_id"]},
        )
        return device
