<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAuditLogs } from '@/api/audit'
import { formatDateTime } from '@/utils/dataAdapters'

const keyword = ref('')
const module = ref('')
const loading = ref(false)
const total = ref(0)
const logs = ref([])
const moduleOptions = [
  { value: 'master_data', label: '橙园与地块' },
  { value: 'account_access', label: '账号与授权' },
  { value: 'production_plan', label: '生产计划' },
  { value: 'task_execution', label: '农事执行' },
  { value: 'irrigation', label: '灌溉控制' },
  { value: 'device_binding', label: '设备绑定' },
]
const moduleLabel = Object.fromEntries(moduleOptions.map((item) => [item.value, item.label]))
const actionLabel = {
  create_farm: '新建橙园', update_farm: '修改橙园', create_plot: '新建地块', update_plot: '修改地块',
  update_own_profile: '修改个人资料', create_employee: '预置员工账号', update_employee: '修改账号及授权', change_employee_status: '修改账号状态',
  reset_initial_password: '重置初始密码', commit_employee_import: '提交员工导入',
  publish_standard_template_version: '发布标准模板版本', update_cycle_draft: '修改下一周期草稿', rebase_cycle_draft: '重新生成周期草稿', publish_cycle_draft: '发布周期计划版本',
  confirm_farm_planting: '确认橙园定植', schedule_farm_planting: '安排橙园定植', save_annual_production: '保存年度生产计划', update_plot_date_offset: '调整地块计划日期',
  start_stage: '确认生产阶段开始', dispatch_stage: '下发阶段任务', generate_plans: '生成地块计划', adjust_task: '调整农事任务', create_change_order: '变更农事任务', create_temporary_task: '新增临时农事',
  complete_task: '登记农事完成', correct_task_completion: '更正农事完成记录', create_historical_stage_supplement: '补录历史阶段农事', create_ad_hoc_task: '补记计划外农事',
  record_harvest_completion: '登记采收完成', record_cleanup_completion: '登记采后清园完成',
  issue_irrigation_command: '下发灌溉指令', bind_device: '绑定设备', unbind_device: '解绑设备',
}
const targetTypeLabel = {
  user: '员工账号', import_job: '账号导入任务', farm: '橙园', plot: '地块', device: '设备',
  crop_template: '品种模板', cycle_draft: '周期计划版本', farm_stage: '橙园生产阶段', task: '农事任务', production_archive: '年度生产档案',
}
const statusLabel = { pending_activation: '待激活', active: '启用', disabled: '停用' }
const trackLabel = { young: '幼树', fruiting: '结果树' }
const detailPreviewLength = 12

const capture = (text, pattern, index = 1) => text.match(pattern)?.[index]
const readableTime = (value) => value?.replace('T', ' ').replace(/\.\d+$/, '')
const containsChinese = (value) => /[\u3400-\u9fff]/.test(value)

function formatTarget(row) {
  if (!row.targetType && !row.targetId) return '-'
  const label = targetTypeLabel[row.targetType] || '业务对象'
  if (!row.targetId) return label
  if (row.targetType === 'farm_stage') {
    const [farmId, year, stageCode] = row.targetId.split(':')
    return `${label}（${farmId || '-'}，${year || '-'} 年度，阶段 ${stageCode || '-'}）`
  }
  if (row.targetType === 'production_archive') {
    const [farmId, year] = row.targetId.split(':')
    return `${label}（${farmId || '-'}，${year || '-'} 年度）`
  }
  return `${label}（${row.targetId}）`
}

function formatDetail(row) {
  const detail = String(row.detail || '').trim()
  const action = row.action
  if (action === 'update_own_profile') return '更新了本人姓名、联系方式或登录密码。'
  if (action === 'confirm_farm_planting') return `确认橙园实际定植日期为 ${capture(detail, /:\s*(.+)$/) || '所选日期'}。`
  if (action === 'create_employee') return `已预置员工账号，登录工号为 ${capture(detail, /employee\s+(.+)$/i) || '所填工号'}。`
  if (action === 'update_employee') return '更新了员工基本资料、角色或橙园/地块授权范围。'
  if (action === 'change_employee_status') return `已将员工账号设为“${statusLabel[capture(detail, /status\s+(.+)$/i)] || '指定状态'}”。`
  if (action === 'reset_initial_password') return '已重置账号初始密码；该员工下次登录时需要重新完成激活。'
  if (action === 'commit_employee_import') return `已完成 Excel 批量导入，共导入 ${capture(detail, /Imported\s+(\d+)/i) || '若干'} 个员工账号。`
  if (action === 'publish_standard_template_version') return `已发布品种标准模板 ${capture(detail, /(V\d+)$/i) || '新版本'}。`
  if (action === 'update_cycle_draft') return '已更新该橙园的下一生产年度管理计划草稿。'
  if (action === 'rebase_cycle_draft') return `已基于模板版本 ${capture(detail, /from\s+(\S+)$/i) || '所选版本'} 重新生成草稿，原草稿内容已被替换。`
  if (action === 'publish_cycle_draft') {
    const match = detail.match(/Published the (initial|next) farm version for (\S+)/i)
    return `已为橙园 ${match?.[2] || '对应橙园'} 发布${match?.[1] === 'initial' ? '首个' : '下一年度'}管理计划版本。`
  }
  if (action === 'start_stage') return `已确认该生产阶段于 ${readableTime(capture(detail, /at\s+(.+)$/i)) || '所选时间'} 开始。`
  if (action === 'dispatch_stage') {
    const match = detail.match(/Dispatched\s+(\d+)\s+tasks for stage\s+(.+)$/i)
    return `已为阶段 ${match?.[2] || '对应阶段'} 下发 ${match?.[1] || '若干'} 项农事任务。`
  }
  if (action === 'adjust_task') return '已调整尚未完成的农事任务日期、备注或状态。'
  if (action === 'create_change_order') {
    const match = detail.match(/Replaced by\s+(\S+):\s*(.+)$/i)
    return `已生成替代任务 ${match?.[1] || '新任务'}；变更原因：${match?.[2] || '详见任务记录'}。`
  }
  if (action === 'create_temporary_task') return `已新增当前阶段的临时农事任务；原因：${detail || '未填写'}。`
  if (action === 'create_historical_stage_supplement') return `已补录过去生产阶段的实际执行记录；补录原因：${detail || '未填写'}。`
  if (action === 'complete_task') return `已登记任务完成情况，完成记录编号为 ${capture(detail, /completion\s+(\S+)$/i) || '系统生成编号'}。`
  if (action === 'correct_task_completion') {
    const match = detail.match(/correction\s+(\S+):\s*(.+)$/i)
    return `已追加完成记录更正 ${match?.[1] || ''}${match?.[2] ? `；更正原因：${match[2]}` : ''}。`
  }
  if (action === 'create_ad_hoc_task') return `已为地块 ${capture(detail, /for\s+(\S+)$/i) || '对应地块'} 补记一项已完成的计划外农事。`
  if (['record_harvest_completion', 'record_cleanup_completion'].includes(action)) return `已登记该生产年度的${action === 'record_harvest_completion' ? '采收' : '采后清园'}完成时间：${readableTime(capture(detail, /at\s+(.+)$/i)) || '所选时间'}。`
  if (action === 'save_annual_production') {
    const match = detail.match(/independent\s+(\d+)\s+farm management plan using track\s+(\S+)/i)
    return `已保存 ${match?.[1] || '对应年度'} 年度独立管理计划，采用${trackLabel[match?.[2]] || '所选'}生产轨道。`
  }
  if (action === 'schedule_farm_planting') return `已按 ${capture(detail, /for\s+(\S+)$/i) || '所选日期'} 为橙园各有效地块安排定植任务。`
  if (action === 'create_farm') return `已创建橙园“${capture(detail, /farm\s+(.+)$/i) || '所填名称'}”。`
  if (action === 'update_farm') return '已更新橙园名称、地址、面积、负责人、备注或启停状态。'
  if (action === 'create_plot') return `已创建地块“${capture(detail, /plot\s+(.+)$/i) || '所填名称'}”。`
  if (action === 'update_plot') return '已更新地块档案、所属橙园或启停状态。'
  if (action === 'update_plot_date_offset') return `已将该地块生产计划日期整体偏移 ${capture(detail, /to\s+(-?\d+)\s+days/i) || '所填'} 天。`
  if (action === 'bind_device') return `已将设备绑定至地块 ${capture(detail, /to\s+(\S+)$/i) || '所选地块'}。`
  if (action === 'unbind_device') return '已解除设备与地块的绑定，并将设备状态标记为离线。'
  if (action === 'issue_irrigation_command') {
    const match = detail.match(/irrigation_(on|off) command (\S+) for (\S+)/i)
    return `已向地块 ${match?.[3] || '对应地块'} 的设备下发${match?.[1] === 'off' ? '关闭' : '开启'}灌溉指令，指令编号为 ${match?.[2] || '系统生成编号'}。`
  }
  if (containsChinese(detail)) return detail
  return `${actionLabel[action] || '该项关键操作'}已执行，相关记录已保存。`
}

function detailPreview(row) {
  const characters = Array.from(formatDetail(row))
  return characters.length > detailPreviewLength ? `${characters.slice(0, detailPreviewLength).join('')}......` : characters.join('')
}

const isDetailTruncated = (row) => Array.from(formatDetail(row)).length > detailPreviewLength

const rows = computed(() => logs.value.filter((item) => {
  const search = keyword.value.trim().toLowerCase()
  return (!module.value || item.module === module.value) && (!search || `${item.actorName}${item.actorEmployeeNo}${formatAction(item.action)}${formatTarget(item)}${formatDetail(item)}`.toLowerCase().includes(search))
}))

async function loadLogs() {
  loading.value = true
  try {
    const response = await getAuditLogs({ page: 1, pageSize: 100 })
    logs.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    ElMessage.error(error.message || '操作日志加载失败')
  } finally {
    loading.value = false
  }
}

const formatAction = (value) => actionLabel[value] || '其他关键操作'
const formatModule = (value) => moduleLabel[value] || value

onMounted(loadLogs)
</script>

<template>
  <div class="farmer-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">关键操作日志</h1>
        <p class="page-subtitle">追溯橙园和地块维护、账号授权、计划、农事与灌溉控制等关键操作。</p>
      </div>
      <div class="page-actions log-filters">
        <el-input v-model="keyword" clearable placeholder="搜索操作人或内容">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="module" clearable placeholder="全部模块">
          <el-option v-for="item in moduleOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-button :loading="loading" circle aria-label="刷新操作日志" title="刷新操作日志" @click="loadLogs"><el-icon><Refresh /></el-icon></el-button>
      </div>
    </div>

    <section class="content-panel" v-loading="loading">
      <div class="section-head"><div><h3>操作记录</h3><p>已记录 {{ total }} 条关键操作。</p></div></div>
      <el-table :data="rows" class="compact-table" empty-text="暂无操作日志">
        <el-table-column label="时间" min-width="180"><template #default="scope">{{ formatDateTime(scope.row.occurredAt, '-') }}</template></el-table-column>
        <el-table-column label="操作人" min-width="150"><template #default="scope"><strong>{{ scope.row.actorName }}</strong><small class="employee-no">{{ scope.row.actorEmployeeNo || '-' }}</small></template></el-table-column>
        <el-table-column label="模块" min-width="120"><template #default="scope"><span class="status-pill info">{{ formatModule(scope.row.module) }}</span></template></el-table-column>
        <el-table-column label="操作" min-width="180"><template #default="scope">{{ formatAction(scope.row.action) }}</template></el-table-column>
        <el-table-column label="对象" min-width="220"><template #default="scope">{{ formatTarget(scope.row) }}</template></el-table-column>
        <el-table-column label="说明" min-width="360">
          <template #default="scope">
            <el-tooltip :content="formatDetail(scope.row)" :disabled="!isDetailTruncated(scope.row)" placement="top" popper-class="audit-detail-tooltip">
              <span class="detail-preview">{{ detailPreview(scope.row) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.log-filters { display: flex; gap: 10px; align-items: center; }.log-filters .el-input { width: 230px; }.log-filters .el-select { width: 160px; }.employee-no { display: block; margin-top: 3px; color: #98a69f; font-size: 11px; font-weight: 400; }.detail-preview { display: block; white-space: nowrap; }
:global(.audit-detail-tooltip) { max-width: 520px; line-height: 1.6; white-space: normal; }
@media (max-width: 650px) { .log-filters { width: 100%; flex-wrap: wrap; }.log-filters .el-input, .log-filters .el-select { flex: 1 1 180px; width: auto; } }
</style>
