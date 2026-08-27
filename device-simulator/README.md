# 模拟设备（device-simulator）

鸿蒙传感器模拟器（JavaFX 桌面程序）的交付物：模拟**温度传感器、湿度传感器、灌溉控制器**，通过 MQTT 上报数据、接收控制指令。**不需要真实硬件**。

## 目录结构

| 文件 | 说明 |
| --- | --- |
| `鸿蒙模拟器/javafx-demo-1.0-SNAPSHOT.jar` | 模拟器程序，`java -jar` 运行（需 JDK 20） |
| `鸿蒙模拟器/使用文档.md` | 模拟器完整使用文档（界面、操作、MQTT 协议、测试命令） |
| `设备填写表与MQTT对接.md` | **6 台设备 名称↔UUID 对照表 + 后端订阅 topic + MQTT 消息格式** |
| `基本功能-数据库表.docx` | 数据库权威表结构（对接字段以此为准） |

> 不入库的文件：`sensors.dat`（模拟器本地设备配置，每台机器运行时会重新生成，UUID 已在对接文档登记）、JDK 安装包（约 167MB，按 `使用文档.md` 自行安装 JDK 20）。

## 对接要点（以 `设备填写表与MQTT对接.md` 为准）

| 项 | 值 |
| --- | --- |
| 数据上报 | `sensor/{设备UUID}/data` |
| 控制指令 | `sensor/cmd`（body 带 `deviceId`=UUID + `switch`） |
| 控制回执 | `sensor/ack` |
| 状态广播 | `sensor/state`（Retained） |
| 心跳快照 | `sensor/heartbeat`（每 30 秒） |
| 后端订阅 | `sensor/+/data`、`sensor/ack`、`sensor/state`、`sensor/heartbeat` |
| MQTT Broker | EMQX `8.137.105.88:1883`（匿名连接，管理台 `http://8.137.105.88:18083` admin/public） |

> ⚠️ 注意：`../contracts/mqtt-topics.md` 是早期冻结的 `farm/telemetry/...` 主题规范，与模拟器实际使用的 `sensor/...` 协议**不一致**，已由模拟器协议取代。对接请以本目录文档为准。
