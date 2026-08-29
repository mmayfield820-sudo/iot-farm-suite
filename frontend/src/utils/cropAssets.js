import fengjieLateOrange from '@/assets/crops/奉节晚橙.png'
import fengyuan72Orange from '@/assets/crops/奉园72-1脐橙.png'
import fengyuan91Orange from '@/assets/crops/奉园91脐橙.png'
import hongcui2Orange from '@/assets/crops/红翠2号.png'

export const orangeCropBackgrounds = {
  奉节晚橙: fengjieLateOrange,
  '奉园72-1脐橙': fengyuan72Orange,
  奉园91脐橙: fengyuan91Orange,
  红翠2号: hongcui2Orange,
}

export const orangeCropFallbacks = Object.values(orangeCropBackgrounds)

export function orangeCropBackground(cropName, index = 0) {
  return orangeCropBackgrounds[cropName]
    || orangeCropFallbacks[index % orangeCropFallbacks.length]
}
