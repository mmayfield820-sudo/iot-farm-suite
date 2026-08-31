<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getPlotTimeline } from '@/api/cultivation'
import { useFarmerStore } from '@/stores/farmer'
import { formatDateTime } from '@/utils/dataAdapters'

const store = useFarmerStore()
const items = ref([])
const loading = ref(false)
const hasMore = ref(true)
const viewport = ref(null)
const pageSize = 20
let requestVersion = 0
let refreshTimer

const itemClass = (item) => item.type === 'TASK' ? 'task-event' : 'support-event'
const typeLabel = computed(() => ({
  TASK: '农事任务',
  IRRIGATION: '灌溉',
  ALERT: '提醒',
  AUDIT: '配置变更',
}))

async function loadMore(reset = false) {
  const plotId = store.selectedPlotId
  if (!plotId || loading.value || (!reset && !hasMore.value)) return
  const version = reset ? ++requestVersion : requestVersion
  if (reset) {
    items.value = []
    hasMore.value = true
  }
  loading.value = true
  try {
    const rows = await getPlotTimeline(plotId, { limit: pageSize, offset: items.value.length })
    if (version !== requestVersion || plotId !== store.selectedPlotId) return
    const existing = new Set(items.value.map((item) => `${item.type}-${item.id}`))
    items.value.push(...rows.filter((item) => !existing.has(`${item.type}-${item.id}`)))
    hasMore.value = rows.length === pageSize
    if (reset) await nextTick()
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

async function refreshLatest() {
  const plotId = store.selectedPlotId
  if (!plotId || loading.value) return
  const rows = await getPlotTimeline(plotId, { limit: pageSize, offset: 0 })
  if (plotId !== store.selectedPlotId) return
  const latestKeys = new Set(rows.map((item) => `${item.type}-${item.id}`))
  items.value = [...rows, ...items.value.filter((item) => !latestKeys.has(`${item.type}-${item.id}`))]
}

function handleScroll(event) {
  const element = event.currentTarget
  if (element.scrollLeft + element.clientWidth >= element.scrollWidth - 160) loadMore()
}

watch(() => [store.selectedPlotId, store.timelineRevision], ([plotId]) => {
  requestVersion += 1
  loading.value = false
  if (!plotId) { items.value = []; hasMore.value = false; return }
  loadMore(true)
}, { immediate: true })

onMounted(() => {
  refreshTimer = window.setInterval(() => refreshLatest().catch(() => {}), 10000)
  window.addEventListener('focus', refreshLatest)
})
onBeforeUnmount(() => {
  window.clearInterval(refreshTimer)
  window.removeEventListener('focus', refreshLatest)
})
</script>

<template>
  <section class="timeline-panel">
    <span v-if="items.length" class="scroll-hint">向右滑动查看更多历史</span>
    <div v-if="items.length" ref="viewport" v-loading="loading && !items.length" class="timeline-viewport" @scroll.passive="handleScroll">
      <div class="timeline-track" :style="{ '--event-count': items.length }">
        <article v-for="item in items" :key="`${item.type}-${item.id}`" :class="['timeline-event', itemClass(item), `type-${item.type.toLowerCase()}`]">
          <span class="axis-dot"></span>
          <span class="event-stem"></span>
          <el-popover trigger="click" placement="top" :width="280" popper-class="timeline-event-popover">
            <template #reference>
              <button class="event-point" :aria-label="`查看${item.title}详情`"><i></i><span>{{ typeLabel[item.type] || '管理事件' }}</span></button>
            </template>
            <div class="event-detail">
              <span>{{ typeLabel[item.type] || '管理事件' }}</span>
              <strong>{{ item.title }}</strong>
              <p>{{ item.detail }}</p>
              <time>{{ formatDateTime(item.occurredAt) }}</time>
            </div>
          </el-popover>
          <time class="axis-time">{{ formatDateTime(item.occurredAt).slice(5, 16) }}</time>
        </article>
        <div class="timeline-tail"><span v-if="loading">加载中…</span><span v-else-if="hasMore">···</span><span v-else>—</span></div>
      </div>
    </div>
    <div v-else-if="loading" class="timeline-loading">正在读取管理记录…</div>
    <el-empty v-else description="暂无管理事件" :image-size="54" />
  </section>
</template>

<style scoped>
.timeline-panel{position:relative;margin:0 0 12px;padding:0;background:transparent}.scroll-hint{position:absolute;top:1px;right:10px;z-index:3;color:rgba(125,91,70,.52);font-size:10px;letter-spacing:.03em}.timeline-viewport{overflow-x:auto;overflow-y:hidden;overscroll-behavior-inline:contain;scrollbar-width:thin;scrollbar-color:rgba(190,119,67,.2) transparent}.timeline-viewport::-webkit-scrollbar{height:4px}.timeline-viewport::-webkit-scrollbar-track{background:transparent}.timeline-viewport::-webkit-scrollbar-thumb{border-radius:10px;background:rgba(190,119,67,.2)}.timeline-track{--item-width:154px;width:max-content;min-width:100%;height:152px;position:relative;display:grid;grid-template-columns:repeat(var(--event-count),var(--item-width)) 80px;padding:0 16px}.timeline-track::before{height:1px;position:absolute;top:76px;left:16px;right:16px;content:'';background:repeating-linear-gradient(90deg,rgba(181,111,60,.34) 0 4px,transparent 4px 9px)}.timeline-event{height:152px;position:relative}.axis-dot{width:7px;height:7px;position:absolute;top:73px;left:50%;z-index:2;border:2px solid rgba(255,250,245,.9);border-radius:50%;background:rgba(190,103,46,.68);transform:translateX(-50%);box-shadow:0 0 0 1px rgba(171,96,45,.2)}.event-stem{width:1px;height:35px;position:absolute;left:50%;background:linear-gradient(rgba(190,103,46,.18),rgba(190,103,46,.62));transform:translateX(-50%)}.task-event .event-stem{top:41px}.support-event .event-stem{top:76px;background:linear-gradient(rgba(58,137,103,.62),rgba(58,137,103,.18))}.event-point{position:absolute;left:50%;display:flex;align-items:center;gap:5px;padding:2px 5px;border:0;color:rgba(113,72,46,.64);background:transparent;font:inherit;font-size:9px;white-space:nowrap;cursor:pointer;transform:translateX(-50%)}.task-event .event-point{top:24px}.support-event .event-point{top:108px}.event-point i{width:11px;height:11px;border:3px solid rgba(255,248,241,.92);border-radius:50%;background:rgba(218,103,31,.82);box-shadow:0 0 0 1px rgba(187,97,42,.22);transition:.2s}.type-irrigation .event-point i{background:rgba(61,137,214,.84);box-shadow:0 0 0 1px rgba(61,137,214,.24)}.type-alert .event-point i{background:rgba(213,76,76,.84);box-shadow:0 0 0 1px rgba(213,76,76,.24)}.type-audit .event-point i{background:rgba(54,139,101,.82);box-shadow:0 0 0 1px rgba(54,139,101,.22)}.event-point:hover i,.event-point:focus-visible i{transform:scale(1.25);box-shadow:0 0 0 4px rgba(218,103,31,.1)}.axis-time{position:absolute;top:61px;left:calc(50% + 9px);color:rgba(116,80,57,.5);font-size:8px;white-space:nowrap}.timeline-tail{height:152px;display:grid;place-items:center;color:rgba(125,91,70,.42);font-size:11px}.timeline-loading{height:110px;display:grid;place-items:center;color:rgba(125,91,70,.55);font-size:12px}.event-detail{display:flex;flex-direction:column;gap:6px}.event-detail>span{color:#b45c22;font-size:11px;letter-spacing:.06em}.event-detail strong{color:#4b2815;font-size:15px}.event-detail p{margin:0;color:#7d6252;font-size:12px;line-height:1.6}.event-detail time{padding-top:5px;border-top:1px solid #f0e3d9;color:#a08473;font-size:11px}@media(max-width:760px){.timeline-track{--item-width:132px}.scroll-hint{right:4px}}
</style>
