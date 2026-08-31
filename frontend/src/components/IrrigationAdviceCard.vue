<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getIrrigationAdvice } from '@/api/irrigationAdvice'

const props = defineProps({ plotId: { type: String, default: '' } })
const router = useRouter()
const advice = ref(null)
const loading = ref(false)
const labels = { IRRIGATE: '建议灌溉', NO_IRRIGATION: '暂不建议灌溉', CHECK_DEVICE: '请先检查设备', DATA_INSUFFICIENT: '数据不足' }
const tone = computed(() => ({ IRRIGATE: 'warning', NO_IRRIGATION: 'success', CHECK_DEVICE: 'danger', DATA_INSUFFICIENT: 'info' }[advice.value?.decision] || 'info'))
async function load() { if (!props.plotId) return; loading.value = true; try { advice.value = await getIrrigationAdvice(props.plotId) } catch { advice.value = null } finally { loading.value = false } }
function goIrrigation() { router.push({ path: '/farmer/irrigation', query: { plotId: props.plotId, suggestedDuration: advice.value.suggestedDuration, source: 'advice' } }) }
watch(() => props.plotId, load, { immediate: true })
</script>
<style scoped>.advice-card{margin-bottom:18px;border-color:#efd5c0;background:linear-gradient(120deg,#fff5e8,#fffdfa)}.advice-content{display:grid;grid-template-columns:54px 1fr 180px;gap:18px;align-items:flex-start}.advice-mark{width:52px;height:52px;display:grid;place-items:center;border-radius:16px;color:#fff;background:#db6b1c;font-size:20px}.advice-copy>span{color:#aa5b28;font-size:12px}.title{display:flex;align-items:center;gap:10px}.title h2{margin:6px 0;color:#512b15}.advice-copy p{margin:5px 0;color:#806857;font-size:12px}.advice-metrics{display:grid;gap:4px;text-align:right}.advice-metrics b{color:#9e4613;font-size:18px}.advice-metrics small{margin-bottom:7px;color:#947461}@media(max-width:760px){.advice-content{grid-template-columns:52px 1fr}.advice-metrics{grid-column:1/3;text-align:left}}</style>
