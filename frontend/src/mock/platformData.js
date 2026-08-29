const simulatorDeviceRows = [
  ['D001', 'P001-TEMP', '3b8dcefd-3a51-4adc-b452-47c184c0951d', '温度传感器', 'F001', 'P001', '25.7℃'],
  ['D002', 'P001-MOIST', '814621f7-2561-49ad-9766-72d3fcd18d86', '湿度传感器', 'F001', 'P001', '46.4%'],
  ['D003', 'P001-IRRIG', '435106ba-01e7-4745-9646-3907d15b28df', '灌溉设备', 'F001', 'P001', '关闭'],
  ['D004', 'P002-TEMP', '77448f68-baa9-46f1-b380-d835d4e2dda6', '温度传感器', 'F001', 'P002', '25.1℃'],
  ['D005', 'P002-MOIST', '8e52cfa5-9106-45c2-8645-2a26f9d0e554', '湿度传感器', 'F001', 'P002', '42.3%'],
  ['D006', 'P002-IRRIG', 'b0242636-5e56-4c0f-9b82-5a407e6e23ea', '灌溉设备', 'F001', 'P002', '关闭'],
  ['D007', 'P003-TEMP', '4ae3704f-4ef1-42f2-9301-4af74fcf6454', '温度传感器', 'F001', 'P003', '24.2℃'],
  ['D008', 'P003-MOIST', 'ff8706d0-2058-48fa-aa90-b95a4f61553c', '湿度传感器', 'F001', 'P003', '40.6%'],
  ['D009', 'P003-IRRIG', '1b8a4d7c-5e9c-4788-b8d1-3c02b0505664', '灌溉设备', 'F001', 'P003', '关闭'],
]

export const platformFarms = [
  { farmId: 'F001', name: '奉节县朱衣橙园', city: '重庆市奉节县', address: '朱衣镇脐橙产业园', active: true, createdAt: '2026-08-01 09:00:00' },
  { farmId: 'F002', name: '奉节县安坪橙园', city: '重庆市奉节县', address: '安坪镇临江果园', active: true, createdAt: '2026-08-02 09:00:00' },
]

export const platformPlots = [
  { internalId: '1', plotNo: 'P001', farmId: 'F001', name: '朱衣一号果园', crop: '奉园72-1脐橙', location: '朱衣镇东坡 A 区', note: '果实膨大期', active: true },
  { internalId: '2', plotNo: 'P002', farmId: 'F001', name: '朱衣二号果园', crop: '奉园91脐橙', location: '朱衣镇河谷 B 区', note: '果实转色期', active: true },
  { internalId: '3', plotNo: 'P003', farmId: 'F001', name: '朱衣晚熟果园', crop: '奉节晚橙', location: '朱衣镇南坡 C 区', note: '秋梢生长期', active: true },
  { internalId: '4', plotNo: 'P004', farmId: 'F002', name: '安坪红翠果园', crop: '红翠2号', location: '安坪镇临江 D 区', note: '幼树整形期，等待接入设备', active: true },
]

export const platformDevices = simulatorDeviceRows.map(([id, deviceNo, deviceUuid, type, farmId, plotNo, latestValue]) => ({
  id, deviceNo, deviceUuid, mqttId: deviceUuid, type, farmId, plotNo, plotId: plotNo,
  status: '在线', latestValue, lastHeartbeat: '刚刚',
}))

export const platformUsers = [
  { id: 'U001', username: 'demo_admin', name: '张园长', phone: '13800000001', email: 'admin@orange.local', roles: ['农场管理员'], farmScope: 'F001, F002', plotScope: '-', lastLogin: '2026-08-28 09:20:00', status: '正常' },
  { id: 'U002', username: 'demo_farmer', name: '李果农', phone: '13800000002', email: 'farmer@orange.local', roles: ['农户'], farmScope: '-', plotScope: 'P001, P002, P003, P004', lastLogin: '2026-08-28 09:18:00', status: '正常' },
  { id: 'U003', username: 'demo_system', name: '王管理员', phone: '13800000003', email: 'system@orange.local', roles: ['系统管理员'], farmScope: '-', plotScope: '-', lastLogin: '2026-08-28 09:10:00', status: '正常' },
]

export const platformAlerts = [
  { id: 'A001', type: '墒情偏低', level: '中', farmId: 'F001', plotNo: 'P001', occurTime: '2026-08-28 06:30:00', status: '未处理', reason: '土壤湿度接近配置阈值' },
  { id: 'A002', type: '温度偏高', level: '低', farmId: 'F001', plotNo: 'P002', occurTime: '2026-08-28 05:20:00', status: '处理中', reason: '午间温度短时超过阈值' },
  { id: 'A003', type: '设备未接入', level: '低', farmId: 'F002', plotNo: 'P004', occurTime: '2026-08-27 16:00:00', status: '未处理', reason: '该地块暂未绑定模拟设备' },
]

export const platformAuditLogs = [
  { id: 'LOG001', time: '2026-08-28 09:20:00', user: '张园长', module: '橙园管理', action: '查看朱衣橙园概览', result: '成功', ip: '127.0.0.1' },
  { id: 'LOG002', time: '2026-08-28 09:18:00', user: '李果农', module: '地块管理', action: '查看四个授权地块', result: '成功', ip: '127.0.0.1' },
  { id: 'LOG003', time: '2026-08-28 09:12:00', user: '王管理员', module: '设备管理', action: '核对设备绑定', result: '成功', ip: '127.0.0.1' },
  { id: 'LOG004', time: '2026-08-28 08:55:00', user: '张园长', module: '告警管理', action: '确认墒情告警', result: '成功', ip: '127.0.0.1' },
  { id: 'LOG005', time: '2026-08-28 08:30:00', user: '李果农', module: '智慧灌溉', action: '完成朱衣一号果园灌溉', result: '成功', ip: '127.0.0.1' },
  { id: 'LOG006', time: '2026-08-28 08:10:00', user: '张园长', module: '农场切换', action: '切换至安坪橙园', result: '成功', ip: '127.0.0.1' },
  { id: 'LOG007', time: '2026-08-28 07:50:00', user: '王管理员', module: '用户管理', action: '查看演示账号', result: '成功', ip: '127.0.0.1' },
  { id: 'LOG008', time: '2026-08-28 07:30:00', user: '李果农', module: '智能助手', action: '查询灌溉建议', result: '成功', ip: '127.0.0.1' },
]

export const initialSystemParams = {
  heartbeatTimeoutMinutes: 10,
  commandTimeoutSeconds: 15,
  commandRetryCount: 2,
  dataDelayMinutes: 10,
  alertRetentionDays: 180,
  irrigationSafetyMinutes: 60,
}
