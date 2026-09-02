# MQTT 协议与数据库映射（鸿蒙模拟器）

本文件以鸿蒙模拟器的原生 topic、当前 MySQL 表结构为准。`deviceId` 始终表示模拟器 UUID，对应 `device.device_uuid`；它不是数据库主键 `device_id`，也不是业务编号 `device_code`。

## 1. 标识与通用规则

| 概念 | 示例 | 用途 |
|---|---|---|
| 数据库设备 ID | `D001` | HTTP 返回用的内部业务显示 ID；不进入 MQTT |
| `device_code` | `P001-TEMP` | 人工填写、设备展示和运维核对 |
| `device_uuid` / MQTT `deviceId` | `3b8dcefd-3a51-4adc-b452-47c184c0951d` | MQTT topic 和 payload 的唯一设备标识 |
| `seq` | `101` | 模拟器全局递增序列号；控制幂等和 ACK 关联 |
| `msgId` | `1787625267746` | 单台传感器遥测消息 ID；数据库去重 |

- 设备上线前，管理员必须将模拟器 UUID 填入 `device.device_uuid`，并同时登记正确的 `device_code`、`device_type`、`plot_id`。
- 后端收到 `sensor/{uuid}/data` 时，topic 内 UUID 必须等于 payload 的 `deviceId`；不一致直接拒绝。
- 所有 `ts`、`timestamp` 均为 Unix 毫秒时间戳（UTC）。
- `name`、`device_code` 是展示信息，不能用于身份认证；后端只依 UUID 查 `device` 表。

## 2. Topic 总览

| Topic | 方向 | 设备范围 | 数据库作用 |
|---|---|---|---|
| `sensor/{deviceId}/data` | 设备 → 后端 | 温度、湿度传感器 | 去重并生成 `plot_report` |
| `sensor/state` | 设备 → 后端 | 全部设备 | 更新设备在线时间 |
| `sensor/heartbeat` | 设备 → 后端 | 全部设备 | 批量更新设备在线时间 |
| `sensor/cmd` | 后端 → 模拟器 | 全部设备 | 灌溉控制时创建/下发 `irrigation_record` |
| `sensor/ack` | 模拟器 → 后端 | 全部设备 | 回写灌溉指令状态或返回查询结果 |

## 3. 信息流 A：温度数据上报

- Topic：`sensor/3b8dcefd-3a51-4adc-b452-47c184c0951d/data`
- 设备类型：`device.device_type = 'temperature'`
- 模拟器 Payload 模板：

```json
{
  "temperature": 25,
  "deviceId": "${deviceId}",
  "timestamp": ${timestamp},
  "msgId": "${timestamp}"
}
```

| 字段 | 必填 | 说明 | 数据库去向 |
|---|---:|---|---|
| `temperature` | 是 | 温度，单位 ℃ | 配对后写 `plot_report.temperature` |
| `deviceId` | 是 | 温度设备 UUID | 查询 `device.device_uuid` |
| `timestamp` | 是 | 采集时刻，毫秒 UTC | 配对后写 `plot_report.report_datetime` |
| `msgId` | 是 | 本设备唯一的遥测消息 ID | 写 `mqtt_telemetry_message.message_id` 去重 |

`msgId` 使用 `${timestamp}` 是因为模拟器模板已提供该变量；同一设备每次上报的时间戳必须不同。不能省略它，否则 MQTT 的 QoS 1 重投可能重复写入报告。

## 4. 信息流 B：土壤湿度数据上报

- Topic：`sensor/814621f7-2561-49ad-9766-72d3fcd18d86/data`
- 设备类型：`device.device_type = 'humidity'`
- 模拟器 Payload 模板：

```json
{
  "plot_moisture": 40,
  "deviceId": "${deviceId}",
  "timestamp": ${timestamp},
  "msgId": "${timestamp}"
}
```

| 字段 | 必填 | 说明 | 数据库去向 |
|---|---:|---|---|
| `plot_moisture` | 是 | 土壤湿度，范围 0–100，单位 % | 配对后写 `plot_report.plot_moisture` |
| `deviceId` | 是 | 湿度设备 UUID | 查询 `device.device_uuid` |
| `timestamp` | 是 | 采集时刻，毫秒 UTC | 配对后写 `plot_report.report_datetime` |
| `msgId` | 是 | 本设备唯一的遥测消息 ID | 写 `mqtt_telemetry_message.message_id` 去重 |

温度和湿度须属于同一 `plot_id`，且采集时间差不超过 `TELEMETRY_PAIR_TIMEOUT_SECONDS`（当前 30 秒）。两条都存在才插入一条 `plot_report`；只到一条且超时则创建 `alert.alert_type = 'device_fault'`。

## 5. 信息流 C：设备状态广播

- Topic：`sensor/state`
- 触发：本地开关、远程控制、自动变化、重连后的状态同步。

```json
{
  "seq": 2783,
  "ts": 1787625476220,
  "deviceId": "435106ba-01e7-4745-9646-3907d15b28df",
  "switch": "on",
  "reason": "local",
  "values": {}
}
```

| 字段 | 必填 | 说明 |
|---|---:|---|
| `seq` | 是 | 状态消息序列号 |
| `ts` | 是 | 状态产生时间，毫秒 UTC |
| `deviceId` | 是 | 设备 UUID |
| `switch` | 是 | `on` / `off`，表示设备功能或上报开关，不等同于 MQTT 在线状态 |
| `reason` | 是 | `local` / `remote` / `auto` / `heartbeat` |
| `values` | 是 | 当前业务值对象；马达为空对象 `{}` |

数据库映射：后端以 `deviceId` 找到设备，更新 `device.status = 'online'`、`device.last_heartbeat = ts`、`device.switch_state = switch` 和 `device.switch_changed_at = ts`。灌溉设备以该状态作为实时真相源；`reason = local/auto` 的实际状态变化还会生成成功的灌溉开关记录，远程控制广播则由原命令 ACK 结算，避免重复记录。

## 6. 信息流 D：心跳快照

- Topic：`sensor/heartbeat`
- 频率：模拟器每 30 秒一次；连接恢复后也立即发送。

```json
{
  "seq": 301,
  "ts": 1787625480000,
  "type": "snapshot",
  "sensors": [
    {
      "deviceId": "3b8dcefd-3a51-4adc-b452-47c184c0951d",
      "switch": "on",
      "name": "P001-TEMP",
      "values": {"temperature": 24.13}
    },
    {
      "deviceId": "435106ba-01e7-4745-9646-3907d15b28df",
      "switch": "off",
      "name": "P001-IRRIG",
      "values": {}
    }
  ]
}
```

| 字段 | 必填 | 说明 |
|---|---:|---|
| `seq`、`ts`、`type` | 是 | 快照标识；`type` 固定为 `snapshot` |
| `sensors` | 是 | 设备状态数组 |
| `sensors[].deviceId` | 是 | UUID，用于逐项匹配 `device.device_uuid` |
| `sensors[].switch`、`name`、`values` | 是 | 展示/诊断信息 |

数据库映射：每个已登记 UUID 更新 `device.status = 'online'`、`device.last_heartbeat = ts`。快照中的 `values` 不写入 `plot_report`，避免与正式 data topic 重复计量。

## 7. 信息流 E：灌溉控制下发

仅 `device_type = 'irrigation'` 的设备由当前业务系统创建 `irrigation_record`。发送前后端必须先插入一条记录：`status = 'pending'`、`action_type = switch`、`requested_at = ts`，并将 `command_id` 写为本次 `seq` 的十进制字符串。

- Topic：`sensor/cmd`

```json
{
  "seq": 10001,
  "ts": 1787625500000,
  "deviceId": "435106ba-01e7-4745-9646-3907d15b28df",
  "switch": "on"
}
```

| 字段 | 必填 | 说明 | 数据库映射 |
|---|---:|---|---|
| `seq` | 是 | 全局递增、未确认前不可复用 | `irrigation_record.command_id = "10001"` |
| `ts` | 是 | 指令生成时间，毫秒 UTC | `irrigation_record.requested_at` |
| `deviceId` | 是 | 灌溉设备 UUID | 取得 `irrigation_record.device_id`、`plot_id` |
| `switch` | 是 | `on` / `off` | `irrigation_record.action_type` |

模拟器仅在 ACK 中回传 `cmdSeq`，不回传自定义 `commandId`。因此，在不新增 `mqtt_seq` 字段的前提下，当前表的 `command_id` 约定为字符串化的 `seq`，这是 ACK 与灌溉记录能可靠关联的必要条件。

模拟器也可控制温湿度传感器的 `switch`（用于演示离线告警），但当前数据库只有 `irrigation_record`，不会为传感器控制创建控制记录。若要正式审计传感器的启停操作，应新增通用 `device_command` 表，而非复用 `irrigation_record`。

## 8. 信息流 F：控制 ACK

- Topic：`sensor/ack`

```json
{
  "seq": 10002,
  "cmdSeq": 10001,
  "action": "control",
  "deviceId": "435106ba-01e7-4745-9646-3907d15b28df",
  "result": "ok",
  "switch": "on",
  "name": "P001-IRRIG"
}
```

| 字段 | 必填 | 说明 | 数据库映射 |
|---|---:|---|---|
| `seq` | 是 | ACK 自身序列号 | 诊断/日志 |
| `cmdSeq` | 是 | 被确认控制指令的 `seq` | 查找 `irrigation_record.command_id = "cmdSeq"` |
| `action` | 是 | 控制 ACK 固定为 `control` | 校验消息用途 |
| `deviceId` | 是 | 执行设备 UUID | 校验对应 `device_id` |
| `result` | 是 | `ok` / `failed` | 写 `status = success` / `failed` |
| `switch` | 是 | 实际开关结果 | 与原指令核对 |
| `name` | 否 | 模拟器设备显示名 | 仅日志，不作为身份依据 |

MQTT Broker 接受发布只表示指令已经送出，`irrigation_record` 保持 `pending`。后端收到匹配的 `sensor/ack` 后，才根据 `result` 更新为 `success` 或 `failed`；超过 `COMMAND_ACK_TIMEOUT_SECONDS` 未收到 ACK 则更新为 `timeout`。前端展示的“开启命令成功”或“关闭命令成功”对应设备 ACK 成功，不表示整次灌溉任务已经结束。

## 9. 信息流 G：查询与查询响应

查询不改变灌溉记录，因此不写 `irrigation_record`。

查询单个设备，发布到 `sensor/cmd`：

```json
{"seq":10003,"ts":1787625600000,"action":"query","deviceId":"3b8dcefd-3a51-4adc-b452-47c184c0951d"}
```

查询全部设备，发布到 `sensor/cmd`：

```json
{"seq":10004,"ts":1787625600000,"action":"queryAll"}
```

单设备响应（`sensor/ack`）：

```json
{"seq":10005,"cmdSeq":10003,"action":"query","deviceId":"3b8dcefd-3a51-4adc-b452-47c184c0951d","switch":"on","name":"P001-TEMP"}
```

全量响应（`sensor/ack`）：

```json
{"seq":10006,"cmdSeq":10004,"action":"queryAll","sensors":[{"deviceId":"3b8dcefd-3a51-4adc-b452-47c184c0951d","switch":"on","name":"P001-TEMP"}]}
```

查询结果可以更新内存中的实时展示；如需将 `switch` 的查询结果持久化，仍需新增设备状态字段或状态历史表。

## 10. 配置清单（6 台设备）

| device_code | device_type | device_uuid |
|---|---|---|
| `P001-TEMP` | `temperature` | `3b8dcefd-3a51-4adc-b452-47c184c0951d` |
| `P001-MOIST` | `humidity` | `814621f7-2561-49ad-9766-72d3fcd18d86` |
| `P001-IRRIG` | `irrigation` | `435106ba-01e7-4745-9646-3907d15b28df` |
| `P002-TEMP` | `temperature` | `5b0a7464-a7db-449b-ae30-26063977c708` |
| `P002-MOIST` | `humidity` | `f2ac7d43-6c0d-4fb3-9b1a-5404bc51299a` |
| `P002-IRRIG` | `irrigation` | `b4d49779-b744-4096-898a-433b2d231839` |

在 6 个模拟器中，温度和湿度设备的业务 Topic 都填 `sensor/${deviceId}/data`；控制 Topic 都填 `sensor/cmd`。温度、湿度分别使用第 3、4 节的模板；灌溉马达业务 Payload 留空。
