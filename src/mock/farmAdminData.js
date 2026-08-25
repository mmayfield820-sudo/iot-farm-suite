/**
 * 模拟数据 - 后端接口未就绪时使用
 * 真实环境切换：在 api 文件中注释掉 mock 调用即可
 */

export const mockPlots = [
  {
    plotId: 'P001',
    plotName: '一号温室',
    farmId: 'F001',
    farmName: '示范农场',
    temperature: 25.6,
    humidity: 28.5,
    threshold: 35,
    maxDuration: 60,
    status: 'alert',
    deviceOnline: true,
    irrigating: false,
    unhandledAlerts: 2,
    updateTime: '2026-08-22 09:15:00',
    deviceId: 'D001',
    cropName: '番茄'
  },
  {
    plotId: 'P002',
    plotName: '二号大棚',
    farmId: 'F001',
    farmName: '示范农场',
    temperature: 27.2,
    humidity: 42.0,
    threshold: 35,
    maxDuration: 45,
    status: 'irrigating',
    deviceOnline: true,
    irrigating: true,
    unhandledAlerts: 0,
    updateTime: '2026-08-22 09:14:30',
    deviceId: 'D002',
    cropName: '辣椒'
  },
  {
    plotId: 'P003',
    plotName: '三号露地',
    farmId: 'F001',
    farmName: '示范农场',
    temperature: 30.1,
    humidity: 22.0,
    threshold: 30,
    maxDuration: 60,
    status: 'dry',
    deviceOnline: true,
    irrigating: false,
    unhandledAlerts: 1,
    updateTime: '2026-08-22 09:13:00',
    deviceId: 'D003',
    cropName: '空心菜'
  },
  {
    plotId: 'P004',
    plotName: '四号育苗区',
    farmId: 'F001',
    farmName: '示范农场',
    temperature: 24.5,
    humidity: 55.0,
    threshold: 40,
    maxDuration: 30,
    status: 'normal',
    deviceOnline: true,
    irrigating: false,
    unhandledAlerts: 0,
    updateTime: '2026-08-22 09:15:00',
    deviceId: 'D004',
    cropName: '番茄幼苗'
  },
  {
    plotId: 'P005',
    plotName: '五号试验田',
    farmId: 'F001',
    farmName: '示范农场',
    temperature: 26.0,
    humidity: 33.0,
    threshold: 35,
    maxDuration: 60,
    status: 'offline',
    deviceOnline: false,
    irrigating: false,
    unhandledAlerts: 1,
    updateTime: '2026-08-22 08:00:00',
    deviceId: 'D005',
    cropName: '试验作物'
  }
]

export const mockAlerts = [
  {
    alertId: 'A001',
    alertType: '湿度过低',
    plotId: 'P001',
    plotName: '一号温室',
    deviceId: 'D001',
    reason: '当前湿度28.5%，低于阈值35%',
    triggerValue: '28.5%',
    threshold: '35%',
    occurTime: '2026-08-22 09:05:00',
    recoverTime: '',
    status: '未处理'
  },
  {
    alertId: 'A002',
    alertType: '湿度过低',
    plotId: 'P003',
    plotName: '三号露地',
    deviceId: 'D003',
    reason: '当前湿度22.0%，低于阈值30%',
    triggerValue: '22.0%',
    threshold: '30%',
    occurTime: '2026-08-22 08:50:00',
    recoverTime: '',
    status: '未处理'
  },
  {
    alertId: 'A003',
    alertType: '设备离线',
    plotId: 'P005',
    plotName: '五号试验田',
    deviceId: 'D005',
    reason: '设备SENSOR-005超过30分钟未上报心跳',
    triggerValue: '-',
    threshold: '30分钟',
    occurTime: '2026-08-22 08:30:00',
    recoverTime: '',
    status: '处理中'
  },
  {
    alertId: 'A004',
    alertType: '湿度过低',
    plotId: 'P001',
    plotName: '一号温室',
    deviceId: 'D001',
    reason: '当前湿度28.5%，低于阈值35%',
    triggerValue: '28.5%',
    threshold: '35%',
    occurTime: '2026-08-22 07:20:00',
    recoverTime: '2026-08-22 08:15:00',
    status: '已处理'
  },
  {
    alertId: 'A005',
    alertType: '数据未更新',
    plotId: 'P002',
    plotName: '二号大棚',
    deviceId: 'D002',
    reason: '传感器数据超过1小时未更新',
    triggerValue: '-',
    threshold: '1小时',
    occurTime: '2026-08-22 06:00:00',
    recoverTime: '2026-08-22 07:30:00',
    status: '已处理'
  }
]

export const mockIrrigationRecords = [
  {
    recordId: 'IR001',
    plotId: 'P002',
    deviceId: 'D002',
    operator: '张三',
    operatorId: 'U001',
    operationType: '开启',
    startTime: '2026-08-22 09:00:00',
    endTime: '',
    duration: '-',
    status: '进行中',
    source: '页面'
  },
  {
    recordId: 'IR002',
    plotId: 'P001',
    deviceId: 'D001',
    operator: '李四',
    operatorId: 'U002',
    operationType: '开启',
    startTime: '2026-08-22 08:00:00',
    endTime: '2026-08-22 08:20:00',
    duration: 20,
    status: '成功',
    source: '智能问答'
  },
  {
    recordId: 'IR003',
    plotId: 'P003',
    deviceId: 'D003',
    operator: '王五',
    operatorId: 'U003',
    operationType: '开启',
    startTime: '2026-08-22 07:00:00',
    endTime: '2026-08-22 07:05:00',
    duration: 5,
    status: '失败',
    source: '页面'
  },
  {
    recordId: 'IR004',
    plotId: 'P002',
    deviceId: 'D002',
    operator: '张三',
    operatorId: 'U001',
    operationType: '开启',
    startTime: '2026-08-22 06:30:00',
    endTime: '2026-08-22 06:50:00',
    duration: 20,
    status: '成功',
    source: '页面'
  }
]
