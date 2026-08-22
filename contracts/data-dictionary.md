# 数据字典

## 编号

| 字段 | 规则 | 示例 |
|---|---|---|
| 用户 ID | `U` 加序号 | `U001` |
| 农场 ID | `F` 加序号 | `F001` |
| 地块 ID | `P` 加序号 | `P001` |
| 数据库设备 ID | `D` 加序号 | `D001` |
| 设备业务编号 | `SENSOR-` 加序号 | `SENSOR-001` |
| MQTT 通信标识 | `device_` 加序号 | `device_001` |

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

所有时间统一使用 ISO 8601 格式，并尽量使用 UTC，例如 `2026-08-21T09:59:50Z`。遥测消息中的 `ts` 是设备采集时间，数据库另存后端收到消息的时间。
