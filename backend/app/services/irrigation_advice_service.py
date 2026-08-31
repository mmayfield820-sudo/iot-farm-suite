from __future__ import annotations

from typing import Any


def build_irrigation_advice(
    *,
    current_moisture: float | None,
    threshold: float | None,
    suggested_duration: int,
    stage_code: str | None,
    device_online: bool,
    weather: dict[str, Any],
    latest_irrigation_at: str | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    rain_probability = weather.get("rainProbability24h") if weather.get("available") else None
    if not device_online:
        decision = "CHECK_DEVICE"
        reasons.append("灌溉设备离线或心跳超时，请先检查设备")
    elif current_moisture is None or threshold is None:
        decision = "DATA_INSUFFICIENT"
        reasons.append("缺少有效土壤湿度或设备阈值数据")
    elif rain_probability is not None and float(rain_probability) >= 60:
        decision = "NO_IRRIGATION"
        reasons.append("未来24小时降雨概率较高，暂缓灌溉")
    elif current_moisture < threshold:
        decision = "IRRIGATE"
        reasons.append("当前湿度低于设备告警阈值")
        reasons.append("未来24小时降雨概率较低" if rain_probability is not None else "天气不可用，本次仅依据农田数据判断")
    else:
        decision = "NO_IRRIGATION"
        reasons.append("当前湿度不低于设备告警阈值")
    if device_online:
        reasons.append("灌溉设备在线")
    if not weather.get("available"):
        reasons.append("天气数据暂不可用，未参与本次建议")
    if latest_irrigation_at:
        reasons.append(f"最近一次灌溉控制时间：{latest_irrigation_at}")
    return {
        "decision": decision,
        "suggestedDuration": suggested_duration,
        "currentMoisture": current_moisture,
        "deviceThreshold": threshold,
        "stageCode": stage_code,
        "deviceOnline": device_online,
        "rainProbability24h": rain_probability,
        "weatherAvailable": bool(weather.get("available")),
        "reasons": reasons,
    }
