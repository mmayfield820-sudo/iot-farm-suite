export const FARM_TASK_TYPES = [
  { value: 'PATROL', label: '巡园检查' },
  { value: 'IRRIGATION_CHECK', label: '墒情与灌溉检查' },
  { value: 'IRRIGATION', label: '灌溉作业' },
  { value: 'FERTILIZATION', label: '施肥管理' },
  { value: 'PRUNING', label: '整形修剪' },
  { value: 'PEST_CONTROL', label: '病虫害防治' },
  { value: 'WEEDING', label: '除草管理' },
  { value: 'HARVEST_PREP', label: '采收准备' },
  { value: 'HARVEST', label: '采收作业' },
  { value: 'CLEANUP', label: '采后清园' },
  { value: 'OTHER', label: '其他农事' },
]

export const FARM_TASK_TYPE_LABELS = Object.fromEntries(FARM_TASK_TYPES.map((item) => [item.value, item.label]))
export const farmTaskTypeLabel = (value) => FARM_TASK_TYPE_LABELS[value] || value || '其他农事'
