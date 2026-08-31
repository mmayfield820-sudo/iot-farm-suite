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
  create_employee: '预置员工账号', update_employee: '修改账号或授权', change_employee_status: '修改账号状态',
  reset_initial_password: '重置初始密码', commit_employee_import: '提交员工导入',
  update_cycle_draft: '修改下一周期草稿', publish_cycle_draft: '发布下一周期版本', generate_plans: '生成地块计划', adjust_task: '调整农事任务', complete_task: '完成农事任务', create_ad_hoc_task: '补记计划外农事',
  issue_irrigation_command: '下发灌溉指令', bind_device: '绑定设备', unbind_device: '解绑设备',
}

const rows = computed(() => logs.value.filter((item) => {
  const search = keyword.value.trim().toLowerCase()
  return (!module.value || item.module === module.value) && (!search || `${item.actorName}${item.actorEmployeeNo}${item.detail}${item.action}`.toLowerCase().includes(search))
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

const formatAction = (value) => actionLabel[value] || value
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
        <el-table-column label="操作" min-width="160"><template #default="scope">{{ formatAction(scope.row.action) }}</template></el-table-column>
        <el-table-column label="对象" min-width="120"><template #default="scope">{{ scope.row.targetId || '-' }}</template></el-table-column>
        <el-table-column prop="detail" label="说明" min-width="260" show-overflow-tooltip />
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.log-filters { display: flex; gap: 10px; align-items: center; }.log-filters .el-input { width: 230px; }.log-filters .el-select { width: 160px; }.employee-no { display: block; margin-top: 3px; color: #98a69f; font-size: 11px; font-weight: 400; }
@media (max-width: 650px) { .log-filters { width: 100%; flex-wrap: wrap; }.log-filters .el-input, .log-filters .el-select { flex: 1 1 180px; width: auto; } }
</style>
