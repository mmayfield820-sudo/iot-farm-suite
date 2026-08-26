export const platformFarms = [
  { farmId: 'F001', name: '一号示范农场', location: '重庆市北碚区', status: '正常', plotCount: 5 },
  { farmId: 'F002', name: '西区试验农场', location: '重庆市璧山区', status: '正常', plotCount: 3 },
]

export const platformPlots = [
  { internalId: 1, farmId: 'F001', plotNo: 'P001', name: '一号温室', crop: '番茄', note: '结果期' },
  { internalId: 2, farmId: 'F001', plotNo: 'P002', name: '二号大棚', crop: '辣椒', note: '开花期' },
  { internalId: 3, farmId: 'F001', plotNo: 'P003', name: '三号露地', crop: '空心菜', note: '生长期' },
  { internalId: 4, farmId: 'F001', plotNo: 'P004', name: '四号育苗区', crop: '番茄幼苗', note: '育苗期' },
  { internalId: 5, farmId: 'F001', plotNo: 'P005', name: '五号试验田', crop: '试验作物', note: '' },
  { internalId: 101, farmId: 'F002', plotNo: 'P101', name: '西区一号田', crop: '水稻', note: '生长期' },
]

export const platformDevices = [
  { id: 'D001', deviceNo: 'SENSOR-001', mqttId: 'device_001', type: '温度传感器', farmId: 'F001', plotNo: 'P001', status: '在线', lastHeartbeat: '2026-08-22 10:25:20', lastDataAt: '2026-08-22 10:25:18', latestValue: '25.6℃', msgId: 'M01842' },
  { id: 'D002', deviceNo: 'SENSOR-002', mqttId: 'device_002', type: '湿度传感器', farmId: 'F001', plotNo: 'P001', status: '在线', lastHeartbeat: '2026-08-22 10:25:20', lastDataAt: '2026-08-22 10:25:18', latestValue: '28.5%', msgId: 'M01839' },
  { id: 'D003', deviceNo: 'SENSOR-003', mqttId: 'device_003', type: '灌溉设备', farmId: 'F001', plotNo: 'P001', status: '在线', lastHeartbeat: '2026-08-22 10:25:19', lastDataAt: '-', latestValue: '关闭', msgId: '-' },
  { id: 'D004', deviceNo: 'SENSOR-004', mqttId: 'device_004', type: '温度传感器', farmId: 'F001', plotNo: 'P002', status: '在线', lastHeartbeat: '2026-08-22 10:25:05', lastDataAt: '2026-08-22 10:24:46', latestValue: '27.2℃', msgId: 'M01125' },
  { id: 'D005', deviceNo: 'SENSOR-005', mqttId: 'device_005', type: '湿度传感器', farmId: 'F001', plotNo: 'P002', status: '在线', lastHeartbeat: '2026-08-22 10:25:05', lastDataAt: '2026-08-22 10:24:46', latestValue: '42%', msgId: 'M01124' },
  { id: 'D006', deviceNo: 'SENSOR-006', mqttId: 'device_006', type: '灌溉设备', farmId: 'F001', plotNo: 'P002', status: '在线', lastHeartbeat: '2026-08-22 10:24:58', lastDataAt: '-', latestValue: '运行中', msgId: '-' },
  { id: 'D007', deviceNo: 'SENSOR-007', mqttId: 'device_007', type: '温度传感器', farmId: 'F001', plotNo: 'P003', status: '在线', lastHeartbeat: '2026-08-22 10:20:00', lastDataAt: '2026-08-22 10:02:00', latestValue: '30.1℃', msgId: 'M00680' },
  { id: 'D008', deviceNo: 'SENSOR-008', mqttId: 'device_008', type: '湿度传感器', farmId: 'F001', plotNo: 'P003', status: '异常', lastHeartbeat: '2026-08-22 10:20:00', lastDataAt: '2026-08-22 10:02:00', latestValue: '22%', msgId: 'M00677' },
  { id: 'D009', deviceNo: 'SENSOR-009', mqttId: 'device_009', type: '灌溉设备', farmId: 'F001', plotNo: '', status: '离线', lastHeartbeat: '2026-08-20 16:30:00', lastDataAt: '-', latestValue: '-', msgId: '-' },
  { id: 'D101', deviceNo: 'SENSOR-101', mqttId: 'device_101', type: '温度传感器', farmId: 'F002', plotNo: 'P101', status: '在线', lastHeartbeat: '2026-08-22 10:24:30', lastDataAt: '2026-08-22 10:24:28', latestValue: '29.3℃', msgId: 'M10101' },
  { id: 'D102', deviceNo: 'SENSOR-102', mqttId: 'device_102', type: '湿度传感器', farmId: 'F002', plotNo: 'P101', status: '在线', lastHeartbeat: '2026-08-22 10:24:30', lastDataAt: '2026-08-22 10:24:28', latestValue: '24%', msgId: 'M10102' },
  { id: 'D103', deviceNo: 'VALVE-101', mqttId: 'device_103', type: '灌溉设备', farmId: 'F002', plotNo: 'P101', status: '在线', lastHeartbeat: '2026-08-22 10:24:29', lastDataAt: '-', latestValue: '关闭', msgId: 'M10103' },
]

export const platformUsers = [
  { id: 'U001', username: 'zhangsan', name: '张三', email: 'zhangsan@example.com', roles: ['农户', '农场管理员', '系统管理员'], status: '正常', farmScope: 'F001', plotScope: 'P001', lastLogin: '2026-08-22 09:48:12' },
  { id: 'U002', username: 'lisi', name: '李四', email: 'lisi@example.com', roles: ['农户'], status: '正常', farmScope: 'F001', plotScope: 'P003', lastLogin: '2026-08-21 19:22:05' },
  { id: 'U003', username: 'wangwu', name: '王五', email: '', roles: ['农场管理员'], status: '正常', farmScope: 'F002', plotScope: '-', lastLogin: '2026-08-20 08:15:44' },
  { id: 'U004', username: 'disabled_user', name: '赵六', email: 'zhaoliu@example.com', roles: ['农户'], status: '禁用', farmScope: 'F001', plotScope: 'P004', lastLogin: '2026-08-18 15:30:12' },
]

export const platformAlerts = [
  { id: 'A001', farmId: 'F001', farmName: '一号示范农场', plotNo: 'P001', plotName: '一号温室', deviceId: 'D002', type: '湿度过低', value: '28.5%', threshold: '35%', occurTime: '2026-08-22 09:05:00', handledAt: '', status: '未处理', process: ['09:05 系统生成告警'] },
  { id: 'A002', farmId: 'F001', farmName: '一号示范农场', plotNo: 'P003', plotName: '三号露地', deviceId: 'D008', type: '数据未更新', value: '-', threshold: '-', occurTime: '2026-08-22 08:50:00', handledAt: '', status: '未处理', process: ['08:50 超过离线判定时间', '09:10 管理员查看设备'] },
  { id: 'A003', farmId: 'F001', farmName: '一号示范农场', plotNo: 'P005', plotName: '五号试验田', deviceId: 'D009', type: '设备离线', value: '-', threshold: '-', occurTime: '2026-08-22 08:30:00', handledAt: '2026-08-22 09:30:00', status: '已处理', process: ['08:30 设备离线', '09:00 已确认', '09:30 标记处理'] },
  { id: 'A004', farmId: 'F002', farmName: '西区试验农场', plotNo: 'P101', plotName: '西区一号田', deviceId: 'D101', type: '湿度过低', value: '24%', threshold: '32%', occurTime: '2026-08-22 07:20:00', handledAt: '', status: '未处理', process: ['07:20 系统生成告警'] },
]

export const platformAuditLogs = [
  { id: 'LOG001', time: '2026-08-22 10:02:18', user: '张三(U001)', module: '远程控制', action: '向 device_003 下发 irrigation_on', result: '成功', ip: '192.168.1.18' },
  { id: 'LOG002', time: '2026-08-22 09:40:06', user: '张三(U001)', module: '阈值配置', action: 'P001 湿度阈值 32% → 35%', result: '成功', ip: '192.168.1.18' },
  { id: 'LOG003', time: '2026-08-22 09:10:22', user: '王五(U003)', module: '设备管理', action: '查看 D008 异常信息', result: '成功', ip: '192.168.1.33' },
  { id: 'LOG004', time: '2026-08-21 16:42:35', user: 'admin(U001)', module: '用户管理', action: '禁用账号 U004', result: '成功', ip: '192.168.1.10' },
  { id: 'LOG005', time: '2026-08-21 15:20:10', user: '王五(U003)', module: '设备绑定', action: 'D009 从 P003 解绑', result: '成功', ip: '192.168.1.33' },
]

export const initialSystemParams = {
  humidityMin: 20, humidityMax: 70, defaultHumidity: 35, offlineMinutes: 30,
  staleDataMinutes: 15, alertCooldown: 30, irrigationMaxMinutes: 60, commandTimeoutSeconds: 10, commandRetryCount: 2,
}
