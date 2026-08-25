<template>
  <section class="orchard-overview">
    <header class="map-header">
      <div class="map-title">
        <span class="location-icon">⌖</span>
        <div>
          <strong>农场地块分布</strong>
          <small>实时地块状态 · 悬停查看 · 点击进入详情</small>
        </div>
      </div>

      <div class="legend">
        <div v-for="item in legendItems" :key="item.key" class="legend-item">
          <i :class="['legend-dot', item.key]"></i>
          <span>{{ item.label }}</span>
        </div>
      </div>
    </header>

    <div
      ref="mapRef"
      class="map-container"
      @mouseleave="scheduleClearHover"
      @mouseenter="cancelClearHover"
    >
      <!-- 地图底图：不是地块本身，地块只是覆盖在这张“农场地图”上 -->
      <div class="map-background" aria-hidden="true">
        <div class="terrain terrain-a"></div>
        <div class="terrain terrain-b"></div>
        <div class="terrain terrain-c"></div>
        <div class="terrain terrain-d"></div>

        <div class="map-grid"></div>

        <svg class="road-layer" viewBox="0 0 1400 720" preserveAspectRatio="none">
          <path d="M-40 540 C210 455 320 490 505 420 S850 315 1040 355 S1260 420 1440 300" />
          <path d="M110 60 C260 190 350 260 530 275 S820 250 1010 180 S1240 115 1450 150" />
          <path d="M730 -30 C710 140 730 250 700 365 S650 590 720 760" />
          <path d="M1180 20 C1090 145 1080 260 1160 355 S1250 560 1190 750" />
        </svg>

        <div class="map-label label-1">农场主干道</div>
        <div class="map-label label-2">北侧作业区</div>
        <div class="map-label label-3">灌溉水渠</div>
      </div>

      <svg
        class="farm-svg"
        viewBox="0 0 1400 720"
        preserveAspectRatio="none"
        role="img"
        aria-label="农场地块分布图"
      >
        <defs>
          <filter id="parcelShadow" x="-20%" y="-20%" width="140%" height="150%">
            <feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#24483a" flood-opacity=".18" />
          </filter>

          <linearGradient id="normalGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#86b979" />
            <stop offset="100%" stop-color="#619f68" />
          </linearGradient>
          <linearGradient id="warningGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#d0b66d" />
            <stop offset="100%" stop-color="#ad8e48" />
          </linearGradient>
          <linearGradient id="dangerGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#806154" />
            <stop offset="100%" stop-color="#5e473c" />
          </linearGradient>
          <linearGradient id="wateringGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#5eb0c4" />
            <stop offset="100%" stop-color="#397f99" />
          </linearGradient>

          <clipPath
            v-for="farm in farms"
            :id="`rainClip-${farm.key}`"
            :key="`clip-${farm.key}`"
          >
            <polygon :points="farm.points" />
          </clipPath>
        </defs>

        <!-- 每块地来自 Voronoi 式分区：共享边界，不互相覆盖 -->
        <g
          v-for="farm in farms"
          :key="farm.key"
          class="farm-group"
          :class="[`status-${farm.status}`, { active: hoveredFarm?.key === farm.key }]"
          @mouseenter="handleHover(farm, $event)"
          @mouseleave="scheduleClearHover"
          @click.stop="openMonitor(farm)"
        >
          <polygon
            :points="farm.points"
            :fill="gradientId(farm)"
            class="farm-polygon"
            filter="url(#parcelShadow)"
          />

          <!-- 清晰的共享边界线 -->
          <polygon :points="farm.points" class="farm-border" />

          <!-- 地块内部农田纹理 -->
          <g class="field-lines">
            <line
              v-for="(line, index) in farm.fieldLines"
              :key="`${farm.key}-line-${index}`"
              :x1="line.x1"
              :y1="line.y1"
              :x2="line.x2"
              :y2="line.y2"
            />
          </g>

          <!-- 果树点位 -->
          <g class="tree-points">
            <circle
              v-for="(tree, index) in farm.trees"
              :key="`${farm.key}-tree-${index}`"
              :cx="tree.x"
              :cy="tree.y"
              r="5"
            />
          </g>

          <!-- 灌溉中的地块：整块地内部持续下雨 -->
          <g
            v-if="farm.status === 'watering'"
            :clip-path="`url(#rainClip-${farm.key})`"
            class="rain-layer"
          >
            <line
              v-for="rain in farm.rain"
              :key="rain.id"
              class="rain-drop"
              :x1="rain.x"
              :y1="rain.y"
              :x2="rain.x - 8"
              :y2="rain.y + 34"
              :style="{ animationDelay: `${rain.delay}s` }"
            />
          </g>

          <!-- 中心信息 -->
          <text
            :x="farm.center.x"
            :y="farm.center.y - 16"
            class="farm-name"
            text-anchor="middle"
          >{{ farm.name }}</text>

          <text
            :x="farm.center.x"
            :y="farm.center.y + 27"
            class="farm-humidity"
            text-anchor="middle"
          >{{ farm.humidity }}%</text>

          <text
            :x="farm.center.x"
            :y="farm.center.y + 53"
            class="farm-status"
            text-anchor="middle"
          >{{ statusText(farm) }}</text>

          <!-- 状态徽标 -->
          <g
            class="status-marker"
            :transform="`translate(${farm.marker.x}, ${farm.marker.y})`"
          >
            <circle r="26" class="marker-bg" />
            <text
              text-anchor="middle"
              dominant-baseline="central"
              class="marker-icon"
            >{{ statusIcon(farm) }}</text>
          </g>
        </g>
      </svg>

      <!-- Tooltip 独立于 SVG，永远在最上层，不会被其它地块盖住 -->
      <transition name="tooltip">
        <div
          v-if="hoveredFarm"
          class="farm-tooltip"
          :class="tooltipPosition.side"
          :style="tooltipStyle"
          @mouseenter="cancelClearHover"
          @mouseleave="scheduleClearHover"
          @click.stop
        >
          <div class="tooltip-accent" :class="`accent-${hoveredFarm.status}`"></div>

          <div class="tooltip-head">
            <div>
              <div class="tooltip-title">{{ hoveredFarm.name }}</div>
              <div class="tooltip-subtitle">地块编号：{{ hoveredFarm.id }}</div>
            </div>
            <span class="tooltip-status" :class="`tooltip-${hoveredFarm.status}`">
              {{ statusText(hoveredFarm) }}
            </span>
          </div>

          <div class="tooltip-grid">
            <div class="tooltip-item">
              <span>土壤湿度</span>
              <strong>{{ hoveredFarm.humidity }}%</strong>
            </div>
            <div class="tooltip-item">
              <span>环境温度</span>
              <strong>{{ hoveredFarm.temperature }}℃</strong>
            </div>
            <div class="tooltip-item">
              <span>设备状态</span>
              <strong>{{ hoveredFarm.device }}</strong>
            </div>
            <div class="tooltip-item">
              <span>灌溉状态</span>
              <strong>{{ hoveredFarm.irrigation }}</strong>
            </div>
          </div>

          <div class="tooltip-extra">
            <span>作物</span>
            <b>{{ hoveredFarm.cropName || '—' }}</b>
            <span>生长阶段</span>
            <b>{{ hoveredFarm.cropStage || '—' }}</b>
          </div>

          <button type="button" class="tooltip-action" @click="openMonitor(hoveredFarm)">
            进入地块详情
            <span>→</span>
          </button>
        </div>
      </transition>

      <div v-if="!farms.length" class="empty-map">
        <div class="empty-icon">⌖</div>
        <strong>暂无可展示的地块</strong>
        <span>请检查当前账号的地块权限或等待后端数据加载。</span>
      </div>

      <div class="map-tip">
        悬停查看实时数据 · 点击地块进入详情
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'

const router = useRouter()
const store = useFarmerStore()
const mapRef = ref(null)
const hoveredFarm = ref(null)
const clearTimer = ref(null)

const legendItems = [
  { key: 'normal', label: '正常' },
  { key: 'warning', label: '关注' },
  { key: 'danger', label: '异常' },
  { key: 'watering', label: '灌溉中' },
]

/*
 * 这组点是“地图上的位置锚点”，不是地块边界。
 * Voronoi 分割会自动把整个地图切成互不重叠的地块。
 * 后端以后增加/减少地块时，不需要手工重新画多边形。
 */
const SEEDS = [
  [230, 170],
  [520, 150],
  [900, 160],
  [1180, 220],
  [350, 470],
  [760, 470],
  [1130, 520],
  [980, 650],
  [180, 650],
  [1320, 610],
]

const farms = computed(() => {
  const source = Array.isArray(store.accessiblePlots) ? store.accessiblePlots : []

  return source.map((plot, index) => {
    const seed = SEEDS[index % SEEDS.length]
    const status = resolveStatus(plot)
    const cell = buildVoronoiCell(seed, source.map((_, i) => SEEDS[i % SEEDS.length]))
    const center = polygonCenter(cell)
    const marker = markerPosition(cell, center)

    return {
      key: String(plot.plotId ?? plot.id ?? index),
      id: String(plot.plotId ?? plot.id ?? index + 1),
      name: plot.plotName ?? plot.name ?? `地块 ${index + 1}`,
      humidity: Number(plot.humidity ?? 0),
      temperature: Number(plot.temperature ?? 0),
      threshold: Number(plot.threshold ?? 30),
      device: plot.deviceOnline ? '在线' : '离线',
      irrigation: plot.irrigating ? '正在灌溉' : (plot.irrigationStatus ?? '未灌溉'),
      cropName: plot.cropName,
      cropStage: plot.cropStage,
      status,
      points: cell.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' '),
      center,
      marker,
      trees: createTrees(cell, index),
      fieldLines: createFieldLines(cell, index),
      rain: status === 'watering' ? createRain(cell, index) : [],
      raw: plot,
    }
  })
})

function resolveStatus(plot) {
  if (plot.status && ['normal', 'warning', 'danger', 'watering'].includes(plot.status)) {
    return plot.status
  }
  if (plot.irrigating === true || String(plot.irrigationStatus ?? '').includes('灌溉')) {
    return 'watering'
  }
  if (plot.deviceOnline === false) return 'danger'
  const humidity = Number(plot.humidity ?? 0)
  const threshold = Number(plot.threshold ?? 30)
  return humidity < threshold ? 'warning' : 'normal'
}

/* Sutherland-Hodgman：用两点之间的垂直平分线逐个裁剪地图矩形，得到真正不重叠的分区。 */
function buildVoronoiCell(seed, allSeeds) {
  let polygon = [
    [20, 20],
    [1380, 20],
    [1380, 700],
    [20, 700],
  ]

  for (const other of allSeeds) {
    if (other[0] === seed[0] && other[1] === seed[1]) continue

    const a = 2 * (other[0] - seed[0])
    const b = 2 * (other[1] - seed[1])
    const c = other[0] ** 2 + other[1] ** 2 - seed[0] ** 2 - seed[1] ** 2
    polygon = clipPolygon(polygon, a, b, c)
    if (!polygon.length) break
  }

  return polygon
}

function clipPolygon(polygon, a, b, c) {
  if (!polygon.length) return []
  const result = []

  for (let i = 0; i < polygon.length; i += 1) {
    const current = polygon[i]
    const next = polygon[(i + 1) % polygon.length]
    const currentValue = a * current[0] + b * current[1] - c
    const nextValue = a * next[0] + b * next[1] - c
    const currentInside = currentValue <= 0
    const nextInside = nextValue <= 0

    if (currentInside) result.push(current)

    if (currentInside !== nextInside) {
      const t = currentValue / (currentValue - nextValue)
      result.push([
        current[0] + t * (next[0] - current[0]),
        current[1] + t * (next[1] - current[1]),
      ])
    }
  }

  return result
}

function polygonCenter(polygon) {
  const total = polygon.reduce((acc, [x, y]) => ({ x: acc.x + x, y: acc.y + y }), { x: 0, y: 0 })
  return {
    x: total.x / polygon.length,
    y: total.y / polygon.length,
  }
}

function markerPosition(polygon, center) {
  let best = polygon[0]
  let bestScore = -Infinity

  for (const [x, y] of polygon) {
    const distance = Math.hypot(x - center.x, y - center.y)
    if (distance > bestScore) {
      best = [x, y]
      bestScore = distance
    }
  }

  return {
    x: center.x + (best[0] - center.x) * 0.55,
    y: center.y + (best[1] - center.y) * 0.55,
  }
}

function polygonBounds(polygon) {
  return polygon.reduce((acc, [x, y]) => ({
    minX: Math.min(acc.minX, x),
    maxX: Math.max(acc.maxX, x),
    minY: Math.min(acc.minY, y),
    maxY: Math.max(acc.maxY, y),
  }), { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity })
}

function createTrees(polygon, index) {
  const bounds = polygonBounds(polygon)
  const points = []
  const offsets = [
    [0.22, 0.28], [0.48, 0.20], [0.74, 0.30],
    [0.30, 0.52], [0.58, 0.48], [0.78, 0.62],
    [0.18, 0.73], [0.46, 0.76], [0.68, 0.80],
  ]

  offsets.forEach(([rx, ry], i) => {
    const x = bounds.minX + (bounds.maxX - bounds.minX) * rx + ((index * 13 + i * 7) % 9 - 4)
    const y = bounds.minY + (bounds.maxY - bounds.minY) * ry + ((index * 11 + i * 5) % 9 - 4)
    if (pointInPolygon([x, y], polygon)) points.push({ x, y })
  })

  return points
}

function createFieldLines(polygon, index) {
  const bounds = polygonBounds(polygon)
  const lines = []
  for (let i = 0; i < 4; i += 1) {
    const y = bounds.minY + (bounds.maxY - bounds.minY) * (0.22 + i * 0.18)
    lines.push({
      x1: bounds.minX - 20,
      y1: y + index * 2,
      x2: bounds.maxX + 20,
      y2: y - 25 + index * 2,
    })
  }
  return lines
}

function createRain(polygon, index) {
  const bounds = polygonBounds(polygon)
  const drops = []
  for (let i = 0; i < 30; i += 1) {
    const x = bounds.minX + ((i * 83 + index * 47) % 1000) / 1000 * (bounds.maxX - bounds.minX)
    const y = bounds.minY + ((i * 137 + index * 71) % 1000) / 1000 * (bounds.maxY - bounds.minY)
    if (pointInPolygon([x, y], polygon)) {
      drops.push({
        id: i,
        x,
        y,
        delay: -((i * 0.11 + index * 0.17) % 1.4),
      })
    }
  }
  return drops
}

function pointInPolygon([x, y], polygon) {
  let inside = false
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0]
    const yi = polygon[i][1]
    const xj = polygon[j][0]
    const yj = polygon[j][1]
    const intersect = ((yi > y) !== (yj > y)) && (x < ((xj - xi) * (y - yi)) / (yj - yi) + xi)
    if (intersect) inside = !inside
  }
  return inside
}

const tooltipPosition = ref({ x: 0, y: 0, side: 'below' })
const tooltipStyle = computed(() => ({
  left: `${tooltipPosition.value.x}px`,
  top: `${tooltipPosition.value.y}px`,
}))

function handleHover(farm, event) {
  cancelClearHover()
  hoveredFarm.value = farm

  const rect = mapRef.value?.getBoundingClientRect()
  if (!rect) return

  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  const tooltipWidth = Math.min(360, rect.width - 32)
  const tooltipHeight = 280
  const gap = 18

  let left = x - tooltipWidth / 2
  left = Math.max(16, Math.min(left, rect.width - tooltipWidth - 16))

  const showBelow = y < tooltipHeight + 30 || rect.height - y < tooltipHeight + 30
  let top = showBelow ? y + gap : y - tooltipHeight - gap
  top = Math.max(16, Math.min(top, rect.height - tooltipHeight - 16))

  tooltipPosition.value = {
    x: left,
    y: top,
    side: showBelow ? 'below' : 'above',
  }
}

function scheduleClearHover() {
  cancelClearHover()
  clearTimer.value = window.setTimeout(() => {
    hoveredFarm.value = null
  }, 180)
}

function cancelClearHover() {
  if (clearTimer.value) {
    window.clearTimeout(clearTimer.value)
    clearTimer.value = null
  }
}

function gradientId(farm) {
  return `url(#${farm.status}Gradient)`
}

function statusText(farm) {
  if (farm.status === 'danger') return '设备离线'
  if (farm.status === 'warning') return '需要关注'
  if (farm.status === 'watering') return '灌溉中'
  return '正常'
}

function statusIcon(farm) {
  if (farm.status === 'danger') return '×'
  if (farm.status === 'warning') return '!'
  if (farm.status === 'watering') return '💧'
  return '✓'
}

function openMonitor(farm) {
  const plotId = String(farm.id)

  // 先同步 store，再进入原有地块管理页面。
  // 这样即使管理页已经打开，也能正确切换当前地块。
  if (typeof store.selectPlot === 'function') {
    store.selectPlot(plotId)
  }

  router.push({
    name: 'farmer-management',
    query: { plotId },
  })
}

onBeforeUnmount(() => {
  cancelClearHover()
})
</script>

<style scoped>
.orchard-overview {
  width: 100%;
  border: 1px solid rgba(61, 103, 78, .14);
  border-radius: 24px;
  overflow: hidden;
  background: #dfead9;
  box-shadow: 0 24px 60px rgba(39, 76, 54, .10);
}

.map-header {
  min-height: 76px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  background: rgba(255,255,255,.97);
  border-bottom: 1px solid rgba(59, 101, 76, .12);
}

.map-title { display: flex; align-items: center; gap: 12px; color: #294d3b; }
.map-title strong { display: block; font-size: 18px; font-weight: 850; }
.map-title small { display: block; margin-top: 3px; color: #91a098; font-size: 11px; }
.location-icon { color: #63a67c; font-size: 28px; font-weight: 800; }
.legend { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 7px; color: #74867c; font-size: 12px; font-weight: 650; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; box-shadow: 0 0 0 3px rgba(255,255,255,.75); }
.legend-dot.normal { background: #6da574; }
.legend-dot.warning { background: #b38b48; }
.legend-dot.danger { background: #63483c; }
.legend-dot.watering { background: #4d99ae; }

.map-container { position: relative; height: 640px; overflow: hidden; }
.map-background { position: absolute; inset: 0; background: linear-gradient(135deg,#d9ead2 0%,#cbdcc7 48%,#dce9d7 100%); overflow: hidden; }
.terrain { position: absolute; border-radius: 50%; background: rgba(104,143,89,.11); filter: blur(2px); }
.terrain-a { width: 680px; height: 260px; left: -110px; top: 30px; transform: rotate(-8deg); }
.terrain-b { width: 700px; height: 300px; right: -120px; top: 60px; transform: rotate(12deg); }
.terrain-c { width: 760px; height: 260px; left: 300px; bottom: -90px; transform: rotate(8deg); }
.terrain-d { width: 520px; height: 220px; left: 700px; top: 270px; transform: rotate(-18deg); background: rgba(255,255,255,.18); }
.map-grid { position: absolute; inset: 0; opacity: .25; background-image: linear-gradient(90deg,rgba(71,111,83,.15) 1px,transparent 1px),linear-gradient(rgba(71,111,83,.15) 1px,transparent 1px); background-size: 54px 54px; }
.road-layer { position: absolute; inset: 0; width: 100%; height: 100%; opacity: .62; }
.road-layer path { fill: none; stroke: rgba(255,255,255,.86); stroke-width: 22; stroke-linecap: round; }
.road-layer path + path { stroke-width: 13; opacity: .72; }
.map-label { position: absolute; padding: 5px 10px; border-radius: 999px; color: rgba(61,94,69,.52); background: rgba(255,255,255,.30); border: 1px solid rgba(255,255,255,.35); font-size: 11px; letter-spacing: .08em; }
.label-1 { left: 11%; top: 67%; transform: rotate(-10deg); }
.label-2 { right: 8%; top: 18%; }
.label-3 { left: 48%; top: 78%; transform: rotate(-7deg); }

.farm-svg { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 2; overflow: visible; }
.farm-group { cursor: pointer; }
.farm-polygon { opacity: .88; transition: opacity .22s ease, filter .22s ease; }
.farm-border { fill: none; stroke: rgba(255,255,255,.96); stroke-width: 5; vector-effect: non-scaling-stroke; pointer-events: none; transition: stroke-width .22s ease, stroke .22s ease; }
.farm-group:hover .farm-polygon, .farm-group.active .farm-polygon { opacity: 1; filter: brightness(1.08) url(#parcelShadow); }
.farm-group:hover .farm-border, .farm-group.active .farm-border { stroke-width: 8; }

.field-lines line { stroke: rgba(255,255,255,.18); stroke-width: 2; stroke-dasharray: 11 14; opacity: .75; pointer-events: none; }
.tree-points circle { fill: rgba(46,103,68,.76); stroke: rgba(255,255,255,.26); stroke-width: 1.5; pointer-events: none; }
.farm-name { fill: #fff; font-size: 20px; font-weight: 850; paint-order: stroke; stroke: rgba(31,66,47,.65); stroke-width: 5; stroke-linejoin: round; pointer-events: none; }
.farm-humidity { fill: #fff; font-size: 32px; font-weight: 950; paint-order: stroke; stroke: rgba(31,66,47,.56); stroke-width: 5; pointer-events: none; }
.farm-status { fill: #fff; font-size: 13px; font-weight: 750; paint-order: stroke; stroke: rgba(31,66,47,.46); stroke-width: 3; pointer-events: none; }

.status-marker { filter: drop-shadow(0 6px 8px rgba(0,0,0,.18)); pointer-events: none; }
.marker-bg { fill: rgba(255,255,255,.95); stroke: rgba(255,255,255,.92); stroke-width: 3; }
.marker-icon { font-size: 20px; font-weight: 900; }
.status-normal .marker-icon { fill: #5c9c67; }
.status-warning .marker-icon { fill: #b0833f; }
.status-danger .marker-icon { fill: #66483b; }
.status-watering .marker-icon { fill: #3d94ad; }

.rain-layer { pointer-events: none; }
.rain-drop { stroke: rgba(226,249,255,.96); stroke-width: 3; stroke-linecap: round; opacity: 0; animation: rainFall 1.05s linear infinite; transform-box: fill-box; transform-origin: center; }
@keyframes rainFall { 0% { opacity: 0; transform: translate3d(0,-38px,0); } 15% { opacity: .95; } 100% { opacity: 0; transform: translate3d(-8px,76px,0); } }

.farm-tooltip { position: absolute; z-index: 10000; width: min(360px, calc(100% - 32px)); box-sizing: border-box; padding: 22px; border-radius: 20px; background: rgba(255,255,255,.98); border: 1px solid rgba(78,128,95,.16); box-shadow: 0 28px 70px rgba(26,59,41,.28), 0 8px 24px rgba(26,59,41,.10); backdrop-filter: blur(18px); pointer-events: auto; }
.tooltip-accent { position: absolute; left: 0; top: 20px; bottom: 20px; width: 4px; border-radius: 0 5px 5px 0; }
.accent-normal { background: #6da574; } .accent-warning { background: #b38b48; } .accent-danger { background: #63483c; } .accent-watering { background: #4d99ae; }
.tooltip-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.tooltip-title { color: #294d3b; font-size: 20px; font-weight: 850; }
.tooltip-subtitle { margin-top: 5px; color: #8a9a91; font-size: 11px; }
.tooltip-status { white-space: nowrap; font-size: 12px; font-weight: 800; }
.tooltip-normal { color: #5c9867; } .tooltip-warning { color: #aa823f; } .tooltip-danger { color: #694a3e; } .tooltip-watering { color: #438ea3; }
.tooltip-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 13px; margin-top: 18px; }
.tooltip-item { padding: 11px 12px; border-radius: 12px; background: #f5f8f5; }
.tooltip-item span { display: block; color: #8a9990; font-size: 11px; }
.tooltip-item strong { display: block; margin-top: 4px; color: #315746; font-size: 17px; }
.tooltip-extra { display: grid; grid-template-columns: 1fr 1fr; gap: 7px 12px; margin-top: 12px; padding: 12px; border-top: 1px solid #e7eee9; color: #8a9990; font-size: 11px; }
.tooltip-extra b { color: #456452; text-align: right; }
.tooltip-action { width: 100%; margin-top: 13px; padding: 11px 13px; display: flex; align-items: center; justify-content: center; gap: 8px; border: 0; border-radius: 12px; color: #fff; background: linear-gradient(135deg,#5d9e70,#3d7f59); font-size: 12px; font-weight: 800; cursor: pointer; box-shadow: 0 8px 20px rgba(55,112,78,.20); }
.tooltip-action:hover { filter: brightness(1.06); }
.tooltip-enter-active, .tooltip-leave-active { transition: opacity .16s ease, transform .16s ease; }
.tooltip-enter-from, .tooltip-leave-to { opacity: 0; transform: translateY(7px) scale(.98); }

.map-tip { position: absolute; z-index: 5; left: 50%; bottom: 15px; transform: translateX(-50%); padding: 8px 16px; border-radius: 999px; color: #fff; background: rgba(45,76,57,.58); backdrop-filter: blur(10px); font-size: 11px; white-space: nowrap; pointer-events: none; }
.empty-map { position: absolute; z-index: 4; inset: 0; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 8px; color: #4f6d59; background: rgba(231,241,226,.42); }
.empty-icon { font-size: 42px; opacity: .7; }
.empty-map strong { font-size: 18px; }
.empty-map span { font-size: 12px; color: #83958a; }

@media (max-width: 900px) {
  .map-header { padding: 12px 16px; align-items: flex-start; }
  .legend { gap: 10px; }
  .map-container { height: 540px; }
  .farm-name { font-size: 16px; }
  .farm-humidity { font-size: 25px; }
  .farm-status { font-size: 11px; }
}

@media (max-width: 640px) {
  .map-header { flex-direction: column; }
  .legend { width: 100%; justify-content: flex-start; }
  .map-container { height: 470px; }
  .map-tip { display: none; }
}
</style>
