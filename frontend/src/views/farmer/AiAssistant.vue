<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { getChatHealth, sendChatMessage } from '@/api/chat'
import { useFarmerStore } from '@/stores/farmer'

const store = useFarmerStore()
const router = useRouter()
const input = ref('')
const sending = ref(false)
const listening = ref(false)
const speechSupported = ref(false)
const recognition = ref(null)
const chat = ref(null)
const sessionId = `WEB${Date.now()}`
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const plot = computed(() => store.currentPlot)
const messages = ref([{ id: 1, role: 'assistant', text: '你好呀，我是小橙子。你可以问我灌溉、设备、告警和农事问题，我会结合当前地块的数据给出建议。', evidence: [] }])
const quickQuestions = ['现在需要浇水吗？', '为什么产生湿度告警？', '设备状态是否适合灌溉？', '分析最近灌溉效果']

function readableAnswer(value) {
  return String(value || '').replace(/<think>[\s\S]*?<\/think>/gi, '').replace(/<\|[^>]*\|>/g, '').replace(/```(?:\w+)?\s*/g, '').replace(/```/g, '').trim()
}

async function refreshStatus() {
  if (isMock) { store.serviceStatus.assistant = true; return }
  try {
    const response = await getChatHealth()
    const body = response?.data || response || {}
    store.serviceStatus.assistant = body.available !== false && body.modelEnabled !== false
  } catch { store.serviceStatus.assistant = false }
}

async function ask(question = input.value) {
  const text = question.trim()
  if (!text || sending.value) return
  if (!plot.value) return ElMessage.warning('当前账号没有可访问的地块')
  messages.value.push({ id: Date.now(), role: 'user', text })
  input.value = ''
  sending.value = true
  await nextTick()
  chat.value?.scrollTo({ top: chat.value.scrollHeight, behavior: 'smooth' })
  try {
    if (isMock) {
      messages.value.push({ id: Date.now() + 1, role: 'assistant', text: `${plot.value.plotName} 当前土壤湿度为 ${plot.value.humidity}% ，阈值为 ${plot.value.threshold}%。请结合天气和设备状态确认灌溉安排。`, evidence: [`湿度阈值 ${plot.value.threshold}%`] })
    } else {
      const response = await sendChatMessage(sessionId, { message: text, plotId: plot.value.plotId })
      const body = response?.data || response || {}
      messages.value.push({ id: Date.now() + 1, role: 'assistant', text: readableAnswer(body.answer) || '小橙子暂时没有得到有效结果，请换一种说法再试一次。', evidence: body.sources || [] })
      store.serviceStatus.assistant = true
    }
  } catch (error) {
    await refreshStatus()
    messages.value.push({ id: Date.now() + 1, role: 'assistant', text: error?.response?.data?.message || error.message || '智能服务暂时不可用，请稍后重试。', evidence: [] })
  } finally {
    sending.value = false
    await nextTick()
    chat.value?.scrollTo({ top: chat.value.scrollHeight, behavior: 'smooth' })
  }
}

function toggleVoice() {
  if (!speechSupported.value) return ElMessage.info('当前浏览器不支持语音识别，可继续使用文字输入')
  if (listening.value) recognition.value?.stop()
  else recognition.value?.start()
}

function initSpeech() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) return
  speechSupported.value = true
  const engine = new SpeechRecognition()
  engine.lang = 'zh-CN'
  engine.interimResults = false
  engine.onstart = () => { listening.value = true }
  engine.onresult = (event) => { input.value = event.results[0][0].transcript.trim() }
  engine.onerror = () => { listening.value = false; ElMessage.warning('小橙子没有听清，请再说一次') }
  engine.onend = () => { listening.value = false }
  recognition.value = engine
}

function focusComposer() { document.querySelector('.assistant-composer textarea')?.focus() }
onMounted(() => { refreshStatus(); initSpeech(); window.addEventListener('orchard-assistant-focus', focusComposer) })
onBeforeUnmount(() => { recognition.value?.abort(); window.removeEventListener('orchard-assistant-focus', focusComposer) })
</script>

<template>
  <div class="farmer-page assistant-page">
    <div class="page-head assistant-head"><div><span class="assistant-eyebrow">FARM COMPANION</span><h1 class="page-title">小橙子 · 农事助手</h1><p class="page-subtitle">把问题直接告诉小橙子，建议依据仍来自你有权访问的真实地块数据。</p></div><span :class="['status-pill', store.serviceStatus.assistant ? '' : 'danger']">智能服务{{ store.serviceStatus.assistant ? '正常' : '不可用' }}</span></div>
    <section class="assistant-grid">
      <main class="content-panel chat-panel"><div ref="chat" class="messages"><div v-for="item in messages" :key="item.id" :class="['message', item.role]"><div v-if="item.role === 'assistant'" class="mini-orange"><i></i><b></b></div><div v-else class="message-avatar">我</div><div class="bubble"><p>{{ item.text }}</p><div v-if="item.evidence?.length" class="answer-evidence"><span v-for="evidence in item.evidence" :key="evidence">{{ evidence }}</span></div></div></div><div v-if="sending" class="message assistant"><div class="mini-orange thinking"><i></i><b></b></div><div class="bubble typing">小橙子正在结合地块数据分析...</div></div></div><div class="assistant-composer"><el-input v-model="input" type="textarea" :rows="2" resize="none" placeholder="询问灌溉、设备、告警或农事问题..." @keydown.enter.exact.prevent="ask()" /><div class="composer-actions"><button type="button" :class="['voice-button', { listening }]" @click="toggleVoice">{{ listening ? '正在聆听' : '语音提问' }}</button><el-button type="success" :loading="sending" @click="ask()">发送</el-button></div></div></main>
      <aside class="assistant-side"><section class="content-panel mascot-card"><div :class="['big-orange', { thinking: sending, listening }]" aria-hidden="true"><i class="leaf"></i><i class="eye left"></i><i class="eye right"></i><i class="mouth"></i><i class="cheek left"></i><i class="cheek right"></i></div><strong>{{ sending ? '我正在分析呢...' : listening ? '我在听呢...' : '你好呀，我是小橙子' }}</strong><p>直接告诉我果园里的问题。</p><button class="talk-button" type="button" @click="toggleVoice">{{ listening ? '结束说话' : '开始说话' }}</button></section><section class="content-panel context-card"><div class="section-head"><div><h3>当前分析上下文</h3><p>仅使用授权数据</p></div></div><strong>{{ plot?.plotName || '暂无地块' }}</strong><small>{{ plot?.farmName || '未命名农场' }}</small><dl><div><dt>土壤湿度</dt><dd :class="{ danger: plot?.humidity < plot?.threshold }">{{ plot?.humidity ?? '-' }}%</dd></div><div><dt>湿度阈值</dt><dd>{{ plot?.threshold ?? '-' }}%</dd></div><div><dt>环境温度</dt><dd>{{ plot?.temperature ?? '-' }}℃</dd></div><div><dt>设备状态</dt><dd>{{ plot?.deviceOnline ? '在线' : '离线' }}</dd></div></dl></section><section class="content-panel quick-card"><div class="section-head"><div><h3>可以这样问我</h3></div></div><button v-for="question in quickQuestions" :key="question" class="quick-question" type="button" @click="ask(question)">{{ question }}</button><button class="irrigation-link" type="button" @click="router.push('/farmer/irrigation')">前往智慧灌溉</button></section></aside>
    </section>
  </div>
</template>

<style scoped>
.assistant-head{align-items:flex-end;margin-bottom:18px}.assistant-eyebrow{display:block;margin-bottom:7px;color:#5d9b70;font-size:10px;font-weight:800;letter-spacing:2px}.assistant-grid{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:18px;min-height:calc(100vh - 190px)}.chat-panel{display:flex;flex-direction:column;min-height:0;padding:0;overflow:hidden;background:rgba(255,255,255,.75)}.messages{min-height:480px;flex:1;padding:24px;overflow-y:auto}.message{display:flex;align-items:flex-start;gap:11px;margin-bottom:18px}.message.user{flex-direction:row-reverse}.mini-orange{position:relative;width:38px;height:38px;flex:0 0 38px;border-radius:48% 52% 50% 50%;background:#f0a43b;box-shadow:inset -3px -4px 0 rgba(139,77,24,.12)}.mini-orange i{position:absolute;right:2px;top:-4px;width:14px;height:7px;border-radius:100% 0 100% 0;background:#71a85b;transform:rotate(-24deg)}.mini-orange b{position:absolute;left:14px;top:23px;width:10px;height:5px;border-bottom:2px solid #543c2d;border-radius:0 0 50% 50%}.mini-orange.thinking,.big-orange.thinking{animation:breathe 1.1s ease-in-out infinite}.message-avatar{width:34px;height:34px;display:grid;place-items:center;flex:0 0 34px;border-radius:50%;color:#fff;background:#3b8b5e;font-size:11px}.bubble{max-width:76%;padding:13px 15px;border:1px solid #dbe7df;border-radius:6px 16px 16px;color:#385249;background:#fff}.message.user .bubble{border:0;border-radius:16px 6px 16px 16px;color:#fff;background:#3b8b5e}.bubble p{margin:0;white-space:pre-line;font-size:13px;line-height:1.75}.answer-evidence{display:grid;gap:5px;margin-top:10px;padding-top:9px;border-top:1px solid #e6eeea}.answer-evidence span{color:#6d8378;font-size:11px}.typing{color:#71857c;font-size:12px}.assistant-composer{padding:15px;border-top:1px solid #dfe9e3;background:rgba(255,255,255,.9)}.composer-actions{display:flex;justify-content:space-between;align-items:center;margin-top:9px}.voice-button,.talk-button{height:34px;padding:0 12px;border:1px solid #b9d8c7;border-radius:8px;color:#287e5b;background:#f2f9f5;cursor:pointer;font-size:12px}.voice-button.listening,.talk-button:hover{color:#fff;border-color:#2d9468;background:#2d9468}.assistant-side{display:grid;align-content:start;gap:18px}.mascot-card{text-align:center}.big-orange{position:relative;width:132px;height:132px;margin:2px auto 14px;border-radius:48% 52% 49% 51%;background:#f0a43b;box-shadow:inset -10px -12px 0 rgba(139,77,24,.12),0 15px 28px rgba(89,93,52,.12);transition:.2s}.big-orange.listening{transform:translateY(-3px) scale(1.03)}.big-orange .leaf{position:absolute;right:11px;top:-12px;width:37px;height:16px;border:1px solid #396c4b;border-radius:100% 0 100% 0;background:#71a85b;transform:rotate(-24deg)}.big-orange .eye{position:absolute;top:52px;width:10px;height:14px;border-radius:50%;background:#543c2d}.big-orange .eye.left{left:38px}.big-orange .eye.right{right:38px}.big-orange .mouth{position:absolute;left:56px;top:72px;width:25px;height:14px;border-bottom:4px solid #543c2d;border-radius:0 0 50% 50%}.big-orange .cheek{position:absolute;top:76px;width:16px;height:9px;border-radius:50%;background:rgba(181,65,47,.25)}.big-orange .cheek.left{left:21px}.big-orange .cheek.right{right:21px}.mascot-card>strong{display:block;color:#29473d;font-size:16px}.mascot-card>p{margin:6px 0 14px;color:#788f84;font-size:11px}.context-card>strong,.context-card>small{display:block}.context-card>strong{color:#29473d}.context-card>small{margin-top:5px;color:#81958c;font-size:11px}.context-card dl{margin:13px 0 0}.context-card dl div{display:flex;justify-content:space-between;padding:8px 2px;border-bottom:1px solid #e6eeea}.context-card dt{color:#81918b;font-size:11px}.context-card dd{margin:0;color:#29473d;font-size:12px;font-weight:650}.context-card dd.danger{color:#c45353}.quick-card .section-head{margin-bottom:7px}.quick-question{width:100%;padding:9px 2px;border:0;border-bottom:1px solid #e6eeea;color:#506b5f;background:transparent;text-align:left;font-size:11px;cursor:pointer}.quick-question:hover,.irrigation-link:hover{color:#287e5b}.irrigation-link{margin-top:14px;padding:0;border:0;color:#3b8b5e;background:transparent;font-size:11px;cursor:pointer}@keyframes breathe{50%{transform:translateY(-3px) rotate(-2deg) scale(1.02)}}@media(max-width:1100px){.assistant-grid{grid-template-columns:1fr}.assistant-side{grid-template-columns:1fr 1fr}.quick-card{grid-column:1/-1}}@media(max-width:700px){.assistant-head{align-items:flex-start;flex-direction:column}.messages{min-height:400px;padding:16px}.assistant-side{grid-template-columns:1fr}.quick-card{grid-column:auto}.bubble{max-width:88%}}
</style>
