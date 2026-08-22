# 统一错误码

接口失败时返回：

```json
{
  "code": "DEVICE_NOT_FOUND",
  "message": "设备不存在",
  "requestId": "req-123"
}
```

| 错误码 | 含义 | HTTP 状态 |
|---|---|---:|
| `INVALID_REQUEST` | 请求参数错误 | 400 |
| `UNAUTHORIZED` | 未登录或令牌无效 | 401 |
| `FORBIDDEN` | 没有访问权限 | 403 |
| `RESOURCE_NOT_FOUND` | 资源不存在 | 404 |
| `DEVICE_NOT_FOUND` | 设备未注册 | 404 |
| `DEVICE_OFFLINE` | 设备当前离线 | 409 |
| `COMMAND_TIMEOUT` | 指令执行超时 | 504 |
| `MQTT_UNAVAILABLE` | MQTT 服务暂不可用 | 503 |
| `INTERNAL_ERROR` | 未预期的服务器错误 | 500 |
