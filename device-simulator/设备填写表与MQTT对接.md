# 设备填写表与 MQTT 对接

> ① 登记 6 台模拟器的名称与 UUID；② 后端订阅的 topic；③ 数据上报 / 控制指令的 MQTT 格式。

---

## 一、6 台设备 名称 ↔ UUID 对照表

| #   | 设备名称（=device_code） | 设备类型  | 模拟器 UUID（点卡片「复制」填入）                  |
| --- | ------------------ | ----- | ------------------------------------ |
| 1   | `P001-TEMP`        | 温度传感器 | 3b8dcefd-3a51-4adc-b452-47c184c0951d |
| 2   | `P001-MOIST`       | 湿度传感器 | 814621f7-2561-49ad-9766-72d3fcd18d86 |
| 3   | `P001-IRRIG`       | 灌溉马达  | 435106ba-01e7-4745-9646-3907d15b28df |
| 4   | `P002-TEMP`        | 温度传感器 | 5b0a7464-a7db-449b-ae30-26063977c708 |
| 5   | `P002-MOIST`       | 湿度传感器 | f2ac7d43-6c0d-4fb3-9b1a-5404bc51299a |
| 6   | `P002-IRRIG`       | 灌溉马达  | b4d49779-b744-4096-898a-433b2d231839 |

> 入库时，将「名称(device_code) + UUID」写进 device 表同一行，后端即可用 UUID ↔ device_code ↔ device_id 互查。

---

## 二、后端订阅 topic

| 订阅 topic           | 用途                              |
| ------------------ | ------------------------------- |
| `sensor/+/data`    | 收所有设备数据上报                       |
| `sensor/ack`       | 收控制回执                           |
| `sensor/state`     | 收状态广播（Retained，新订阅者上线立即可拿到最后状态） |
| `sensor/heartbeat` | 收心跳快照（每 30 秒一次，用于判断在线/离线）       |

---

## 三、数据上报 MQTT 格式（设备 → 后端）

- **Topic**：`sensor/{UUID}/data`（模拟器里 Topic 填 `sensor/${deviceId}/data`，`${deviceId}` 自动展开成 UUID）
- **Payload**：

| 设备  | Payload                                                                |
| --- | ---------------------------------------------------------------------- |
| 温度  | {"temperature":25,"deviceId":"${deviceId}","timestamp":${timestamp}}   |
| 湿度  | {"plot_moisture":40,"deviceId":"${deviceId}","timestamp":${timestamp}} |
| 马达  | 无                                                                      |

> 运行日志：
> 
> [10:34:27] 上报 P001-TEMP: {"temperature":24.13,"deviceId":"3b8dcefd-3a51-4adc-b452-47c184c0951d","timestamp":1787625267746}
> 
> [10:37:30] 状态广播 [sensor/state]: {"seq":2781,"ts":1787625450657,"deviceId":"814621f7-2561-49ad-9766-72d3fcd18d86","switch":"off","reason":"local","values":{"plot_moisture":43.12}}
> 
> [10:37:29] 上报 P001-MOIST: {"plot_moisture":43.12,"deviceId":"814621f7-2561-49ad-9766-72d3fcd18d86","timestamp":1787625449586}
> 
> [10:37:56] 状态广播 [sensor/state]: {"seq":2783,"ts":1787625476220,"deviceId":"435106ba-01e7-4745-9646-3907d15b28df","switch":"on","reason":"local","values":{}}
> 
> [10:37:56] 上报 P001-IRRIG: 
> 
> [10:37:57] 状态广播 [sensor/state]: {"seq":2784,"ts":1787625477378,"deviceId":"435106ba-01e7-4745-9646-3907d15b28df","switch":"off","reason":"local","values":{}}
> [10:38:07] 心跳快照 [sensor/heartbeat]: 9 个传感器
> 
> 

---

## 四、控制指令 MQTT 格式（后端 → 设备 → 回执）

### 1. 下发指令 —— 后端发到 `sensor/cmd`

```json
{"seq":1,"ts":1715059200000,"deviceId":"<马达UUID>","switch":"on"}
{"seq":2,"ts":1715059200000,"deviceId":"<马达UUID>","switch":"off"}
{"seq":3,"ts":1715059200000,"deviceId":"<温度UUID>","switch":"off"}   // 远程关传感器（演示离线告警）
```

| 字段         | 说明                                   |
| ---------- | ------------------------------------ |
| `seq`      | 全局递增序列号，用于幂等去重                       |
| `ts`       | 毫秒时间戳，防过期指令                          |
| `deviceId` | **必须是模拟器 UUID**（不能填 device_code）     |
| `switch`   | `on` 开 / `off` 关（对马达=灌溉开关，对传感器=上报启停） |

### 2. 控制回执 —— 设备自动回 `sensor/ack`

```json
{"seq":101,"cmdSeq":1,"action":"control","deviceId":"<UUID>","result":"ok","switch":"on","name":"P001-IRRIG"}
```

| 字段       | 说明                  |
| -------- | ------------------- |
| `result` | `ok` / `failed`     |
| `name`   | 该设备的名称（device_code） |

> 后端**不能假定下发即成功**：发完 `sensor/cmd` 后，等 `sensor/ack` 的 `result` 确认；等不到即超时。映射到 DB：`switch`→`action_type`(ON/OFF)；`result`→`status`(SUCCESS/FAILED/TIMEOUT)。

### 3. 状态广播 / 心跳（设备自动发，后端可订阅）

**`sensor/state`**（任何状态变更立即广播）：

```json
{"seq":201,"ts":1715059210000,"deviceId":"<UUID>","switch":"on","reason":"remote","values":{"temperature":25.30}}
```

**`sensor/heartbeat`**（每 30 秒全量快照）：

```json
{"seq":301,"ts":1715059500000,"type":"snapshot","sensors":[{"deviceId":"<UUID>","switch":"on","name":"P001-TEMP","values":{...}}]}
```

---

## 五、总结

> **模拟器**：名称=device_code、Topic=`sensor/${deviceId}/data`、控制Topic=`sensor/cmd`、温度湿度填最小 payload（含 `${deviceId}`）、马达留空。**后端**：订阅 `sensor/+/data` + `sensor/ack` + `sensor/state` + `sensor/heartbeat`，靠 UUID 查 device 表识别设备，控制走 `sensor/cmd` + UUID。
