# WebSocket 实时事件

后端通过 WebSocket 向前端推送实时变化。连接地址为 `/api/ws/realtime`，连接时使用登录后的 JWT。

每条消息使用统一外层格式：

```json
{
  "event": "telemetry_updated",
  "ts": "2026-08-21T09:59:50Z",
  "data": {}
}
```

## 温湿度更新

事件名：`telemetry_updated`

```json
{
  "event": "telemetry_updated",
  "ts": "2026-08-21T09:59:50Z",
  "data": {
    "plotId": "P001",
    "deviceId": "D001",
    "type": "temperature",
    "value": 25.6,
    "unit": "C",
    "collectedAt": "2026-08-21T09:59:50Z"
  }
}
```

## 设备状态变化

事件名：`device_status_changed`。`status` 只能是 `online` 或 `offline`。

## 灌溉执行结果

事件名：`command_status_changed`。状态依次可能为 `pending`、`success`、`failed` 或 `timeout`。前端只能根据该事件显示最终结果，不能因为请求成功就直接显示“执行成功”。

## 新告警

事件名：`alert_created`，数据结构与 `contracts/openapi.yaml` 中的 `Alert` 一致。
