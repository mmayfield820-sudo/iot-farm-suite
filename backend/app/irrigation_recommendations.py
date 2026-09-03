from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite
from typing import Any


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) else None


def _minutes_since(value: datetime | None, now: datetime) -> float | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    if now.tzinfo is not None:
        now = now.astimezone(UTC).replace(tzinfo=None)
    return max(0.0, (now - value).total_seconds() / 60)


def _rounded_minutes(value: float) -> int:
    return max(5, min(120, int(round(value / 5) * 5)))


def target_moisture_reached(readings: list[Any], target_min: float | None, required_samples: int = 1) -> bool:
    """Return whether the latest required readings reached the target minimum."""
    lower = _number(target_min)
    if lower is None or required_samples < 1 or len(readings) < required_samples:
        return False
    values = [_number(value) for value in readings[:required_samples]]
    return all(value is not None and value >= lower for value in values)


def build_irrigation_recommendation(
    *,
    now: datetime,
    moisture: float | None,
    report_at: datetime | None,
    target_min: float | None,
    target_max: float | None,
    stage_name: str | None,
    device_bound: bool,
    device_online: bool,
    irrigation_active: bool,
    base_duration_minutes: int | None,
    minimum_interval_minutes: int | None,
    last_irrigation_at: datetime | None,
    last_irrigation_minutes: int | None,
    rain_probability: float | None,
    rainy_days: int,
    temperature: float | None,
    weather_available: bool,
) -> dict[str, Any]:
    """Return a deterministic, explainable irrigation recommendation."""
    moisture_value = _number(moisture)
    lower = _number(target_min)
    upper = _number(target_max)
    rain = _number(rain_probability)
    air_temperature = _number(temperature)
    report_age = _minutes_since(report_at, now)
    since_irrigation = _minutes_since(last_irrigation_at, now)
    interval = max(0, int(minimum_interval_minutes or 0))
    base_duration = max(5, min(120, int(base_duration_minutes or 30)))
    stage_label = stage_name or "当前阶段"

    inputs = {
        "moisture": moisture_value,
        "reportAt": report_at.isoformat() if report_at else None,
        "targetMin": lower,
        "targetMax": upper,
        "stageName": stage_name,
        "deviceBound": device_bound,
        "deviceOnline": device_online,
        "irrigationActive": irrigation_active,
        "baseDurationMinutes": base_duration,
        "minimumIntervalMinutes": interval,
        "lastIrrigationAt": last_irrigation_at.isoformat() if last_irrigation_at else None,
        "lastIrrigationMinutes": last_irrigation_minutes,
        "rainProbability": rain,
        "rainyDays": rainy_days,
        "temperature": air_temperature,
        "weatherAvailable": weather_available,
    }

    def result(decision: str, title: str, reasons: list[str], minutes: int | None = None) -> dict[str, Any]:
        return {
            "decision": decision,
            "title": title,
            "suggestedMinutes": minutes,
            "summary": "；".join(reasons),
            "reasons": reasons,
            "inputs": inputs,
            "ruleVersion": "irrigation-rules-v1",
            "evaluatedAt": now.isoformat(),
        }

    if not device_bound:
        return result("check_device", "暂不可灌溉", ["当前地块未绑定灌溉控制器，请先完成设备绑定"])
    if not device_online:
        return result("check_device", "暂不可灌溉", ["灌溉控制器当前离线，请先检查设备连接状态"])
    if moisture_value is None or report_at is None:
        return result("check_data", "暂无灌溉建议", ["当前缺少有效的土壤湿度数据，不能安全计算灌溉时长"])
    if report_age is not None and report_age > 30:
        return result("check_data", "暂无灌溉建议", [f"土壤湿度数据已超过 {int(report_age)} 分钟未更新，请先检查传感器"])
    if lower is None:
        return result("check_data", "暂无灌溉建议", ["当前生产阶段尚未配置土壤湿度目标下限"])
    if irrigation_active:
        return result("active", "正在灌溉", ["当前灌溉任务尚未结束，无需重复下发开启指令"])

    target_text = f"{stage_label}目标下限 {lower:g}%"
    if moisture_value >= lower:
        range_text = f"，目标区间为 {lower:g}%~{upper:g}%" if upper is not None else ""
        return result("no_irrigation", "当前无需灌溉", [f"土壤湿度 {moisture_value:g}% 已达到{target_text}{range_text}"])

    deficit = lower - moisture_value
    moisture_reason = f"土壤湿度 {moisture_value:g}% 低于{target_text}，缺口 {deficit:g} 个百分点"
    if weather_available and (rainy_days >= 2 or (rain is not None and rain >= 75)):
        weather_reason = f"已出现连续 {rainy_days} 天降雨" if rainy_days >= 2 else f"未来24小时最高降雨概率 {rain:g}%"
        return result("wait", "建议暂缓灌溉", [moisture_reason, f"{weather_reason}，优先等待降雨后重新评估"])

    recent_irrigation = since_irrigation is not None and interval > 0 and since_irrigation < interval
    if recent_irrigation and deficit < 10:
        remaining = max(1, int(round(interval - since_irrigation)))
        recent = f"距上次灌溉仅 {int(since_irrigation)} 分钟"
        if last_irrigation_minutes:
            recent += f"，上次执行 {last_irrigation_minutes} 分钟"
        return result("wait", "建议稍后复查", [moisture_reason, f"{recent}，建议 {remaining} 分钟后复测土壤湿度"])

    if deficit <= 3:
        deficit_factor = 0.5
    elif deficit <= 8:
        deficit_factor = 0.75
    elif deficit <= 15:
        deficit_factor = 1.0
    else:
        deficit_factor = 1.25

    factor = deficit_factor
    adjustments = [moisture_reason]
    if air_temperature is not None and air_temperature >= 32:
        factor *= 1.15
        adjustments.append(f"当前气温 {air_temperature:g}℃，高温条件适度增加补水量")
    if weather_available and rain is not None:
        if rain >= 40:
            factor *= 0.7
            adjustments.append(f"未来24小时最高降雨概率 {rain:g}%，已下调灌溉时长")
        else:
            adjustments.append(f"未来24小时最高降雨概率 {rain:g}%，暂无明显降雨影响")
    else:
        adjustments.append("天气数据暂不可用，本次未使用降雨修正")
    if recent_irrigation:
        factor *= 0.75
        adjustments.append(f"距上次灌溉 {int(since_irrigation)} 分钟，已降低本次建议时长")
    elif since_irrigation is not None:
        adjustments.append(f"距上次灌溉约 {int(since_irrigation)} 分钟")
    else:
        adjustments.append("近期没有可用灌溉记录")

    minutes = _rounded_minutes(base_duration * factor)
    adjustments.append(f"最长运行时间以 {base_duration} 分钟为基准，动态修正为 {minutes} 分钟")
    return result("irrigate", "建议按目标湿度自动灌溉", adjustments, minutes)
