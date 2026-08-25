# 智慧农业前端 API 接口使用说明

> 本文档以 `frontend/openapi.yaml` 为唯一契约依据，说明不同用户界面需要调用的接口、前端如何发起请求，以及后端应返回的 JSON 数据。

## 1. 通用约定

### 1.1 请求地址

- 统一前缀：`/api`
- 本地示例：`http://localhost:8080/api`
- 前端可通过 `VITE_API_BASE_URL` 修改后端地址。
- 除注册接口外，请求默认需要 JWT。

```http
Authorization: Bearer <token>
Content-Type: application/json
```

前端的请求拦截器会自动从 `localStorage` 读取 `smart-agriculture-token` 并放入 `Authorization` 请求头，因此页面不需要自己拼接 Token。

### 1.2 前端实际拿到的数据

Axios 响应拦截器已经返回 `response.data`，所以 API 函数返回值就是后端 JSON，不需要再读取 `response.data.data`。

```js
const farms = await getFarmList()
// farms 直接是后端返回的数组
```

### 1.3 时间格式

所有时间都使用带时区的 ISO 8601：

```text
2026-08-25T10:30:00+08:00
```

### 1.4 通用错误响应

```json
{
  "code": "DEVICE_OFFLINE",
  "message": "设备当前离线，无法执行操作",
  "details": {
    "deviceId": "D003"
  }
}
```

| HTTP 状态码 | 含义 | 前端处理 |
| --- | --- | --- |
| 400 | 请求参数不正确 | 显示 `message` |
| 401 | Token 失效或未登录 | 清除登录信息并跳转登录页 |
| 403 | 当前用户无权访问 | 显示无权限提示 |
| 404 | 农场、地块、设备或用户不存在 | 显示 `message` |
| 409 | 重复提交或状态冲突 | 显示 `message` |
| 503 | 第三方服务不可用 | 使用降级界面 |

---

## 2. 登录和注册界面

### 2.1 用户登录

**页面：** 登录页  
**接口：** `POST /api/auth/login`

前端调用：

```js
const result = await login({
  username: 'zhangsan',
  password: '123456'
})
```

请求体：

```json
{
  "username": "zhangsan",
  "password": "123456"
}
```

后端响应：

```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9.example",
  "user": {
    "id": "U001",
    "username": "zhangsan",
    "role": "farmer"
  }
}
```

前端用途：

- 保存 `token`，后续请求自动携带。
- 根据 `role` 跳转到农户、农场管理员或系统管理员界面。
- 角色值只能是 `farmer`、`farm_admin` 或 `system_admin`。

### 2.2 加载注册时可申请的农场

**页面：** 注册页  
**接口：** `GET /api/farms`

前端调用：

```js
const farms = await getFarmList()
```

后端响应：

```json
[
  {
    "id": "F001",
    "name": "一号示范农场"
  },
  {
    "id": "F002",
    "name": "智慧农业实验基地"
  }
]
```

> **契约问题：** 注册页还没有 Token，但 YAML 把 `/farms` 定义为需要 Bearer Token。后端应开放一个只返回可申请资源的公开接口，或明确允许注册页匿名访问这个接口。

### 2.3 加载注册时可申请的地块

**页面：** 注册页  
**接口：** `GET /api/farms/{farmId}/overview`

前端会对每个农场查询一次：

```js
const overview = await getFarmOverview('F001')
```

后端响应：

```json
[
  {
    "plot": {
      "id": "P001",
      "farmId": "F001",
      "name": "一号温室"
    },
    "latestMetrics": [
      {
        "type": "temperature",
        "value": 25.6,
        "unit": "C",
        "ts": "2026-08-25T10:25:18+08:00"
      },
      {
        "type": "humidity",
        "value": 28.5,
        "unit": "%",
        "ts": "2026-08-25T10:25:18+08:00"
      }
    ],
    "devices": []
  }
]
```

注册页只使用 `plot.id`、`plot.farmId` 和 `plot.name`，不使用实时指标和设备数据。

### 2.4 提交注册申请

**页面：** 注册页  
**接口：** `POST /api/auth/register`  
**认证：** 不需要 Token

前端调用的数据需转换为 YAML 规定的下划线字段：

```js
await register({
  username: 'zhangsan',
  password: '123456',
  real_name: '张三',
  email: 'zhangsan@example.com',
  phone: '13800138000',
  role_codes: ['farmer'],
  plot_ids: ['P001'],
  farm_ids: []
})
```

请求体：

```json
{
  "username": "zhangsan",
  "password": "123456",
  "real_name": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "role_codes": ["farmer"],
  "plot_ids": ["P001"],
  "farm_ids": []
}
```

后端响应：

```json
{
  "id": "REG001",
  "username": "zhangsan",
  "realName": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "roles": ["farmer"],
  "plotIds": ["P001"],
  "farmIds": [],
  "status": "待审核",
  "createdAt": "2026-08-25T10:30:00+08:00",
  "reviewedAt": null,
  "rejectReason": null
}
```

---

## 3. 农户界面

### 3.1 农户页面首次进入时的请求链

进入任意农户页面时，`FarmerLayout` 会触发一次基础数据加载：

```text
GET /farms
  → 对每个农场 GET /farms/{farmId}/overview
  → GET /alert-rules
  → GET /alerts
  → 对每个地块 GET /plots/{plotId}/irrigation-settings
  → 对每个地块 GET /irrigation/records?plotId={plotId}
  → GET /weather/forecast?plotId={selectedPlotId}
```

这些数据被农户首页、地块管理、智慧灌溉、告警中心和 AI 助手共享，不是每切换一个页面都重新请求。

### 3.2 查询农户可访问农场

**涉及页面：** 农户首页、地块管理、智慧灌溉、告警中心、AI 助手  
**接口：** `GET /api/farms`

前端调用：

```js
const farms = await getFarmList()
```

后端只能返回当前 Token 有权访问的农场：

```json
[
  {
    "id": "F001",
    "name": "一号示范农场"
  }
]
```

### 3.3 查询地块实时概况

**涉及页面：** 农户首页、地块管理、智慧灌溉  
**接口：** `GET /api/farms/{farmId}/overview`

前端调用：

```js
const rows = await getFarmOverview('F001')
```

后端响应：

```json
[
  {
    "plot": {
      "id": "P001",
      "farmId": "F001",
      "name": "一号温室"
    },
    "latestMetrics": [
      {
        "type": "temperature",
        "value": 25.6,
        "unit": "C",
        "ts": "2026-08-25T10:25:18+08:00"
      },
      {
        "type": "humidity",
        "value": 28.5,
        "unit": "%",
        "ts": "2026-08-25T10:25:20+08:00"
      }
    ],
    "devices": [
      {
        "id": "D001",
        "deviceNo": "TEMP-001",
        "mqttDeviceId": "temperature_001",
        "type": "temperature",
        "plotId": "P001",
        "status": "online",
        "lastSeenAt": "2026-08-25T10:25:25+08:00"
      },
      {
        "id": "D002",
        "deviceNo": "HUM-001",
        "mqttDeviceId": "humidity_001",
        "type": "humidity",
        "plotId": "P001",
        "status": "online",
        "lastSeenAt": "2026-08-25T10:25:20+08:00"
      },
      {
        "id": "D003",
        "deviceNo": "VALVE-001",
        "mqttDeviceId": "irrigation_001",
        "type": "irrigation",
        "plotId": "P001",
        "status": "online",
        "lastSeenAt": "2026-08-25T10:25:22+08:00"
      }
    ]
  }
]
```

页面字段映射：

| 后端字段 | 前端用途 |
| --- | --- |
| `plot.id` | 地块编号和后续请求的 `plotId` |
| `latestMetrics[type=temperature].value` | 环境温度 |
| `latestMetrics[type=humidity].value` | 土壤湿度 |
| `latestMetrics[].ts` | 数据更新时间、数据延迟判断 |
| `devices[].type` | 区分温度、湿度和灌溉设备 |
| `devices[].status` | 显示在线或离线 |
| `devices[].lastSeenAt` | 显示最后心跳 |

### 3.4 查询单台设备状态

**接口：** `GET /api/devices/{deviceId}/status`  
**当前状态：** YAML 已定义，前端 API 已封装，但当前页面主要使用农场概况中的 `devices[].status`，尚未单独调用该接口。

前端可这样调用：

```js
const status = await getDeviceStatus('D003')
```

后端响应：

```json
{
  "deviceId": "D003",
  "status": "online",
  "lastSeenAt": "2026-08-25T10:25:22+08:00"
}
```

### 3.5 查询告警规则

**涉及页面：** 地块管理  
**接口：** `GET /api/alert-rules`

前端调用：

```js
const rules = await getAlertRules()
```

后端响应：

```json
[
  {
    "id": "RULE001",
    "plotId": "P001",
    "metricType": "humidity",
    "operator": "<",
    "threshold": 35,
    "enabled": true
  }
]
```

前端会找到当前地块 `metricType=humidity` 且 `enabled=true` 的规则，将 `threshold` 显示为土壤湿度阈值。

### 3.6 保存湿度告警阈值

**页面：** 地块管理  
**接口：** `POST /api/alert-rules`

前端调用：

```js
const savedRule = await saveAlertRule({
  plotId: 'P001',
  metricType: 'humidity',
  operator: '<',
  threshold: 35,
  enabled: true
})
```

请求体：

```json
{
  "plotId": "P001",
  "metricType": "humidity",
  "operator": "<",
  "threshold": 35,
  "enabled": true
}
```

后端响应：

```json
{
  "id": "RULE001",
  "plotId": "P001",
  "metricType": "humidity",
  "operator": "<",
  "threshold": 35,
  "enabled": true
}
```

`POST /alert-rules` 在这份契约中表示“创建或更新”，后端应以 `plotId + metricType` 查找已有规则，避免每次保存都新增重复规则。

### 3.7 查询灌溉参数

**页面：** 地块管理  
**接口：** `GET /api/plots/{plotId}/irrigation-settings`

前端调用：

```js
const settings = await getIrrigationSettings('P001')
```

后端响应：

```json
{
  "plotId": "P001",
  "irrigationDuration": 60,
  "irrigationInterval": 60,
  "updatedAt": "2026-08-25T09:00:00+08:00"
}
```

- `irrigationDuration`：单次灌溉时长，单位分钟。
- `irrigationInterval`：自动灌溉最小间隔，单位分钟。
- 湿度阈值不属于这个接口，由 `/alert-rules` 管理。

### 3.8 保存灌溉参数

**页面：** 地块管理  
**接口：** `PUT /api/plots/{plotId}/irrigation-settings`

前端调用：

```js
const settings = await updateIrrigationSettings('P001', {
  irrigationDuration: 60,
  irrigationInterval: 60
})
```

请求体：

```json
{
  "irrigationDuration": 60,
  "irrigationInterval": 60
}
```

后端响应：

```json
{
  "plotId": "P001",
  "irrigationDuration": 60,
  "irrigationInterval": 60,
  "updatedAt": "2026-08-25T10:40:00+08:00"
}
```

### 3.9 查询历史温湿度曲线

**页面：** 地块管理的曲线图  
**接口：** `GET /api/plots/{plotId}/metrics`

前端会分别请求温度和湿度：

```js
const params = {
  from: '2026-08-24T10:30:00+08:00',
  to: '2026-08-25T10:30:00+08:00'
}

const [temperature, humidity] = await Promise.all([
  getPlotMetrics('P001', { ...params, type: 'temperature' }),
  getPlotMetrics('P001', { ...params, type: 'humidity' })
])
```

实际请求 URL：

```http
GET /api/plots/P001/metrics?type=temperature&from=2026-08-24T10%3A30%3A00%2B08%3A00&to=2026-08-25T10%3A30%3A00%2B08%3A00
GET /api/plots/P001/metrics?type=humidity&from=2026-08-24T10%3A30%3A00%2B08%3A00&to=2026-08-25T10%3A30%3A00%2B08%3A00
```

温度响应：

```json
[
  {
    "type": "temperature",
    "value": 23.4,
    "unit": "C",
    "ts": "2026-08-25T04:00:00+08:00"
  },
  {
    "type": "temperature",
    "value": 25.6,
    "unit": "C",
    "ts": "2026-08-25T12:00:00+08:00"
  }
]
```

湿度响应：

```json
[
  {
    "type": "humidity",
    "value": 38.2,
    "unit": "%",
    "ts": "2026-08-25T04:00:00+08:00"
  },
  {
    "type": "humidity",
    "value": 31.5,
    "unit": "%",
    "ts": "2026-08-25T12:00:00+08:00"
  }
]
```

前端按 `ts` 合并两个数组，用 `value` 绘制温度和湿度曲线。

### 3.10 查询灌溉记录

**涉及页面：** 智慧灌溉、地块管理历史标记  
**接口：** `GET /api/irrigation/records?plotId={plotId}`

前端调用：

```js
const records = await getIrrigationRecords('P001')
```

后端响应：

```json
[
  {
    "recordId": "IRR001",
    "plotId": "P001",
    "plotName": "一号温室",
    "deviceId": "D003",
    "operatorId": "U001",
    "operator": "张三",
    "operationType": "开启",
    "activationType": "手动",
    "startTime": "2026-08-25T08:00:00+08:00",
    "endTime": "2026-08-25T08:20:00+08:00",
    "duration": 20,
    "status": "成功",
    "source": "Web 农户端"
  }
]
```

### 3.11 下发灌溉开关指令

**页面：** 智慧灌溉  
**接口：** `POST /api/devices/{deviceId}/commands`

开启灌溉：

```js
const command = await createDeviceCommand('D003', 'irrigation_on')
```

请求体：

```json
{
  "action": "irrigation_on"
}
```

关闭灌溉时将 `action` 改为 `irrigation_off`。

后端接受指令后应立即返回 HTTP `202`：

```json
{
  "commandId": "CMD0001",
  "deviceId": "D003",
  "action": "irrigation_on",
  "status": "pending",
  "createdAt": "2026-08-25T10:45:00+08:00",
  "finishedAt": null
}
```

### 3.12 轮询灌溉指令结果

**页面：** 智慧灌溉  
**接口：** `GET /api/commands/{commandId}`

当创建指令返回 `pending` 时，前端每 1 秒查询一次，最多 10 次：

```js
const result = await getCommandStatus('CMD0001')
```

执行成功响应：

```json
{
  "commandId": "CMD0001",
  "deviceId": "D003",
  "action": "irrigation_on",
  "status": "success",
  "createdAt": "2026-08-25T10:45:00+08:00",
  "finishedAt": "2026-08-25T10:45:02+08:00"
}
```

`status` 可为 `pending`、`success`、`failed` 或 `timeout`。

### 3.13 查询告警列表

**涉及页面：** 农户首页、告警中心  
**接口：** `GET /api/alerts`

前端调用：

```js
const alerts = await getAlertList()
```

后端应根据 Token 只返回当前用户有权地块的告警：

```json
[
  {
    "id": "ALT001",
    "plotId": "P001",
    "metricType": "humidity",
    "value": 28.5,
    "threshold": 35,
    "status": "active",
    "triggeredAt": "2026-08-25T10:25:20+08:00"
  }
]
```

前端显示映射：

| 后端值 | 前端显示 |
| --- | --- |
| `metricType: humidity` | 湿度过低 |
| `metricType: temperature` | 温度异常 |
| `status: active` | 未处理 |
| `status: acknowledged` | 处理中 |
| `status: recovered` | 已处理 |

### 3.14 确认告警

**页面：** 告警中心  
**接口：** `POST /api/alerts/{alertId}/ack`

前端调用：

```js
const alert = await acknowledgeAlert('ALT001')
```

该请求没有请求体。后端响应：

```json
{
  "id": "ALT001",
  "plotId": "P001",
  "metricType": "humidity",
  "value": 28.5,
  "threshold": 35,
  "status": "acknowledged",
  "triggeredAt": "2026-08-25T10:25:20+08:00"
}
```

### 3.15 查询天气

**涉及页面：** 农户首页、AI 助手的分析上下文  
**接口：** `GET /api/weather/forecast?plotId={plotId}`

前端调用：

```js
const weather = await getWeatherForecast({ plotId: 'P001' })
```

后端响应：

```json
{
  "current": {
    "city": "北京",
    "condition": "多云",
    "temperature": 27.2,
    "feelsLike": 28.1,
    "high": 30,
    "low": 21,
    "rainProbability": 20,
    "humidity": 61,
    "wind": "东南风 2 级",
    "updatedAt": "2026-08-25T10:20:00+08:00"
  },
  "hourly": [
    {
      "time": "2026-08-25T11:00:00+08:00",
      "condition": "多云",
      "temperature": 28,
      "rainProbability": 20
    }
  ],
  "daily": [
    {
      "date": "2026-08-25",
      "condition": "多云",
      "high": 30,
      "low": 21,
      "rainProbability": 20
    }
  ]
}
```

### 3.16 向 AI 农业助手提问

**页面：** AI 农业助手  
**接口：** `POST /api/chat/sessions/{sessionId}/messages`

前端调用：

```js
const reply = await sendChatMessage('WEB20260825103000', {
  message: '现在需要灌溉吗？',
  plotId: 'P001'
})
```

请求体：

```json
{
  "message": "现在需要灌溉吗？",
  "plotId": "P001"
}
```

后端响应：

```json
{
  "sessionId": "WEB20260825103000",
  "answer": "当前土壤湿度为 28.5%，低于 35% 阈值，建议进行短时灌溉。",
  "sources": [
    "P001 最新湿度 28.5%",
    "P001 湿度阈值 35%",
    "未来 24 小时降雨概率 20%"
  ]
}
```

`answer` 显示为 AI 回答，`sources` 显示在“建议依据”区域。后端必须根据 Token 校验用户是否有权访问 `plotId`。

---

## 4. 农场管理员界面

### 4.1 农场管理员页面首次进入时的请求链

```text
GET /farms
  → 对每个农场 GET /farms/{farmId}/overview
  → GET /devices
  → GET /alerts
```

当前公用 `platformStore` 还会并行请求 `GET /users`，但农场管理员页面目前不使用用户列表；若后端返回 403，前端会忽略该请求失败。后续可将这个无用请求从农场管理员加载流程中拆除。

### 4.2 多地块总览和设备状态

**页面：** 多地块总览、设备状态  
**接口：**

- `GET /api/farms`
- `GET /api/farms/{farmId}/overview`

请求和响应格式与本文档 **3.2** 和 **3.3** 相同。后端应只返回该管理员有权管理的农场、地块和关联设备。

设备状态页的温度、湿度、灌溉设备“在线/离线”均来自 `overview[].devices[].status`。

### 4.3 查询全部设备

**页面：** 设备管理  
**接口：** `GET /api/devices`  
**可选筛选：** `GET /api/devices?plotId=P001`

前端调用：

```js
const devices = await getAllDevices()

// 如需只查一个地块
const plotDevices = await getAllDevices({ plotId: 'P001' })
```

后端响应：

```json
[
  {
    "id": "D001",
    "deviceNo": "TEMP-001",
    "mqttDeviceId": "temperature_001",
    "type": "temperature",
    "plotId": "P001",
    "status": "online",
    "lastSeenAt": "2026-08-25T10:25:25+08:00"
  },
  {
    "id": "D003",
    "deviceNo": "VALVE-001",
    "mqttDeviceId": "irrigation_001",
    "type": "irrigation",
    "plotId": "P001",
    "status": "offline",
    "lastSeenAt": "2026-08-25T09:50:00+08:00"
  }
]
```

### 4.4 录入设备

**页面：** 设备管理  
**接口：** `POST /api/devices`

前端调用：

```js
const device = await createDevice({
  deviceNo: 'HUM-002',
  mqttDeviceId: 'humidity_002',
  type: 'humidity',
  plotId: 'P002'
})
```

请求体：

```json
{
  "deviceNo": "HUM-002",
  "mqttDeviceId": "humidity_002",
  "type": "humidity",
  "plotId": "P002"
}
```

`type` 只能是 `temperature`、`humidity` 或 `irrigation`。后端响应 HTTP `201`：

```json
{
  "id": "D004",
  "deviceNo": "HUM-002",
  "mqttDeviceId": "humidity_002",
  "type": "humidity",
  "plotId": "P002",
  "status": "offline",
  "lastSeenAt": null
}
```

### 4.5 绑定或换绑设备

**页面：** 设备管理  
**接口：** `POST /api/devices/{deviceId}/bind`

前端调用：

```js
const device = await bindDevice('D004', 'P001')
```

请求体：

```json
{
  "plotId": "P001"
}
```

后端响应：

```json
{
  "id": "D004",
  "deviceNo": "HUM-002",
  "mqttDeviceId": "humidity_002",
  "type": "humidity",
  "plotId": "P001",
  "status": "offline",
  "lastSeenAt": null
}
```

### 4.6 解除设备绑定

**页面：** 设备管理  
**接口：** `DELETE /api/devices/{deviceId}/bind`

前端调用：

```js
await unbindDevice('D004')
```

成功时后端返回 HTTP `204 No Content`，不要返回 JSON 正文。前端在请求成功后将本地设备的 `plotId` 清空。

### 4.7 设备状态页的灌溉记录

**页面：** 设备状态  
**接口：** `GET /api/irrigation/records?plotId={plotId}`

农场管理员界面会对有权地块分别查询，格式与本文档 **3.10** 相同。

### 4.8 查询农场告警

**页面：** 多地块总览、告警日志  
**接口：** `GET /api/alerts`

格式与本文档 **3.13** 相同。后端应只返回该管理员授权农场下的告警。

> 当前农场管理员的告警日志页主要用于查询和筛选，尚未在页面中调用告警确认接口。

---

## 5. 系统管理员界面

### 5.1 运行概况首次加载

系统管理员公用数据加载会发起：

```text
GET /farms
  → 对每个农场 GET /farms/{farmId}/overview
  → GET /devices
  → GET /users
  → GET /alerts
```

返回数据用于计算农场数、地块数、在线设备数、离线设备数、用户数和未处理告警数。

### 5.2 查询注册申请

**页面：** 系统管理员运行概况/用户管理审核区  
**接口：** `GET /api/registration-applications`  
**可选参数：** `status=待审核|已通过|已拒绝`

前端调用：

```js
const applications = await getRegistrationApplications({ status: '待审核' })
```

后端响应：

```json
[
  {
    "id": "REG001",
    "username": "zhangsan",
    "realName": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "roles": ["farmer"],
    "plotIds": ["P001"],
    "farmIds": [],
    "status": "待审核",
    "createdAt": "2026-08-25T10:30:00+08:00",
    "reviewedAt": null,
    "rejectReason": null
  }
]
```

### 5.3 通过注册申请

**接口：** `PUT /api/registration-applications/{applicationId}/approve`

前端调用：

```js
const application = await approveRegistration('REG001')
```

该请求没有请求体。后端响应：

```json
{
  "id": "REG001",
  "username": "zhangsan",
  "realName": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "roles": ["farmer"],
  "plotIds": ["P001"],
  "farmIds": [],
  "status": "已通过",
  "createdAt": "2026-08-25T10:30:00+08:00",
  "reviewedAt": "2026-08-25T11:00:00+08:00",
  "rejectReason": null
}
```

后端需要在同一事务中创建用户、写入角色和农场/地块授权，再将申请状态改为“已通过”。

### 5.4 驳回注册申请

**接口：** `PUT /api/registration-applications/{applicationId}/reject`

前端调用：

```js
const application = await rejectRegistration('REG001', {
  reason: '申请的地块信息需要重新确认'
})
```

请求体：

```json
{
  "reason": "申请的地块信息需要重新确认"
}
```

后端响应：

```json
{
  "id": "REG001",
  "username": "zhangsan",
  "realName": "张三",
  "email": "zhangsan@example.com",
  "phone": "13800138000",
  "roles": ["farmer"],
  "plotIds": ["P001"],
  "farmIds": [],
  "status": "已拒绝",
  "createdAt": "2026-08-25T10:30:00+08:00",
  "reviewedAt": "2026-08-25T11:00:00+08:00",
  "rejectReason": "申请的地块信息需要重新确认"
}
```

### 5.5 查询用户

**页面：** 用户管理  
**接口：** `GET /api/users`  
**可选参数：** `keyword`

前端调用：

```js
const users = await getUserList({ keyword: '张三' })
```

后端响应：

```json
[
  {
    "id": "U001",
    "username": "zhangsan",
    "name": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "roles": ["farmer"],
    "farmIds": [],
    "plotIds": ["P001"],
    "active": true,
    "lastLogin": "2026-08-25T09:10:00+08:00"
  }
]
```

### 5.6 创建用户

**页面：** 用户管理  
**接口：** `POST /api/users`

前端调用：

```js
const user = await saveUser(null, {
  username: 'lisi',
  name: '李四',
  email: 'lisi@example.com',
  phone: '13900139000',
  active: true,
  role_codes: ['farm_admin'],
  farm_ids: ['F001'],
  plot_ids: []
})
```

请求体：

```json
{
  "username": "lisi",
  "name": "李四",
  "email": "lisi@example.com",
  "phone": "13900139000",
  "active": true,
  "role_codes": ["farm_admin"],
  "farm_ids": ["F001"],
  "plot_ids": []
}
```

后端响应 HTTP `201`：

```json
{
  "id": "U002",
  "username": "lisi",
  "name": "李四",
  "email": "lisi@example.com",
  "phone": "13900139000",
  "roles": ["farm_admin"],
  "farmIds": ["F001"],
  "plotIds": [],
  "active": true,
  "lastLogin": null
}
```

### 5.7 更新用户和授权范围

**页面：** 用户管理  
**接口：** `PUT /api/users/{userId}`

前端调用：

```js
const user = await saveUser('U002', {
  username: 'lisi',
  name: '李四',
  email: 'lisi@example.com',
  phone: '13900139000',
  active: true,
  role_codes: ['farm_admin'],
  farm_ids: ['F001', 'F002'],
  plot_ids: []
})
```

请求体和创建用户一致，后端返回更新后的完整 `UserSummary`：

```json
{
  "id": "U002",
  "username": "lisi",
  "name": "李四",
  "email": "lisi@example.com",
  "phone": "13900139000",
  "roles": ["farm_admin"],
  "farmIds": ["F001", "F002"],
  "plotIds": [],
  "active": true,
  "lastLogin": "2026-08-24T15:20:00+08:00"
}
```

### 5.8 启用或禁用用户账号

**页面：** 用户管理  
**接口：** `PUT /api/users/{userId}/active`

前端调用：

```js
const user = await updateUserActive('U002', false)
```

请求体：

```json
{
  "active": false
}
```

后端响应：

```json
{
  "id": "U002",
  "username": "lisi",
  "name": "李四",
  "email": "lisi@example.com",
  "phone": "13900139000",
  "roles": ["farm_admin"],
  "farmIds": ["F001"],
  "plotIds": [],
  "active": false,
  "lastLogin": "2026-08-24T15:20:00+08:00"
}
```

### 5.9 重置用户密码

**页面：** 用户管理  
**接口：** `POST /api/users/{userId}/reset-password`

前端调用：

```js
const result = await resetUserPassword('U002')
```

该请求没有请求体。后端响应：

```json
{
  "message": "密码已重置",
  "temporaryPassword": "Tmp@823641"
}
```

如果后端通过短信或邮件发送临时密码，`temporaryPassword` 可以返回 `null`。

### 5.10 系统管理员的农场、设备和告警数据

运行概况和全局告警使用下列接口：

- `GET /api/farms`：格式见 **3.2**。
- `GET /api/farms/{farmId}/overview`：格式见 **3.3**。
- `GET /api/devices`：格式见 **4.3**。
- `GET /api/alerts`：格式见 **3.13**。

系统管理员 Token 可以获取全局数据，其他角色必须由后端按授权范围过滤。

### 5.11 系统参数和操作日志

**页面：** 系统参数、操作日志  
**当前状态：** `frontend/openapi.yaml` 尚未定义系统参数和审计日志接口，当前页面使用本地模拟数据，无法与真实后端联调。

---

## 6. 接口与页面快速对照表

| 用户界面 | 页面 | 接口 |
| --- | --- | --- |
| 公共 | 登录 | `POST /auth/login` |
| 公共 | 注册 | `GET /farms`、`GET /farms/{farmId}/overview`、`POST /auth/register` |
| 农户 | 公共基础数据 | `GET /farms`、`GET /farms/{farmId}/overview`、`GET /alerts`、`GET /alert-rules`、`GET /plots/{plotId}/irrigation-settings`、`GET /irrigation/records`、`GET /weather/forecast` |
| 农户 | 地块管理 | `GET /plots/{plotId}/metrics`、`POST /alert-rules`、`PUT /plots/{plotId}/irrigation-settings` |
| 农户 | 智慧灌溉 | `POST /devices/{deviceId}/commands`、`GET /commands/{commandId}`、`GET /irrigation/records` |
| 农户 | 告警中心 | `GET /alerts`、`POST /alerts/{alertId}/ack` |
| 农户 | AI 助手 | `POST /chat/sessions/{sessionId}/messages`、`GET /weather/forecast` |
| 农场管理员 | 多地块总览 | `GET /farms`、`GET /farms/{farmId}/overview`、`GET /alerts` |
| 农场管理员 | 设备状态 | `GET /farms/{farmId}/overview`、`GET /irrigation/records` |
| 农场管理员 | 设备管理 | `GET /devices`、`POST /devices`、`POST /devices/{deviceId}/bind`、`DELETE /devices/{deviceId}/bind` |
| 农场管理员 | 告警日志 | `GET /alerts` |
| 系统管理员 | 运行概况 | `GET /farms`、`GET /farms/{farmId}/overview`、`GET /devices`、`GET /users`、`GET /alerts` |
| 系统管理员 | 注册审核 | `GET /registration-applications`、`PUT /registration-applications/{id}/approve`、`PUT /registration-applications/{id}/reject` |
| 系统管理员 | 用户管理 | `GET /users`、`POST /users`、`PUT /users/{userId}`、`PUT /users/{userId}/active`、`POST /users/{userId}/reset-password` |
| 系统管理员 | 系统参数/操作日志 | YAML 尚未定义对应接口 |

---

## 7. 联调时必须确认的要点

1. 后端返回的 JSON 顶层应与 YAML 一致。列表接口直接返回数组，不要临时包装成 `{ "data": [...] }` 或 `{ "records": [...] }`。
2. `Farm`、`Plot`、`Device` 的主键在契约中都是 `id`，不要混用 `farmId`、`plotId`、`deviceId` 作为返回对象的主键字段。
3. 请求体中有两套命名风格：旧契约主要是驼峰命名，扩展的注册和用户保存请求使用 `role_codes`、`farm_ids`、`plot_ids`等下划线字段，后端不要自行改名。
4. 后端必须基于 Token 过滤农场、地块、设备、告警和灌溉记录，前端筛选不能代替后端权限校验。
5. 历史指标查询必须正确处理带时区的 `from` 和 `to`，并按 `ts` 升序返回。
6. 灌溉控制是异步链路：创建指令返回 `pending`，后端等待 MQTT ACK 后将指令更新为 `success`、`failed` 或 `timeout`。
7. 注册页所需的匿名农场/地块选项与当前鉴权定义冲突，这是联调前必须解决的契约问题。
8. 系统参数和操作日志暂无 API，如果要去除模拟数据，需先在 OpenAPI 中增加完整契约。
