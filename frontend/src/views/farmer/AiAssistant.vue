<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useFarmerStore } from '@/stores/farmer'
import { getChatHealth, sendChatMessage } from '@/api/chat'

const store = useFarmerStore()
const router = useRouter()
const input = ref('')
const sending = ref(false)
const listening = ref(false)
const speechSupported = ref(false)
const recognition = ref(null)
const transcript = ref('')
const chat = ref()
const sessionId = `WEB${Date.now()}`
const isMock = import.meta.env.VITE_USE_MOCK === 'true'
const messages = ref([{ id: 1, role: 'assistant', text: '你好呀，我是小橙子。你可以直接问我灌溉、设备、告警和农事问题，我会结合当前地块的数据给出清楚、可核验的建议。', evidence: [] }])
const plot = computed(() => store.currentPlot)
const quick = ['现在需要浇水吗？', '为什么产生湿度告警？', '设备状态是否适合灌溉？', '分析最近灌溉效果']

function readableAnswer(value) {
  return String(value || '')
    .replace(/<think>[\s\S]*?<\/think>/gi, '')
    .replace(/<\|[^>]*\|>/g, '')
    .replace(/\[\/?(?:INST|SYSTEM|ASSISTANT|USER)\]/gi, '')
    .replace(/^\s*(?:assistant|analysis|final)\s*[:：]\s*/i, '')
    .replace(/```(?:\w+)?\s*/g, '')
    .replace(/```/g, '')
    .replace(/【\d+†[^】]+】/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

async function refreshAssistantStatus() {
  if (isMock) {
    store.serviceStatus.assistant = true
    return true
  }
  try {
    const response = await getChatHealth()
    const body = response?.data || response
    store.serviceStatus.assistant = body.available === true && body.modelEnabled === true
    return store.serviceStatus.assistant
  } catch {
    store.serviceStatus.assistant = false
    return false
  }
}

async function ask(text = input.value) {
  const question = text.trim()
  if (!question || sending.value) return
  if (!plot.value) {
    messages.value.push({ id: Date.now(), role: 'assistant', text: '当前账号没有可访问的地块，无法读取农情数据。请联系管理员检查地块授权。', evidence: [] })
    return
  }
  messages.value.push({ id: Date.now(), role: 'user', text: question })
  input.value = ''
  transcript.value = ''
  sending.value = true
  await nextTick()
  chat.value?.scrollTo({ top: chat.value.scrollHeight, behavior: 'smooth' })
  try {
    if (isMock) {
      messages.value.push({ id: Date.now() + 1, role: 'assistant', text: `${plot.value.plotName} 当前温度 ${plot.value.temperature}℃、土壤湿度 ${plot.value.humidity}%。`, evidence: [`湿度阈值 ${plot.value.threshold}%`] })
    } else {
      const response = await sendChatMessage(sessionId, { message: question, plotId: plot.value.plotId })
      const body = response?.data || response
      messages.value.push({ id: Date.now() + 1, role: 'assistant', text: readableAnswer(body.answer) || '小橙子暂时没有得到有效结果，请换一种说法再试一次。', evidence: body.sources || [] })
      store.serviceStatus.assistant = true
    }
  } catch (error) {
    await refreshAssistantStatus()
    messages.value.push({ id: Date.now() + 1, role: 'assistant', text: error?.response?.data?.message || error.message || '智能服务暂时不可用，请稍后重试。', evidence: [] })
  } finally {
    sending.value = false
    await nextTick()
    chat.value?.scrollTo({ top: chat.value.scrollHeight, behavior: 'smooth' })
  }
}

function initSpeech() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) return
  speechSupported.value = true
  const engine = new SpeechRecognition()
  engine.lang = 'zh-CN'
  engine.continuous = false
  engine.interimResults = true
  engine.onstart = () => { listening.value = true; transcript.value = '' }
  engine.onresult = (event) => {
    let text = ''
    for (let index = event.resultIndex; index < event.results.length; index += 1) text += event.results[index][0].transcript
    transcript.value = text.trim()
    input.value = transcript.value
  }
  engine.onerror = () => { listening.value = false; ElMessage.warning('小橙子没有听清，请再说一次') }
  engine.onend = () => {
    listening.value = false
    const text = transcript.value.trim()
    if (text) ask(text)
  }
  recognition.value = engine
}

function toggleVoice() {
  if (sending.value) return
  if (!speechSupported.value) return ElMessage.info('当前浏览器不支持语音识别，可以继续使用文字输入')
  if (listening.value) recognition.value?.stop()
  else { input.value = ''; transcript.value = ''; recognition.value?.start() }
}

function handleAssistantVoiceToggle() { toggleVoice() }
onMounted(() => {
  refreshAssistantStatus()
  initSpeech()
  window.addEventListener('orchard-assistant-toggle-voice', handleAssistantVoiceToggle)
})
onBeforeUnmount(() => {
  recognition.value?.abort()
  window.removeEventListener('orchard-assistant-toggle-voice', handleAssistantVoiceToggle)
})
</script>

<template>
  <div class="farmer-page assistant-page">
    <div class="page-head assistant-head">
      <div>
        <span class="assistant-eyebrow">ORCHARD COMPANION</span>
        <h1 class="page-title">小橙子 · 农事助手</h1>
        <p class="page-subtitle">把问题直接告诉小橙子，建议依据仍来自你有权访问的真实地块数据。</p>
      </div>
      <div class="page-actions">
        <span :class="['status-pill', store.serviceStatus.assistant ? '' : 'danger']">智能体服务{{ store.serviceStatus.assistant ? '正常' : '不可用' }}</span>
        <div class="filter-control plot-filter">
          <span class="filter-label"><el-icon><Location /></el-icon> 当前地块</span>
          <el-select class="plot-select" size="large" :model-value="store.selectedPlotId" @change="store.selectPlot">
            <el-option v-for="item in store.accessiblePlots" :key="item.plotId" :label="`${item.farmName} · ${item.plotName}`" :value="item.plotId" />
          </el-select>
        </div>
      </div>
    </div>

    <section class="assistant-grid">
      <main class="content-panel chat-panel">
        <div ref="chat" class="messages">
          <div v-for="item in messages" :key="item.id" :class="['message', item.role]">
            <div v-if="item.role === 'assistant'" class="message-mascot" aria-hidden="true">
              <div class="orange-character"><span class="leaf"></span><span class="eye eye-l"></span><span class="eye eye-r"></span><span class="mouth"></span><span class="cheek cheek-l"></span><span class="cheek cheek-r"></span></div>
            </div>
            <div v-else class="message-avatar">我</div>
            <div class="bubble">
              <p>{{ item.text }}</p>
              <div v-if="item.evidence?.length" class="answer-evidence">
                <strong>本次建议依据</strong>
                <span v-for="evidence in item.evidence" :key="evidence"><el-icon><CircleCheck /></el-icon>{{ evidence }}</span>
              </div>
            </div>
          </div>
          <div v-if="sending" class="message assistant">
            <div class="message-mascot"><div class="orange-character thinking"><span class="leaf"></span><span class="eye eye-l"></span><span class="eye eye-r"></span><span class="mouth"></span></div></div>
            <div class="bubble typing">小橙子正在结合地块数据想一想……</div>
          </div>
        </div>
        <div class="composer">
          <div class="composer-box">
            <el-input v-model="input" type="textarea" :rows="2" resize="none" placeholder="询问灌溉、设备、告警或农事问题……" @keydown.enter.exact.prevent="ask()" />
            <button class="voice-trigger" :class="{ listening }" :disabled="sending" type="button" @click="toggleVoice"><span>●</span>{{ listening ? '正在听，再点一下结束' : '和小橙子说话' }}</button>
          </div>
          <el-button class="send-btn" type="success" :loading="sending" @click="ask()"><el-icon><Promotion /></el-icon>发送</el-button>
          <small>AI 建议仅供辅助决策；灌溉等设备操作仍需进入对应页面确认。</small>
        </div>
      </main>

      <aside class="assistant-side">
        <section class="content-panel mascot-card">
          <div class="big-mascot" :class="{ listening, thinking: sending }"><span class="leaf"></span><span class="eye eye-l"></span><span class="eye eye-r"></span><span class="mouth"></span><span class="cheek cheek-l"></span><span class="cheek cheek-r"></span></div>
          <strong>{{ sending ? '我正在分析呢……' : listening ? '我在听呢……' : '你好呀，我是小橙子' }}</strong>
          <p>{{ listening ? '说完后再点一下结束。' : '直接说果园里的问题，不用先选择功能。' }}</p>
          <button class="mascot-talk" :class="{ listening }" type="button" :disabled="sending" @click="toggleVoice">{{ listening ? '结束说话' : '开始说话' }}</button>
          <small v-if="!speechSupported">当前浏览器不支持语音识别，可继续使用文字输入。</small>
        </section>

        <section class="content-panel context-card">
          <div class="section-head"><div><h3>当前分析上下文</h3><p>仅使用账号有权访问的数据</p></div></div>
          <div class="context-plot"><strong>{{ plot?.plotName || '暂无地块' }}</strong><small>{{ plot?.cropName }} · {{ plot?.location }}</small></div>
          <dl>
            <div><dt>土壤湿度</dt><dd :class="{ danger: plot?.humidity < plot?.threshold }">{{ plot?.humidity ?? '-' }}%</dd></div>
            <div><dt>湿度阈值</dt><dd>{{ plot?.threshold ?? '-' }}%</dd></div>
            <div><dt>环境温度</dt><dd>{{ plot?.temperature ?? '-' }}℃</dd></div>
            <div><dt>设备状态</dt><dd>{{ plot?.deviceOnline ? '在线' : '离线' }}</dd></div>
          </dl>
        </section>

        <section class="content-panel quick-card">
          <div class="section-head"><div><h3>可以这样问我</h3><p>点击后直接发送</p></div></div>
          <button v-for="item in quick" :key="item" class="quick-question" type="button" @click="ask(item)">{{ item }}<el-icon><ArrowRight /></el-icon></button>
          <button class="irrigation-link" type="button" @click="router.push('/farmer/irrigation')">前往智慧灌溉</button>
        </section>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.assistant-page{padding-bottom:36px}.assistant-eyebrow{display:block;margin-bottom:7px;color:#a06f45;font-size:10px;font-weight:800;letter-spacing:2px}.assistant-head{align-items:flex-end;margin-bottom:18px}.assistant-grid{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:18px;min-height:calc(100vh - 190px)}.chat-panel{position:relative;display:flex;flex-direction:column;min-height:0;padding:0;overflow:hidden;border-color:rgba(205,194,177,.55);background:rgba(255,253,248,.67);box-shadow:0 12px 34px rgba(73,58,42,.055)}.messages{min-height:520px;flex:1;padding:24px;overflow-y:auto;background:linear-gradient(145deg,rgba(255,255,255,.32),rgba(243,248,244,.28))}.message{display:flex;align-items:flex-start;gap:11px;margin-bottom:18px}.message.user{flex-direction:row-reverse}.message-mascot{width:44px;display:flex;flex:0 0 44px;justify-content:center}.message-avatar{width:34px;height:34px;display:grid;place-items:center;flex:0 0 34px;border-radius:50%;color:#fff;background:#6d9279;font-size:11px}.orange-character{position:relative;width:38px;height:38px;border-radius:48% 52% 50% 50%;background:#e5a04e;box-shadow:inset -3px -4px 0 rgba(145,91,39,.09),0 5px 10px rgba(112,78,44,.1)}.orange-character .leaf{position:absolute;right:1px;top:-5px;width:14px;height:7px;border-radius:100% 0 100% 0;background:#66876d;transform:rotate(-24deg)}.orange-character .eye{position:absolute;top:15px;width:3px;height:5px;border-radius:50%;background:#5b463c}.orange-character .eye-l{left:11px}.orange-character .eye-r{right:11px}.orange-character .mouth{position:absolute;left:15px;top:23px;width:9px;height:5px;border-bottom:2px solid #674b3d;border-radius:0 0 50% 50%}.orange-character .cheek{position:absolute;top:23px;width:5px;height:3px;border-radius:50%;background:rgba(190,83,56,.24)}.orange-character .cheek-l{left:6px}.orange-character .cheek-r{right:6px}.orange-character.thinking{animation:breathe 1.1s ease-in-out infinite}.bubble{max-width:76%;padding:13px 15px;border:1px solid #e3ddd2;border-radius:6px 16px 16px;color:#4b5c54;background:rgba(255,255,255,.82)}.message.user .bubble{border:0;border-radius:16px 6px 16px 16px;color:#fff;background:#6d967e}.bubble p{margin:0;white-space:pre-line;font-size:13px;line-height:1.75}.answer-evidence{display:grid;gap:6px;margin-top:11px;padding-top:10px;border-top:1px solid rgba(215,207,194,.7)}.answer-evidence strong{color:#65766e;font-size:11px}.answer-evidence span{display:flex;align-items:center;gap:6px;color:#75877f;font-size:11px}.answer-evidence .el-icon{color:#559274}.typing{color:#7b8c85;font-size:12px}.composer{display:grid;grid-template-columns:1fr auto;gap:9px;padding:15px;border-top:1px solid #e3ddd2;background:rgba(255,255,255,.78)}.composer-box{position:relative}.composer-box :deep(.el-textarea__inner){padding-right:145px;background:rgba(255,255,255,.84)}.voice-trigger{position:absolute;right:8px;bottom:8px;height:32px;padding:0 10px;border:1px solid #d9d1c5;border-radius:10px;color:#6d665d;background:#faf7f0;cursor:pointer;font-size:11px}.voice-trigger span{margin-right:5px;color:#d9863e;font-size:8px}.voice-trigger.listening{color:#fff;border-color:#d9863e;background:#d9863e}.voice-trigger.listening span{color:#fff}.send-btn{height:54px}.composer small{grid-column:1/-1;color:#99a29d;font-size:10px}.assistant-side{display:grid;align-content:start;gap:18px}.mascot-card{text-align:center}.big-mascot{position:relative;width:136px;height:136px;margin:2px auto 14px;border-radius:48% 52% 49% 51%;background:#e5a04e;box-shadow:inset -10px -12px 0 rgba(145,91,39,.09),0 15px 28px rgba(112,78,44,.11);transition:.2s}.big-mascot.listening{transform:translateY(-3px) scale(1.03);box-shadow:0 0 0 9px rgba(213,143,64,.1),inset -10px -12px 0 rgba(145,91,39,.09),0 17px 30px rgba(112,78,44,.12)}.big-mascot.thinking{animation:breathe 1.1s ease-in-out infinite}.big-mascot .leaf{position:absolute;right:11px;top:-12px;width:37px;height:16px;border:1px solid #506d58;border-radius:100% 0 100% 0;background:#66876d;transform:rotate(-24deg)}.big-mascot .eye{position:absolute;top:52px;width:10px;height:14px;border-radius:50%;background:#5b463c}.big-mascot .eye-l{left:38px}.big-mascot .eye-r{right:38px}.big-mascot .mouth{position:absolute;left:56px;top:72px;width:25px;height:14px;border-bottom:4px solid #674b3d;border-radius:0 0 50% 50%}.big-mascot .cheek{position:absolute;top:76px;width:16px;height:9px;border-radius:50%;background:rgba(190,83,56,.23)}.big-mascot .cheek-l{left:21px}.big-mascot .cheek-r{right:21px}.mascot-card>strong{display:block;color:#4d4036;font-size:16px}.mascot-card>p{margin:6px 0 14px;color:#88938d;font-size:11px;line-height:1.7}.mascot-talk{height:39px;padding:0 22px;border:1px solid #d6cbbd;border-radius:12px;color:#6b594b;background:#faf5eb;cursor:pointer}.mascot-talk:hover,.mascot-talk.listening{color:#fff;border-color:#d9863e;background:#d9863e}.mascot-card>small{display:block;margin-top:9px;color:#a49e96;font-size:10px}.context-plot{padding:13px;border-radius:12px;background:#edf5ef}.context-plot strong,.context-plot small{display:block}.context-plot strong{color:#4c5f56}.context-plot small{margin-top:5px;color:#7b8c85;font-size:10px}.context-card dl{margin:13px 0 0}.context-card dl div{display:flex;justify-content:space-between;padding:8px 2px;border-bottom:1px solid #ebece6}.context-card dt{color:#81918b;font-size:11px}.context-card dd{margin:0;color:#29473d;font-size:12px;font-weight:650}.context-card dd.danger{color:#c45353}.quick-card .section-head{margin-bottom:7px}.quick-question{width:100%;display:flex;align-items:center;justify-content:space-between;padding:9px 2px;border:0;border-bottom:1px solid #ebece6;color:#5d7169;background:transparent;text-align:left;font-size:11px;cursor:pointer}.quick-question:hover{color:#b56a2d}.irrigation-link{margin-top:14px;padding:0;border:0;color:#a7652b;background:transparent;font-size:11px;cursor:pointer}.irrigation-link:hover{text-decoration:underline}@keyframes breathe{50%{transform:translateY(-3px) rotate(-2deg) scale(1.02)}}@media(max-width:1100px){.assistant-grid{grid-template-columns:1fr}.assistant-side{grid-template-columns:1fr 1fr}.quick-card{grid-column:1/-1}}@media(max-width:700px){.assistant-head{align-items:flex-start;flex-direction:column}.assistant-grid{min-height:auto}.messages{min-height:430px;padding:16px}.composer{grid-template-columns:1fr}.send-btn{height:42px}.assistant-side{grid-template-columns:1fr}.quick-card{grid-column:auto}.bubble{max-width:88%}.composer-box :deep(.el-textarea__inner){padding-right:12px;padding-bottom:48px}}
.assistant-grid{height:calc(100vh - 210px);min-height:480px}.messages{min-height:0}.assistant-side{overflow-y:auto;padding-right:3px}@media(max-width:1100px){.assistant-grid{height:auto}.assistant-side{overflow:visible}.messages{min-height:500px}}@media(max-width:700px){.messages{min-height:430px}}
</style>
