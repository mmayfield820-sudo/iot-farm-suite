<script setup>
import { computed, ref, watch } from 'vue'
import { getPlotPlanting } from '@/api/cultivation'
import { getPlotTasks } from '@/api/farmTask'
import { getPlanChangeRequests } from '@/api/planChangeRequest'

const props=defineProps({plotId:{type:String,default:''}});const planting=ref(null);const tasks=ref([]);const requests=ref([]);const today=new Date().toLocaleDateString('sv-SE');const futureEnd=new Date(Date.now()+7*86400000).toLocaleDateString('sv-SE')
watch(()=>props.plotId,async(id)=>{if(!id){planting.value=null;tasks.value=[];requests.value=[];return}[planting.value,tasks.value,requests.value]=await Promise.all([getPlotPlanting(id),getPlotTasks(id),getPlanChangeRequests({plotId:id})])},{immediate:true})
const pending=computed(()=>tasks.value.filter(x=>['PENDING','OVERDUE'].includes(x.taskStatus)));const todayCount=computed(()=>pending.value.filter(x=>x.plannedDate===today).length);const overdue=computed(()=>pending.value.filter(x=>x.plannedDate&&x.plannedDate<today).length);const upcoming=computed(()=>pending.value.filter(x=>x.plannedDate>today&&x.plannedDate<=futureEnd).length);const reminders=computed(()=>requests.value.filter(x=>x.status==='PENDING_REVIEW').length)
</script>
<template><section class="phase2-summary"><article><small>当前阶段</small><strong>{{planting?.currentStage?.stageName||'尚未配置'}}</strong><span>{{planting?.varietyName||'请先绑定种植模板'}}</span></article><article><small>今日待办</small><strong>{{todayCount}}</strong><span>项待完成任务</span></article><article><small>逾期任务</small><strong>{{overdue}}</strong><span>项需要关注</span></article><article><small>未来 7 天</small><strong>{{upcoming}}</strong><span>项计划任务</span></article><article><small>计划调整</small><strong>{{reminders}}</strong><router-link to="/farmer/alarm">查看提醒</router-link></article></section></template>
<style scoped>.phase2-summary{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:18px 0}.phase2-summary article{padding:16px;border:1px solid #eedccc;border-radius:14px;background:#fffdfa}.phase2-summary small,.phase2-summary span,.phase2-summary a{display:block;color:#887568;font-size:12px}.phase2-summary strong{display:block;margin:8px 0;color:#7a3a12;font-size:22px}.phase2-summary a{color:#c35f1b}@media(max-width:1000px){.phase2-summary{grid-template-columns:repeat(2,1fr)}}@media(max-width:520px){.phase2-summary{grid-template-columns:1fr}}</style>
