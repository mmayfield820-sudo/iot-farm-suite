/**
 * 地块状态相关工具函数
 */

export const STATUS_CONFIG = {
  normal: { label: '正常', color: '#67C23A', type: 'success' },
  dry: { label: '偏干', color: '#E6A23C', type: 'warning' },
  alert: { label: '告警', color: '#F56C6C', type: 'danger' },
  irrigating: { label: '灌溉中', color: '#409EFF', type: 'primary' },
  offline: { label: '离线', color: '#909399', type: 'info' }
}

export const getStatusConfig = (status) => STATUS_CONFIG[status] || STATUS_CONFIG.normal

export const getHumidityStatus = (humidity, threshold) => {
  if (humidity < threshold * 0.8) return 'alert'
  if (humidity < threshold) return 'dry'
  return 'normal'
}

export const ALERT_TYPE_CONFIG = {
  '超过阈值': { color: '#F56C6C', type: 'danger' },
  '湿度过低': { color: '#F56C6C', type: 'danger' },
  '湿度偏高': { color: '#E6A23C', type: 'warning' },
  '长期没被访问': { color: '#909399', type: 'info' },
  '设备故障': { color: '#E6A23C', type: 'warning' },
  '设备离线': { color: '#E6A23C', type: 'warning' },
  '数据未更新': { color: '#909399', type: 'info' },
  '灌溉失败': { color: '#F56C6C', type: 'danger' }
}

export const ALERT_STATUS_CONFIG = {
  '未处理': { type: 'danger' },
  '处理中': { type: 'warning' },
  '已处理': { type: 'success' },
  '已忽略': { type: 'info' }
}

export const IRRIGATION_STATUS = {
  '下发中': { type: 'info', icon: 'Loading' },
  '成功': { type: 'success', icon: 'CircleCheck' },
  '失败': { type: 'danger', icon: 'CircleClose' },
  '超时': { type: 'warning', icon: 'Warning' },
  '进行中': { type: 'primary', icon: 'VideoPlay' }
}
