export const farmerPlots = [
  {
    plotId: 'P001', plotName: '一号温室', farmId: 'F001', farmName: '二号示范农场', location: '东区 1 号棚', cropName: '番茄', cropStage: '结果期',
    temperature: 25.6, humidity: 28.5, threshold: 35, cooldown: 30, maxDuration: 60, status: 'alert', irrigating: false,
    deviceOnline: true, dataState: 'realtime', updateTime: '2026-08-22 10:25:18', sensorId: 'SENSOR-001', valveId: 'VALVE-001', lastHeartbeat: '2026-08-22 10:25:20',
    devices: {
      temperature: { id: 'D001', deviceNo: 'SENSOR-001', mqttId: 'device_001', type: '温度传感器', msgId: 'M01842', topic: 'farm/telemetry/device_001' },
      humidity: { id: 'D002', deviceNo: 'SENSOR-002', mqttId: 'device_002', type: '湿度传感器', msgId: 'M01839', topic: 'farm/telemetry/device_002' },
      irrigation: { id: 'D003', deviceNo: 'SENSOR-003', mqttId: 'device_003', type: '灌溉设备', topic: 'farm/command/device_003' },
    },
    lastIrrigation: '2026-08-22 08:00:00', lastIrrigationDuration: 20, unhandledAlerts: 2,
  },
  {
    plotId: 'P002', plotName: '二号大棚', farmId: 'F001', farmName: '一号示范农场', location: '东区 2 号棚', cropName: '辣椒', cropStage: '开花期',
    temperature: 27.2, humidity: 42, threshold: 35, cooldown: 30, maxDuration: 45, status: 'irrigating', irrigating: true,
    deviceOnline: true, dataState: 'realtime', updateTime: '2026-08-22 10:24:46', sensorId: 'SENSOR-002', valveId: 'VALVE-002', lastHeartbeat: '2026-08-22 10:25:05',
    devices: {
      temperature: { id: 'D004', deviceNo: 'SENSOR-004', mqttId: 'device_004', type: '温度传感器', msgId: 'M01125', topic: 'farm/telemetry/device_004' },
      humidity: { id: 'D005', deviceNo: 'SENSOR-005', mqttId: 'device_005', type: '湿度传感器', msgId: 'M01124', topic: 'farm/telemetry/device_005' },
      irrigation: { id: 'D006', deviceNo: 'SENSOR-006', mqttId: 'device_006', type: '灌溉设备', topic: 'farm/command/device_006' },
    },
    lastIrrigation: '2026-08-22 09:00:00', lastIrrigationDuration: null, unhandledAlerts: 0,
  },
  {
    plotId: 'P003', plotName: '三号露地', farmId: 'F001', farmName: '一号示范农场', location: '西区露地', cropName: '空心菜', cropStage: '生长期',
    temperature: 30.1, humidity: 22, threshold: 30, cooldown: 30, maxDuration: 60, status: 'dry', irrigating: false,
    deviceOnline: true, dataState: 'delayed', updateTime: '2026-08-22 10:02:00', sensorId: 'SENSOR-003', valveId: 'VALVE-003', lastHeartbeat: '2026-08-22 10:20:00',
    devices: {
      temperature: { id: 'D007', deviceNo: 'SENSOR-007', mqttId: 'device_007', type: '温度传感器', msgId: 'M00680', topic: 'farm/telemetry/device_007' },
      humidity: { id: 'D008', deviceNo: 'SENSOR-008', mqttId: 'device_008', type: '湿度传感器', msgId: 'M00677', topic: 'farm/telemetry/device_008' },
      irrigation: { id: 'D009', deviceNo: 'SENSOR-009', mqttId: 'device_009', type: '灌溉设备', topic: 'farm/command/device_009' },
    },
    lastIrrigation: '2026-08-21 18:10:00', lastIrrigationDuration: 25, unhandledAlerts: 1,
  },
  {
    plotId: 'P004', plotName: '四号温室', farmId: 'F001', farmName: '一号示范农场', location: '南区 1 号棚', cropName: '黄瓜', cropStage: '爬蔓期',
    temperature: 26.8, humidity: 46, threshold: 34, cooldown: 30, maxDuration: 50, status: 'normal', irrigating: false,
    deviceOnline: true, dataState: 'realtime', updateTime: '2026-08-24 09:58:20', sensorId: 'SENSOR-010', valveId: 'VALVE-004', lastHeartbeat: '2026-08-24 09:58:22',
    devices: {
      temperature: { id: 'D010', deviceNo: 'SENSOR-010', mqttId: 'device_010', type: '温度传感器', msgId: 'M02001', topic: 'farm/telemetry/device_010' },
      humidity: { id: 'D011', deviceNo: 'SENSOR-011', mqttId: 'device_011', type: '湿度传感器', msgId: 'M02002', topic: 'farm/telemetry/device_011' },
      irrigation: { id: 'D012', deviceNo: 'VALVE-004', mqttId: 'device_012', type: '灌溉设备', topic: 'farm/command/device_012' },
    },
    lastIrrigation: '2026-08-24 07:20:00', lastIrrigationDuration: 18, unhandledAlerts: 0,
  },
  {
    plotId: 'P005', plotName: '五号育苗棚', farmId: 'F002', farmName: '西区生态农场', location: '南区育苗棚', cropName: '生菜', cropStage: '幼苗期',
    temperature: 24.3, humidity: 51, threshold: 40, cooldown: 25, maxDuration: 35, status: 'normal', irrigating: false,
    deviceOnline: true, dataState: 'realtime', updateTime: '2026-08-24 09:57:42', sensorId: 'SENSOR-013', valveId: 'VALVE-005', lastHeartbeat: '2026-08-24 09:57:45',
    devices: {
      temperature: { id: 'D013', deviceNo: 'SENSOR-013', mqttId: 'device_013', type: '温度传感器', msgId: 'M02010', topic: 'farm/telemetry/device_013' },
      humidity: { id: 'D014', deviceNo: 'SENSOR-014', mqttId: 'device_014', type: '湿度传感器', msgId: 'M02011', topic: 'farm/telemetry/device_014' },
      irrigation: { id: 'D015', deviceNo: 'VALVE-005', mqttId: 'device_015', type: '灌溉设备', topic: 'farm/command/device_015' },
    },
    lastIrrigation: '2026-08-23 18:00:00', lastIrrigationDuration: 12, unhandledAlerts: 0,
  },
  {
    plotId: 'P006', plotName: '六号试验田', farmId: 'F002', farmName: '西区生态农场', location: '北区试验田', cropName: '玉米', cropStage: '拔节期',
    temperature: 31.2, humidity: 26, threshold: 32, cooldown: 30, maxDuration: 70, status: 'alert', irrigating: false,
    deviceOnline: false, dataState: 'delayed', updateTime: '2026-08-24 09:18:05', sensorId: 'SENSOR-016', valveId: 'VALVE-006', lastHeartbeat: '2026-08-24 09:18:06',
    devices: {
      temperature: { id: 'D016', deviceNo: 'SENSOR-016', mqttId: 'device_016', type: '温度传感器', msgId: 'M02020', topic: 'farm/telemetry/device_016' },
      humidity: { id: 'D017', deviceNo: 'SENSOR-017', mqttId: 'device_017', type: '湿度传感器', msgId: 'M02021', topic: 'farm/telemetry/device_017' },
      irrigation: { id: 'D018', deviceNo: 'VALVE-006', mqttId: 'device_018', type: '灌溉设备', topic: 'farm/command/device_018' },
    },
    lastIrrigation: '2026-08-23 17:30:00', lastIrrigationDuration: 30, unhandledAlerts: 1,
  },
  {
    plotId: 'P007', plotName: '七号生态棚', farmId: 'F002', farmName: '西区生态农场', location: '西南生态区', cropName: '草莓', cropStage: '花果期',
    temperature: 23.9, humidity: 43, threshold: 38, cooldown: 30, maxDuration: 40, status: 'irrigating', irrigating: true,
    deviceOnline: true, dataState: 'realtime', updateTime: '2026-08-24 09:59:11', sensorId: 'SENSOR-019', valveId: 'VALVE-007', lastHeartbeat: '2026-08-24 09:59:15',
    devices: {
      temperature: { id: 'D019', deviceNo: 'SENSOR-019', mqttId: 'device_019', type: '温度传感器', msgId: 'M02030', topic: 'farm/telemetry/device_019' },
      humidity: { id: 'D020', deviceNo: 'SENSOR-020', mqttId: 'device_020', type: '湿度传感器', msgId: 'M02031', topic: 'farm/telemetry/device_020' },
      irrigation: { id: 'D021', deviceNo: 'VALVE-007', mqttId: 'device_021', type: '灌溉设备', topic: 'farm/command/device_021' },
    },
    lastIrrigation: '2026-08-24 09:10:00', lastIrrigationDuration: null, unhandledAlerts: 0,
  },
]

export const farmerAlerts = [
  { alertId: 'A001', plotId: 'P001', plotName: '一号温室', deviceId: 'SENSOR-001', type: '湿度过低', level: '高', reason: '当前湿度 28.5%，低于阈值 35%', value: '28.5%', threshold: '35%', occurTime: '2026-08-22 09:05:00', recoverTime: '', status: '未处理' },
  { alertId: 'A002', plotId: 'P001', plotName: '一号温室', deviceId: 'SENSOR-001', type: '数据未更新', level: '中', reason: '传感器曾连续 18 分钟未上报，当前已处理', value: '18分钟', threshold: '15分钟', occurTime: '2026-08-22 07:42:00', handledAt: '2026-08-22 08:00:00', status: '已处理' },
  { alertId: 'A003', plotId: 'P002', plotName: '二号大棚', deviceId: 'VALVE-002', type: '灌溉失败', level: '中', reason: '灌溉控制器执行异常，正在排查', value: '35', threshold: '45', occurTime: '2026-08-22 09:35:00', handledAt: '', status: '处理中' },
]

const mockToday = new Date().toLocaleDateString('sv-SE')

export const farmerIrrigationRecords = [
  { recordId: 'IR005', plotId: 'P004', plotName: '四号温室', deviceId: 'VALVE-004', operator: '张三', operationType: '开启', startTime: `${mockToday} 07:20:00`, endTime: `${mockToday} 07:38:00`, duration: 18, status: '成功', source: '页面' },
  { recordId: 'IR006', plotId: 'P007', plotName: '七号生态棚', deviceId: 'VALVE-007', operator: '张三', operationType: '开启', activationType: '手动', startTime: `${mockToday} 09:10:00`, endTime: '', duration: '-', status: '进行中', source: '手动' },
  { recordId: 'IR001', plotId: 'P002', plotName: '二号大棚', deviceId: 'VALVE-002', operator: '张三', operationType: '开启', activationType: '手动', startTime: '2026-08-22 09:00:00', endTime: '', duration: '-', status: '进行中', source: '手动' },
  { recordId: 'IR002', plotId: 'P001', plotName: '一号温室', deviceId: 'VALVE-001', operator: '张三', operationType: '开启', startTime: '2026-08-22 08:00:00', endTime: '2026-08-22 08:20:00', duration: 20, status: '成功', source: '智能问答确认' },
  { recordId: 'IR003', plotId: 'P001', plotName: '一号温室', deviceId: 'VALVE-001', operator: '张三', operationType: '开启', startTime: '2026-08-21 18:10:00', endTime: '2026-08-21 18:35:00', duration: 25, status: '成功', source: '页面' },
  { recordId: 'IR004', plotId: 'P002', plotName: '二号大棚', deviceId: 'VALVE-002', operator: '张三', operationType: '开启', startTime: '2026-08-21 06:30:00', endTime: '2026-08-21 06:50:00', duration: 20, status: '成功', source: '页面' },
]

const baseTrend = {
  P001: { temperature: [22.8, 23.5, 24.6, 25.8, 27.1, 26.7, 25.6], soilHumidity: [38, 36, 34, 31, 29, 28, 28.5] },
  P002: { temperature: [23.2, 24.1, 25.5, 27, 28.2, 27.8, 27.2], soilHumidity: [36, 35, 34, 33, 34, 39, 42] },
  P003: { temperature: [24.5, 26, 28.3, 30.2, 31.5, 30.8, 30.1], soilHumidity: [31, 29, 27, 25, 23, 22, 22] },
}

export function getFarmerTrend(plotId, period = '24h') {
  const data = baseTrend[plotId] || baseTrend.P001
  if (period === '7d') {
    return { times: ['8/16', '8/17', '8/18', '8/19', '8/20', '8/21', '8/22'], temperature: data.temperature, soilHumidity: data.soilHumidity, events: [{ index: 2, label: '灌溉' }, { index: 5, label: '灌溉' }] }
  }
  return { times: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '现在'], temperature: data.temperature, soilHumidity: data.soilHumidity, events: [{ index: plotId === 'P002' ? 5 : 2, label: '灌溉' }] }
}

export const weatherCurrent = { city: '重庆市北碚区', condition: '多云', temperature: 29, feelsLike: 31, high: 32, low: 23, rainProbability: 10, humidity: 58, wind: '东南风 2级', updatedAt: '10:20' }
export const hourlyForecast = [
  { time: '现在', icon: 'Cloudy', temperature: 29, rain: 10 }, { time: '12:00', icon: 'Sunny', temperature: 31, rain: 10 },
  { time: '14:00', icon: 'Sunny', temperature: 32, rain: 10 }, { time: '16:00', icon: 'PartlyCloudy', temperature: 31, rain: 15 },
  { time: '18:00', icon: 'Cloudy', temperature: 28, rain: 20 }, { time: '20:00', icon: 'Drizzling', temperature: 26, rain: 35 },
]
export const dailyForecast = [
  { day: '今天', condition: '多云', icon: 'Cloudy', high: 32, low: 23, rain: 10 }, { day: '周日', condition: '小雨', icon: 'Drizzling', high: 29, low: 22, rain: 65 },
  { day: '周一', condition: '阴', icon: 'PartlyCloudy', high: 28, low: 21, rain: 30 }, { day: '周二', condition: '晴', icon: 'Sunny', high: 31, low: 22, rain: 10 },
  { day: '周三', condition: '晴', icon: 'Sunny', high: 33, low: 24, rain: 5 }, { day: '周四', condition: '雷阵雨', icon: 'Lightning', high: 30, low: 23, rain: 70 },
  { day: '周五', condition: '多云', icon: 'Cloudy', high: 31, low: 23, rain: 20 },
]
