<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'
import { sendChatMessage } from '@/api/chat'

const store = useFarmerStore()
const router = useRouter()
const input = ref('')
const sending = ref(false)
const chat = ref()
const sessionId = `WEB${Date.now()}`
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const messages = ref([{ id: 1, role: 'assistant', text: '你好，我可以结合你有权访问的地块数据、灌溉记录和天气信息提供建议。请选择地块后开始提问。', evidence: [] }])
const plot = computed(() => store.currentPlot)
const quick = ['现在需要浇水吗？', '为什么产生湿度告警？', '未来天气适合灌溉吗？', '分析最近灌溉效果']

async function ask(text = input.value) {
  const question = text.trim()
  if (!question || sending.value) return
  if (!plot.value) {
    messages.value.push({ id: Date.now(), role: 'assistant', text: '当前账号没有可访问的地块，无法读取农情数据。请联系管理员检查地块授权。', evidence: [] })
    return
  }
  messages.value.push({ id: Date.now(), role: 'user', text: question })
  input.value = ''
  sending.value = true
  await nextTick()
  chat.value?.scrollTo({ top: chat.value.scrollHeight, behavior: 'smooth' })
  try {
    if (isMock) {
      messages.value.push({ id: Date.now() + 1, role: 'assistant', text: `${plot.value.plotName} 当前温度 ${plot.value.temperature}℃、土壤湿度 ${plot.value.humidity}%。`, evidence: [`湿度阈值 ${plot.value.threshold}%`] })
    } else {
      const response = await sendChatMessage(sessionId, { message: question, plotId: plot.value.plotId })
      const body = response?.data || response
      messages.value.push({ id: Date.now() + 1, role: 'assistant', text: body.answer || '智能体暂未返回有效内容。', evidence: body.sources || [] })
    }
  } catch (error) {
    messages.value.push({ id: Date.now() + 1, role: 'assistant', text: error.message || '智能体服务暂时不可用，请稍后重试。', evidence: [] })
  } finally {
    sending.value = false
    await nextTick()
    chat.value?.scrollTo({ top: chat.value.scrollHeight, behavior: 'smooth' })
  }
}
</script>
<template><div class="farmer-page"><div class="page-head"><div><h1 class="page-title">智能农业助手</h1><p class="page-subtitle">建议依据清晰可核验，高风险控制不会仅凭自然语言直接执行。</p></div><div class="page-actions"><span :class="['status-pill',store.serviceStatus.assistant?'':'danger']">智能体服务{{store.serviceStatus.assistant?'正常':'不可用'}}</span><div class="filter-control plot-filter"><span class="filter-label"><el-icon><Location /></el-icon> 当前地块</span><el-select class="plot-select" size="large" :model-value="store.selectedPlotId" @change="store.selectPlot"><el-option v-for="item in store.accessiblePlots" :key="item.plotId" :label="`${item.farmName} · ${item.plotName}`" :value="item.plotId"/></el-select></div></div></div><section class="assistant-layout"><aside class="content-panel context-panel"><div class="section-head"><div><h3>当前分析上下文</h3><p>仅使用账号有权访问的数据</p></div></div><div class="context-plot"><strong>{{plot?.plotName}}</strong><small>{{plot?.cropName}} · {{plot?.location}}</small></div><dl><div><dt>土壤湿度</dt><dd :class="{danger:plot?.humidity<plot?.threshold}">{{plot?.humidity}}%</dd></div><div><dt>湿度阈值</dt><dd>{{plot?.threshold}}%</dd></div><div><dt>环境温度</dt><dd>{{plot?.temperature}}℃</dd></div><div><dt>设备状态</dt><dd>{{plot?.deviceOnline?'在线':'离线'}}</dd></div><div><dt>天气服务</dt><dd>{{store.serviceStatus.weather?'可用':'不可用'}}</dd></div></dl><div class="quick-title">快捷提问</div><button v-for="item in quick" :key="item" class="quick-question" @click="ask(item)">{{item}}<el-icon><ArrowRight /></el-icon></button></aside><main class="content-panel chat-panel"><div ref="chat" class="messages"><div v-for="item in messages" :key="item.id" :class="['message',item.role]"><div class="message-avatar"><el-icon><User v-if="item.role==='user'"/><MagicStick v-else/></el-icon></div><div class="bubble"><p>{{item.text}}</p><div v-if="item.evidence?.length" class="answer-evidence"><strong>建议依据</strong><span v-for="evidence in item.evidence" :key="evidence"><el-icon><CircleCheck /></el-icon>{{evidence}}</span></div><el-button v-if="item.action" type="success" size="small" @click="router.push('/farmer/irrigation')">前往灌溉页面二次确认</el-button></div></div><div v-if="sending" class="message assistant"><div class="message-avatar"><el-icon><MagicStick/></el-icon></div><div class="bubble typing">正在分析农田数据<span>...</span></div></div></div><div class="composer"><el-input v-model="input" type="textarea" :rows="2" resize="none" placeholder="询问灌溉、天气、告警或农事问题…" @keydown.enter.exact.prevent="ask()"/><el-button type="success" :loading="sending" @click="ask()"><el-icon><Promotion /></el-icon>发送</el-button><small>AI 建议仅供辅助决策，设备控制必须由用户确认。</small></div></main></section></div></template>
<style scoped>.assistant-layout{display:grid;grid-template-columns:300px minmax(0,1fr);gap:18px;height:calc(100vh - 165px);min-height:570px}.context-panel{overflow:auto}.context-plot{padding:14px;border-radius:12px;background:#eef7f2}.context-plot strong,.context-plot small{display:block}.context-plot small{margin-top:5px;color:#7b8c85;font-size:11px}.context-panel dl{margin:15px 0}.context-panel dl div{display:flex;justify-content:space-between;padding:9px 2px;border-bottom:1px solid #edf2ef}.context-panel dt{color:#81918b;font-size:12px}.context-panel dd{margin:0;color:#29473d;font-size:13px;font-weight:650}.context-panel dd.danger{color:#c45353}.quick-title{margin:18px 0 8px;color:#50675e;font-size:12px;font-weight:700}.quick-question{width:100%;display:flex;justify-content:space-between;align-items:center;padding:10px 2px;border:0;border-bottom:1px solid #edf2ef;color:#5d7169;background:transparent;text-align:left;font-size:12px;cursor:pointer}.quick-question:hover{color:#27835d}.chat-panel{display:flex;flex-direction:column;padding:0;overflow:hidden}.messages{min-height:0;flex:1;padding:22px;overflow-y:auto;background:#fbfdfc}.message{display:flex;align-items:flex-start;gap:10px;margin-bottom:18px}.message.user{flex-direction:row-reverse}.message-avatar{width:34px;height:34px;display:grid;place-items:center;flex:0 0 34px;border-radius:11px;color:#277e5b;background:#e3f3eb}.message.user .message-avatar{color:white;background:#3b8c6a}.bubble{max-width:74%;padding:12px 14px;border:1px solid var(--line);border-radius:4px 14px 14px;background:#fff;color:#3d574e}.message.user .bubble{border:0;border-radius:14px 4px 14px 14px;color:white;background:#398363}.bubble p{margin:0;font-size:13px;line-height:1.75}.answer-evidence{display:grid;gap:6px;margin-top:12px;padding-top:11px;border-top:1px solid #e7efeb}.answer-evidence strong{font-size:11px}.answer-evidence span{display:flex;align-items:center;gap:6px;color:#74867f;font-size:11px}.answer-evidence .el-icon{color:#2f9368}.bubble>.el-button{margin-top:12px}.typing{color:#7b8c85;font-size:12px}.composer{display:grid;grid-template-columns:1fr auto;gap:10px;padding:16px;border-top:1px solid var(--line);background:#fff}.composer .el-button{height:54px}.composer small{grid-column:1/-1;color:#98a49f;font-size:10px}@media(max-width:900px){.assistant-layout{grid-template-columns:1fr;height:auto}.context-panel{max-height:none}.chat-panel{height:650px}}@media(max-width:560px){.messages{padding:14px}.bubble{max-width:86%}.composer{grid-template-columns:1fr}.composer .el-button{height:40px}}
</style>
