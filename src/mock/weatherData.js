export const weatherNow = {
  city: '示范农场', condition: '晴', temperature: 29, high: 31, low: 22,
  rainProbability: 10, rainfall: 0, wind: '东南风 2级', humidity: 48,
}

export const irrigationDecision = {
  action: '建议灌溉', level: 'recommended', time: '18:00', duration: 20,
  threshold: 40, soilHumidity: 37, confidence: 92,
  reasons: ['土壤湿度已低于 40% 的设定阈值', '未来 6 小时降雨概率仅为 10%', '傍晚灌溉可减少高温时段的蒸发损失'],
}
