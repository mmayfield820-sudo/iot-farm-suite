# 数据字典

## 编号

| 字段 | 规则 | 示例 |
|---|---|---|
| 用户 ID | `U` 加序号 | `U001` |
| 农场 ID | `F` 加序号 | `F001` |
| 地块 ID | `P` 加序号 | `P001` |
| 数据库设备 ID | `D` 加序号 | `D001` |
| 设备业务编号 | 地块 ID 加设备类型后缀 | `P001-TEMP` |
| MQTT 通信标识 | UUID，对应 `device.device_uuid` | `3b8dcefd-3a51-4adc-b452-47c184c0951d` |

## 设备类型

| 值 | 含义 | 单位 |
|---|---|---|
| `temperature` | 温度传感器 | 摄氏度 `C` |
| `humidity` | 土壤湿度传感器 | 百分比 `%` |
| `irrigation` | 灌溉设备 | 无 |

## 状态值

- 设备状态：`online`、`offline`
- 控制指令状态：`pending`、`success`、`failed`、`timeout`
- 告警状态：`active`、`acknowledged`、`recovered`
- 用户角色：`farmer`、`farm_admin`、`system_admin`

## 时间约定

- 数据库统一保存 UTC。MySQL `DATETIME` 没有时区元数据，但本项目约定其中的值均为 UTC。
- MQTT 的 `ts`、`timestamp` 是 Unix 毫秒时间戳，按 UTC 解析。
- API 返回的时间统一使用带 `Z` 的 ISO 8601 UTC 格式，例如 `2026-08-25T06:04:21Z`；不能返回没有时区标识的时间字符串。
- 前端拿到 API 时间后，按 `Asia/Shanghai` 转换后展示给用户，不修改 API 原始值。
- 遥测消息中的采集时间与后端收到消息的时间是两个概念，数据库分别按对应字段保存。
