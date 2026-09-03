<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: Object,
  metric: { type: String, default: 'moisture' },
  height: { type: Number, default: 270 },
  targetMin: Number,
  targetMax: Number,
})

const el = ref()
let chart

function render() {
  if (!el.value || !props.data) return
  chart ||= echarts.init(el.value)
  const moisture = props.metric === 'moisture'
  const times = Array.isArray(props.data.times) ? props.data.times : []
  const values = moisture ? props.data.soilHumidity || [] : props.data.temperature || []
  const color = moisture ? '#2f8b49' : '#ff820f'
  const areaColor = moisture ? '#70aa7238' : '#ffad5a38'
  const targetMin = props.targetMin ?? props.data.threshold
  const targetMax = props.targetMax
  const series = {
    name: moisture ? '土壤湿度' : '环境温度',
    type: 'line',
    data: values,
    smooth: true,
    connectNulls: false,
    symbol: 'circle',
    symbolSize: 7,
    lineStyle: { width: 2.5, color },
    itemStyle: { color, borderColor: '#fff', borderWidth: 1 },
    areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: areaColor }, { offset: 1, color: '#ffffff08' }]) },
  }
  if (moisture && targetMin != null) {
    const lines = [{ yAxis: targetMin, label: { show: false } }]
    if (targetMax != null) lines.push({ yAxis: targetMax, label: { show: false } })
    series.markLine = { silent: true, symbol: 'none', lineStyle: { type: 'dashed', color: '#5ca66d', width: 1.5 }, data: lines }
    if (targetMax != null) series.markArea = { silent: true, itemStyle: { color: '#7ab77b12' }, data: [[{ yAxis: targetMin }, { yAxis: targetMax }]] }
  }
  const eventSeries = moisture ? (props.data.events || [])
    .filter((event) => Number.isInteger(event.index) && times[event.index] !== undefined)
    .map((event) => ({
      name: event.type === 'alert' ? '告警事件' : '灌溉事件',
      type: 'scatter',
      symbol: 'circle',
      symbolSize: 10,
      data: [[times[event.index], 0]],
      itemStyle: { color: event.type === 'alert' ? '#f04c3a' : '#1697e8' },
      tooltip: { formatter: event.label || event.name },
    })) : []
  chart.setOption({
    animationDuration: 350,
    tooltip: { trigger: 'axis' },
    legend: { data: [series.name], top: 0, right: 6, itemWidth: 28, itemHeight: 10, textStyle: { color: '#606d67', fontSize: 12 } },
    grid: { left: 42, right: moisture && targetMax != null ? 72 : 26, top: 42, bottom: 38 },
    xAxis: { type: 'category', data: times, boundaryGap: false, axisLine: { lineStyle: { color: '#dce3de' } }, axisTick: { show: false }, axisLabel: { color: '#6d7973', fontSize: 11, hideOverlap: true } },
    yAxis: { type: 'value', min: moisture ? 0 : undefined, max: moisture ? 100 : undefined, splitNumber: 4, axisLabel: { color: '#6d7973', fontSize: 11 }, splitLine: { lineStyle: { color: '#edf1ee' } } },
    series: [series, ...eventSeries],
    graphic: moisture && targetMin != null ? [{ type: 'text', right: 8, top: 66, style: { text: targetMax != null ? `目标区间\n${targetMin}%~${targetMax}%` : `参考阈值\n${targetMin}%`, fill: '#4b9860', font: '12px sans-serif', lineHeight: 18 } }] : [],
  }, true)
}

function resize() { chart?.resize() }
onMounted(() => { render(); window.addEventListener('resize', resize) })
watch(() => [props.data, props.metric, props.targetMin, props.targetMax], render, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', resize); chart?.dispose() })
</script>

<template><div ref="el" class="chart" :style="{ height: `${height}px` }"></div></template>

<style scoped>.chart{width:100%}</style>
