export const sensorSummary = [
  { key: 'temperature', label: '环境温度', value: 26.5, unit: '℃', icon: 'Sunny', tone: 'orange' },
  { key: 'soilHumidity', label: '土壤湿度', value: 37, unit: '%', icon: 'Drizzling', tone: 'blue' },
  { key: 'light', label: '光照强度', value: 850, unit: 'Lux', icon: 'Sunrise', tone: 'yellow' },
  { key: 'co2', label: 'CO₂ 浓度', value: 425, unit: 'ppm', icon: 'Cloudy', tone: 'green' },
]

export const environmentTrend = {
  times: ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00'],
  temperature: [22.8, 24.1, 26.2, 28.1, 27.4, 25.9],
  soilHumidity: [46, 43, 41, 39, 37, 38],
}

export const deviceStatus = [
  { name: '环境传感器 S-01', status: 'online', updatedAt: '刚刚' },
  { name: '土壤传感器 S-02', status: 'online', updatedAt: '1 分钟前' },
  { name: '智能灌溉阀 V-01', status: 'standby', updatedAt: '3 分钟前' },
]
