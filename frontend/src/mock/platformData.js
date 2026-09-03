export const platformFarms = [
  { farmId: 'F001', name: '奉节朱衣脐橙示范园', province: '重庆市', city: '奉节县', address: '重庆市奉节县朱衣镇双碾村脐橙产业园', areaMu: 126.5, managerEmployeeNo: 'E000001', managerName: '林致远', note: '奉节脐橙标准化种植与智慧农业示范基地', status: 'active', updatedAt: '2026-08-22 10:25:20' },
  { farmId: 'F002', name: '长江北岸脐橙园', province: '重庆市', city: '奉节县', address: '永乐镇大坝村', areaMu: 88, managerEmployeeNo: '', managerName: '', note: '', status: 'active', updatedAt: '2026-08-20 16:30:00' },
]

export const platformPlots = [
  { internalId: 1, farmId: 'F001', plotNo: 'P001', code: 'FJ-001', name: '东坡一号果园', areaMu: 42.5, location: '示范园东区缓坡梯田', irrigationMethod: 'drip', status: 'active', crop: '脐橙', note: '东坡标准化脐橙种植区' },
  { internalId: 2, farmId: 'F001', plotNo: 'P002', code: 'FJ-002', name: '东坡二号地块', areaMu: 24, location: '橙园东坡下段', irrigationMethod: 'drip', status: 'active', crop: '脐橙', note: '开花坐果期' },
  { internalId: 3, farmId: 'F001', plotNo: 'P003', code: 'FJ-003', name: '河谷二号果园', areaMu: 38, location: '示范园西区临河台地', irrigationMethod: 'sprinkler', status: 'active', crop: '脐橙', note: '河谷水肥一体化脐橙种植区' },
  { internalId: 4, farmId: 'F001', plotNo: 'P004', code: 'FJ-004', name: '高坡试验果园', areaMu: 46, location: '示范园北区高坡水肥试验区', irrigationMethod: 'manual', status: 'active', crop: '脐橙', note: '高坡智慧水肥试验区' },
  { internalId: 5, farmId: 'F001', plotNo: 'P005', code: 'FJ-005', name: '北坡试验地块', areaMu: 20, location: '橙园北坡', irrigationMethod: 'other', status: 'active', crop: '脐橙', note: '冬季管护期' },
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
]

export const platformUsers = [
  { id: 'U001', employeeNo: 'E000001', name: '林致远', email: 'linzhiyuan@example.com', roles: ['农场管理员'], status: '正常', farmScope: 'F001', plotScope: '-', lastLogin: '2026-08-22 09:48:12' },
  { id: 'U002', employeeNo: 'E000002', name: '陈明远', email: 'chenmingyuan@example.com', roles: ['农户'], status: '正常', farmScope: 'F001', plotScope: 'P001, P003', lastLogin: '2026-08-21 19:22:05' },
  { id: 'U003', employeeNo: 'E000003', name: '许文澜', email: 'xuwenlan@example.com', roles: ['系统管理员'], status: '正常', farmScope: '-', plotScope: '-', lastLogin: '2026-08-20 08:15:44' },
  { id: 'U004', employeeNo: 'E000004', name: '周晓梅', email: 'zhouxiaomei@example.com', roles: ['农户'], status: '正常', farmScope: 'F001', plotScope: 'P004', lastLogin: '2026-08-18 15:30:12' },
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
