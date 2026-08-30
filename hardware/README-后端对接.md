# README

> 

---

## 一、简介

** BearPi-HM Nano 板子 + E53_IA1 传感器已作为「P001 地块」的 3 台设备接入 EMQX（`8.137.105.88:1883`，匿名连接），实时上报温湿度，并支持远程控制灌溉马达。** 链路已实测通过。

## 二、板子扮演的角色（3 台设备）

| 设备名        | device_type | deviceId (UUID)                        | 行为              |
| ---------- | ----------- | -------------------------------------- | --------------- |
| P001-TEMP  | temperature | `3b8dcefd-3a51-4adc-b452-47c184c0951d` | 每 2 秒上报温度       |
| P001-MOIST | humidity    | `814621f7-2561-49ad-9766-72d3fcd18d86` | 每 2 秒上报湿度       |
| P001-IRRIG | irrigation  | `435106ba-01e7-4745-9646-3907d15b28df` | 订阅控制指令、开/关马达、回执 |

## 三、后端怎么订阅

| 主题              | 内容         | 用途                 |
| --------------- | ---------- | ------------------ |
| `sensor/+/data` | 温湿度遥测      | 数据落库（一条消息一个设备一个指标） |
| `sensor/ack`    | 控制回执       | 确认马达已执行            |
| `sensor/cmd`    | —（发布用，别订阅） | 后端下发控制指令           |

订阅建议：用通配 `sensor/+/data` 一条覆盖所有地块所有设备（板子 + 模拟器都走这个结构）。示例（paho）：

```python
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    print(msg.topic, "->", msg.payload.decode())

client = mqtt.Client(client_id="backend-sub")
client.on_message = on_message
client.connect("8.137.105.88", 1883, 60)
client.subscribe("sensor/+/data")   # 遥测
client.subscribe("sensor/ack")      # 回执
client.loop_forever()
```

## 四、数据格式（板子实际发的）

**温度**（发到 `sensor/3b8dcefd-.../data`，QoS1）：

```json
{"temperature": 27.31, "deviceId": "3b8dcefd-3a51-4adc-b452-47c184c0951d", "timestamp": 71710, "msgId": "71710"}
```

**湿度**（发到 `sensor/814621f7-.../data`，QoS1）：

```json
{"plot_moisture": 52.65, "deviceId": "814621f7-2561-49ad-9766-72d3fcd18d86", "timestamp": 71710, "msgId": "71710"}
```

要点：

- **一条消息只有一个指标**（temperature 或 plot_moisture），温度和湿度是两条独立消息，靠 `deviceId` 区分。
- QoS1、每 2 秒一对。
- `msgId` = 板子开机毫秒数，**同一份数据里温度/湿度 msgId 相同**，可用来配对 30 秒窗口。
- ⚠️ **`timestamp` 目前是"开机毫秒数"（从 0 累计），不是 13 位 Unix 时间戳**。若后端需要 Unix 时间或精确时序，请找 E 确认是否改 NTP 对时。

## 五、后端怎么发控制指令

### 1. 发布到 `sensor/cmd`

```json
{"seq": 10001, "ts": 1725000000000, "deviceId": "435106ba-01e7-4745-9646-3907d15b28df", "switch": "on"}
```

- `seq`：后端自增序号（回执会原样带回，用于匹配灌溉记录）
- `ts`：Unix 毫秒时间戳
- `deviceId`：**必须是灌溉设备的 UUID**（P001 就是 `435106ba-...`）
- `switch`：`"on"` / `"off"`

### 2. 等待 `sensor/ack` 回执

```json
{"seq": 1000, "cmdSeq": 10001, "action": "control", "deviceId": "435106ba-01e7-4745-9646-3907d15b28df", "result": "ok", "switch": "on", "name": "P001-IRRIG"}
```

- `cmdSeq` = 你发的 `seq`（匹配用）
- `result: "ok"` = 马达已执行；30 秒无回执 = 板子掉线或指令没到（看硬件文档排障）

### 3. 已实测

on（seq=10001）→ 回执 `cmdSeq:10001, result:ok, switch:on`，马达转动；off（seq=10002）→ 同样回执，马达停止。**链路可用。**

paho 发送示例：

```python
import json, time, paho.mqtt.client as mqtt

client = mqtt.Client(client_id="backend-ctrl")
client.connect("8.137.105.88", 1883, 60)
client.loop_start()

payload = json.dumps({
    "seq": 10001,
    "ts": int(time.time() * 1000),
    "deviceId": "435106ba-01e7-4745-9646-3907d15b28df",
    "switch": "on",
})
client.publish("sensor/cmd", payload, qos=1)
```

---

## 六、地块：P001 真机，其他地块全是模拟器

- **P001 地块 = 真实板子**（就是现在这块 BearPi，代表 P001 的三台设备：温度 / 湿度 / 灌溉）。
- **P002 及以后所有其他地块 = 软件模拟器**。由 `iot-farm-suite` 的 `simulator.py` / `mock_sensor.py` / `mock_pump.py` 上报，模拟器可以同时扮演多地块、多台设备。
- **为什么**：一块板子的固件写死一个地块的 UUID，物理上**只能当一个地块**；每个地块都要真机就得各配一块板子。所以分配方案是：**真机只做 P001 演示，其他地块统一用模拟器**。
- 后端**不需要区分真机还是模拟器**：所有地块都走同一个 MQTT 结构 `sensor/{device_uuid}/data`，按 `deviceId` 落库到对应地块即可。

## 七、常见问题

1. **收不到数据**：先确认板子串口有没有 `MQTT connected`（板子侧问题，见硬件复盘文档）；云上用 `mqtt_subscriber.py` 订阅 `sensor/+/data` 快速验证。
2. **控制没反应**：先确认 `deviceId` 是灌溉 UUID；再确认 `switch` 是字符串 `on/off`；再看板子串口有没有打印 `CMD: {...}`。
3. **重复数据**：QoS1 可能因网络重传造成消息重复，用 `msgId` + `deviceId` 去重。
4. **timestamp 非 Unix**：见第四节 ⚠️ 标注。

## 八、资源清单

- 云服务器：`8.137.105.88`（EMQX，Docker，`1883` 匿名；管理台 `:18083` admin/public，**管理台看不到消息内容**）
- 协议总规范：《真实硬件对接规格.md》（含 REST 设备登记说明）
