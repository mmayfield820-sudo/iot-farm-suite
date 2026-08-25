<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
const props = defineProps({ data: Object, height: { type: Number, default: 310 } })
const el = ref(); let chart
function render() {
  if (!el.value || !props.data) return
  chart ||= echarts.init(el.value)
  const times = Array.isArray(props.data.times) ? props.data.times : []
  const temperature = Array.isArray(props.data.temperature) ? props.data.temperature : []
  const soilHumidity = Array.isArray(props.data.soilHumidity) ? props.data.soilHumidity : []
  const moistureSeries = { name:'土壤湿度', type:'line', smooth:true, yAxisIndex:1, data:soilHumidity, symbolSize:7, connectNulls:false, lineStyle:{width:3,color:'#3c9b74'}, itemStyle:{color:'#3c9b74'} }
  if (props.data.threshold != null) moistureSeries.markLine = { silent:true, symbol:'none', label:{formatter:`阈值 ${props.data.threshold}%`,color:'#c67b30',position:'middle'}, lineStyle:{type:'dashed',color:'#e49b4d'}, data:[{yAxis:props.data.threshold}] }
  const events = (props.data.events || []).filter((event) => Number.isInteger(event.index) && times[event.index] !== undefined && soilHumidity[event.index] !== undefined)
  if (events.length) moistureSeries.markPoint = { symbol:'pin', symbolSize:40, itemStyle:{color:'#2879a8'}, label:{formatter:'灌'}, data:events.map((event) => ({ name:event.label, coord:[times[event.index], soilHumidity[event.index]] })) }
  chart.setOption({ tooltip:{trigger:'axis'}, legend:{data:['环境温度','土壤湿度'],top:10,right:6,textStyle:{color:'#71807b'}}, grid:{left:42,right:42,top:72,bottom:28}, xAxis:{type:'category',data:times,boundaryGap:false,axisLine:{lineStyle:{color:'#dce8e3'}}}, yAxis:[{type:'value',name:'℃',splitLine:{lineStyle:{color:'#eef3f1'}}},{type:'value',name:'%',min:0,max:100,splitLine:{show:false}}], series:[{name:'环境温度',type:'line',smooth:true,data:temperature,symbolSize:7,connectNulls:false,lineStyle:{width:3,color:'#e49b4d'},itemStyle:{color:'#e49b4d'},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#f4bc7544'},{offset:1,color:'#fff0'}])}},moistureSeries] }, true)
}
function resize(){chart?.resize()} onMounted(()=>{render();window.addEventListener('resize',resize)}); watch(()=>props.data,render,{deep:true}); onBeforeUnmount(()=>{window.removeEventListener('resize',resize);chart?.dispose()})
</script>
<template><div ref="el" class="chart" :style="{ height: `${height}px` }"></div></template>
<style scoped>.chart{width:100%}</style>
