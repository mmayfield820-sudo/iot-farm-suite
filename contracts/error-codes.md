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
| `INVALID_ID_CARD_NO` | 身份证号格式或校验位无效 | 400 |
| `FIRST_LOGIN_INVALID` | 首次登录资料设置令牌无效或账号状态已变化 | 400 |
| `PASSWORD_MUST_CHANGE` | 正式密码不能继续使用身份证号后六位初始密码 | 400 |
| `UNAUTHORIZED` | 未登录或令牌无效 | 401 |
| `FORBIDDEN` | 没有访问权限 | 403 |
| `RESOURCE_NOT_FOUND` | 资源不存在 | 404 |
| `DEVICE_NOT_FOUND` | 设备未注册 | 404 |
| `EMPLOYEE_NO_OR_ID_CARD_EXISTS` | 工号或身份证号已存在 | 409 |
| `PLOT_CODE_EXISTS` | 地块编号已存在 | 409 |
| `PLOT_ALREADY_ASSIGNED` | 地块已分配给其他农户负责人 | 409 |
| `DEVICE_OFFLINE` | 设备当前离线 | 409 |
| `COMMAND_TIMEOUT` | 指令执行超时 | 504 |
| `MQTT_UNAVAILABLE` | MQTT 服务暂不可用 | 503 |
| `IMPORT_VALIDATION_FAILED` | Excel 预校验存在失败行，不能确认导入 | 422 |
| `INVALID_REMINDER_STATUS` | 计划调整提醒状态参数无效 | 400 |
| `INVALID_REMINDER_DISPOSITION` | 提醒处置方式无效 | 400 |
| `REMINDER_NOT_FOUND` | 计划调整提醒不存在 | 404 |
| `REMINDER_NOT_ACTIONABLE` | 提醒已处置或已恢复，不能再次处置 | 409 |
| `INTERNAL_ERROR` | 未预期的服务器错误 | 500 |

| TEMPLATE_NOT_FOUND | Requested crop template or draft does not exist. | 404 |
| TEMPLATE_EDIT_WINDOW_CLOSED | Harvest cleanup is incomplete or the next cycle has begun. | 409 |
| INVALID_TEMPLATE_DEFINITION | Template stages or task rules are invalid. | 400 |
| TEMPLATE_DRAFT_EXISTS | This farm already has an unpublished draft for the template. | 409 |

| PLANTING_PROFILE_REQUIRED | The farm production profile must be set before plans can be generated. | 409 |
| PLANTING_PROFILE_NOT_FOUND | The farm production profile has not been set for the requested plot. | 404 |
| PLAN_EXISTS | Active plans already exist; set regenerate to true to replace them. | 409 |

| TASK_NOT_FOUND | Requested management task does not exist. | 404 |
| TASK_NOT_ADJUSTABLE | Completed, cancelled, or superseded task cannot be changed. | 409 |
