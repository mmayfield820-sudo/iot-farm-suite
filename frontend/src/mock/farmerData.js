const simulatorDevices = {
  P001: ['3b8dcefd-3a51-4adc-b452-47c184c0951d', '814621f7-2561-49ad-9766-72d3fcd18d86', '435106ba-01e7-4745-9646-3907d15b28df'],
  P002: ['77448f68-baa9-46f1-b380-d835d4e2dda6', '8e52cfa5-9106-45c2-8645-2a26f9d0e554', 'b0242636-5e56-4c0f-9b82-5a407e6e23ea'],
  P003: ['4ae3704f-4ef1-42f2-9301-4af74fcf6454', 'ff8706d0-2058-48fa-aa90-b95a4f61553c', '1b8a4d7c-5e9c-4788-b8d1-3c02b0505664'],
}

function deviceSet(plotId) {
  const uuids = simulatorDevices[plotId]
  if (!uuids) return {}
  const number = plotId.slice(1)
  return {
    temperature: { id: `D${number}-T`, deviceNo: `${plotId}-TEMP`, mqttId: uuids[0], deviceUuid: uuids[0], type: '温度传感器', online: true },
    humidity: { id: `D${number}-M`, deviceNo: `${plotId}-MOIST`, mqttId: uuids[1], deviceUuid: uuids[1], type: '湿度传感器', online: true },
    irrigation: { id: `D${number}-I`, deviceNo: `${plotId}-IRRIG`, mqttId: uuids[2], deviceUuid: uuids[2], type: '灌溉设备', online: true },
  }
}

export const farmerPlots = [
  { plotId: 'P001', plotName: '朱衣一号果园', farmId: 'F001', farmName: '奉节县朱衣橙园', location: '朱衣镇东坡 A 区', cropName: '奉园72-1脐橙', cropStage: '果实膨大期', temperature: 25.7, humidity: 46.4, threshold: 35, maxDuration: 25, status: 'normal', irrigating: false, deviceOnline: true, dataState: 'realtime', updateTime: new Date().toISOString(), sensorId: 'P001-MOIST', valveId: 'P001-IRRIG', devices: deviceSet('P001'), unhandledAlerts: 1 },
  { plotId: 'P002', plotName: '朱衣二号果园', farmId: 'F001', farmName: '奉节县朱衣橙园', location: '朱衣镇河谷 B 区', cropName: '奉园91脐橙', cropStage: '果实转色期', temperature: 25.1, humidity: 42.3, threshold: 35, maxDuration: 20, status: 'normal', irrigating: false, deviceOnline: true, dataState: 'realtime', updateTime: new Date().toISOString(), sensorId: 'P002-MOIST', valveId: 'P002-IRRIG', devices: deviceSet('P002'), unhandledAlerts: 0 },
  { plotId: 'P003', plotName: '朱衣晚熟果园', farmId: 'F001', farmName: '奉节县朱衣橙园', location: '朱衣镇南坡 C 区', cropName: '奉节晚橙', cropStage: '秋梢生长期', temperature: 24.2, humidity: 40.6, threshold: 35, maxDuration: 20, status: 'normal', irrigating: false, deviceOnline: true, dataState: 'realtime', updateTime: new Date().toISOString(), sensorId: 'P003-MOIST', valveId: 'P003-IRRIG', devices: deviceSet('P003'), unhandledAlerts: 0 },
  { plotId: 'P004', plotName: '安坪红翠果园', farmId: 'F002', farmName: '奉节县安坪橙园', location: '安坪镇临江 D 区', cropName: '红翠2号', cropStage: '幼树整形期', temperature: 0, humidity: 0, threshold: 40, maxDuration: 15, status: 'offline', irrigating: false, deviceOnline: false, dataState: 'delayed', updateTime: '', sensorId: '-', valveId: '-', devices: {}, unhandledAlerts: 0 },
]

export const farmerAlerts = [
  { alertId: 'A001', plotId: 'P001', plotName: '朱衣一号果园', deviceId: 'P001-MOIST', type: '湿度过低', level: '中', reason: '当前墒情接近果实膨大期下限', value: '41.6%', threshold: '42%', occurTime: '2026-08-28 06:30:00', recoverTime: '', status: '未处理' },
  { alertId: 'A002', plotId: 'P002', plotName: '朱衣二号果园', deviceId: 'P002-TEMP', type: '数据波动', level: '低', reason: '温度数据曾出现短时波动，已确认恢复', value: '31.2℃', threshold: '30℃', occurTime: '2026-08-28 02:20:00', handledAt: '2026-08-28 03:10:00', status: '已处理' },
  { alertId: 'A003', plotId: 'P003', plotName: '朱衣晚熟果园', deviceId: 'P003-IRRIG', type: '灌溉失败', level: '中', reason: '灌溉指令曾出现超时，设备已恢复', value: '-', threshold: '-', occurTime: '2026-08-27 10:10:00', handledAt: '2026-08-27 11:00:00', status: '已处理' },
]

const mockToday = new Date().toLocaleDateString('sv-SE')
export const farmerIrrigationRecords = [
  { recordId: 'IR001', plotId: 'P001', plotName: '朱衣一号果园', deviceId: 'P001-IRRIG', operator: '李果农', operationType: '开启', startTime: `${mockToday} 06:30:00`, endTime: `${mockToday} 06:55:00`, duration: 25, status: '成功', source: '页面' },
  { recordId: 'IR002', plotId: 'P002', plotName: '朱衣二号果园', deviceId: 'P002-IRRIG', operator: '李果农', operationType: '开启', startTime: `${mockToday} 05:40:00`, endTime: `${mockToday} 06:00:00`, duration: 20, status: '成功', source: '页面' },
  { recordId: 'IR003', plotId: 'P003', plotName: '朱衣晚熟果园', deviceId: 'P003-IRRIG', operator: '李果农', operationType: '开启', startTime: `${mockToday} 04:30:00`, endTime: `${mockToday} 04:50:00`, duration: 20, status: '成功', source: '页面' },
]

const baseTrend = {
  P001: { temperature: [23.6,24.1,24.6,25.3,26.1,25.9,25.7], soilHumidity: [50,49,48.2,46.9,45.8,44.6,46.4] },
  P002: { temperature: [22.9,23.5,23.9,24.8,25.6,25.4,25.1], soilHumidity: [46,45,44.1,42.8,41.7,39.6,42.3] },
  P003: { temperature: [21.8,22.2,22.8,23.7,24.5,24.4,24.2], soilHumidity: [44,43,41.3,40.5,39.9,37.5,40.6] },
  P004: { temperature: [], soilHumidity: [] },
}

export function getFarmerTrend(plotId, period = '24h') {
  const data = baseTrend[plotId] || baseTrend.P001
  const times = period === '7d' ? ['8/22','8/23','8/24','8/25','8/26','8/27','8/28'] : ['00:00','04:00','08:00','12:00','16:00','20:00','现在']
  return { times, temperature: data.temperature, soilHumidity: data.soilHumidity, events: data.temperature.length ? [{ index: 4, label: '灌溉' }] : [] }
}
