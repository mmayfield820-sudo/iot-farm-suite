"""定期处理 MQTT 设备离线和灌溉指令超时。"""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from threading import Event, Thread

from sqlalchemy import text
from sqlalchemy.engine import Engine


logger = logging.getLogger(__name__)


class MqttHealthMonitor:
    """后台巡检任务；所有状态变化均由数据库事务保证。"""

    def __init__(
        self, engine: Engine, offline_after_seconds: int,
        command_timeout_seconds: int, interval_seconds: int,
    ) -> None:
        self._engine = engine
        self._offline_after_seconds = offline_after_seconds
        self._command_timeout_seconds = command_timeout_seconds
        self._interval_seconds = interval_seconds
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, name="mqtt-health-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._interval_seconds + 1)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("MQTT health monitor failed")
            self._stop_event.wait(self._interval_seconds)

    def run_once(self, now: datetime | None = None) -> dict[str, int]:
        """执行一次巡检，返回本次新离线和新超时的数量。"""
        now = now or datetime.now()
        offline_before = now - timedelta(seconds=self._offline_after_seconds)
        command_before = now - timedelta(seconds=self._command_timeout_seconds)
        with self._engine.begin() as connection:
            offline_devices = connection.execute(
                text(
                    "SELECT device_id, plot_id FROM devices "
                    "WHERE status = 'ONLINE' AND last_heartbeat < :offline_before"
                ),
                {"offline_before": offline_before},
            ).mappings().all()
            if offline_devices:
                connection.execute(
                    text(
                        "UPDATE devices SET status = 'OFFLINE' "
                        "WHERE status = 'ONLINE' AND last_heartbeat < :offline_before"
                    ),
                    {"offline_before": offline_before},
                )
                for device in offline_devices:
                    if device["plot_id"] is not None:
                        self._create_device_offline_alert(connection, device)

            timed_out_commands = connection.execute(
                text(
                    "SELECT record_id, plot_id, device_id FROM irrigation_records "
                    "WHERE status = 'PENDING' AND requested_at < :command_before"
                ),
                {"command_before": command_before},
            ).mappings().all()
            if timed_out_commands:
                connection.execute(
                    text(
                        "UPDATE irrigation_records SET status = 'TIMEOUT', executed_at = :now "
                        "WHERE status = 'PENDING' AND requested_at < :command_before"
                    ),
                    {"command_before": command_before, "now": now},
                )
                for command in timed_out_commands:
                    self._create_irrigation_failed_alert(connection, command, "灌溉控制指令执行超时")

        return {"offlineDevices": len(offline_devices), "timedOutCommands": len(timed_out_commands)}

    @staticmethod
    def _create_device_offline_alert(connection: object, device: dict) -> None:
        connection.execute(
            text(
                "INSERT INTO alerts "
                "(plot_id, device_id, alert_type, alert_description) "
                "SELECT :plot_id, :device_id, 'DEVICE_OFFLINE', '设备心跳长时间未更新' "
                "WHERE NOT EXISTS (SELECT 1 FROM alerts a "
                "WHERE a.device_id = :device_id AND a.alert_type = 'DEVICE_OFFLINE' "
                "AND a.alert_status = 'UNHANDLED')"
            ),
            {"plot_id": device["plot_id"], "device_id": device["device_id"]},
        )

    @staticmethod
    def _create_irrigation_failed_alert(connection: object, command: dict, description: str) -> None:
        connection.execute(
            text(
                "INSERT INTO alerts "
                "(plot_id, device_id, alert_type, alert_description) "
                "VALUES (:plot_id, :device_id, 'IRRIGATION_FAILED', :description)"
            ),
            {
                "plot_id": command["plot_id"], "device_id": command["device_id"],
                "description": description,
            },
        )
