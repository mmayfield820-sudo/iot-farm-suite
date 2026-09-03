<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { usePlatformStore } from '@/stores/platform'
import { useUserStore } from '@/stores/user'
import { formatDateTime } from '@/utils/dataAdapters'

const router = useRouter()
const platformStore = usePlatformStore()
const userStore = useUserStore()
const DEVICE_TYPES = ['温度传感器', '湿度传感器', '灌溉设备']
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const refreshing = ref(false)
const dataUpdatedAt = ref(formatDateTime(new Date()))
const keyword = ref('')
const status = ref('')
const deviceType = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const dialog = ref(false)
const bindDialog = ref(false)
const importDialog = ref(false)
const importInput = ref(null)
const importRows = ref([])
const importFileName = ref('')
const importing = ref(false)
const current = ref(null)
const form = reactive({ deviceNo: '', deviceUuid: '', type: '温度传感器', farmId: '', plotNo: '' })
let excelModule

const farmIds = computed(() => {
  const scoped = (userStore.user?.roleScopes?.farmAdmin?.farmIds || []).map(String)
  return scoped.length ? scoped : platformStore.farms.map((farm) => String(farm.farmId))
})
const devices = computed(() => platformStore.devices.filter((device) =>
  !device.plotNo || farmIds.value.includes(String(device.farmId))
))
const currentFarmId = computed(() => farmIds.value[0] || '')
const plots = computed(() => platformStore.plots.filter((plot) => farmIds.value.includes(String(plot.farmId))))
const filteredDevices = computed(() => devices.value.filter((device) =>
  (!keyword.value || `${device.id}${device.deviceNo}`.toLowerCase().includes(keyword.value.trim().toLowerCase())) &&
  (!status.value || device.status === status.value) &&
  (!deviceType.value || device.type === deviceType.value)
))
const pagedDevices = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredDevices.value.slice(start, start + pageSize.value)
})
const validImportCount = computed(() => importRows.value.filter((item) => item.valid).length)
const totalCount = computed(() => devices.value.length)
const unboundCount = computed(() => devices.value.filter((device) => !device.plotNo).length)
const onlineCount = computed(() => devices.value.filter((device) => device.plotNo && device.status === '在线').length)
const abnormalCount = computed(() => devices.value.filter((device) => device.plotNo && ['异常', '离线'].includes(device.status)).length)
const statusSegments = computed(() => {
  const items = [
    { key: 'online', label: '在线正常', count: onlineCount.value, color: '#15915a' },
    { key: 'abnormal', label: '异常', count: abnormalCount.value, color: '#ef3438' },
    { key: 'unbound', label: '未绑定', count: unboundCount.value, color: '#ff9b0b' },
  ]
  let start = 0
  return items.map((item) => {
    const percent = totalCount.value ? item.count * 100 / totalCount.value : 0
    const middleAngle = (start + percent / 2) * 3.6 - 90
    const radians = middleAngle * Math.PI / 180
    const segment = {
      ...item,
      percent,
      dashLength: Math.max(0, percent - (percent ? 0.7 : 0)),
      dashOffset: -start,
      labelX: 130 + Math.cos(radians) * 113,
      labelY: 130 + Math.sin(radians) * 113,
    }
    start += percent
    return segment
  })
})
const deviceTypeStats = computed(() => {
  const knownTypes = [
    { key: 'temperature', label: '温度传感器', type: '温度传感器' },
    { key: 'humidity', label: '湿度传感器', type: '湿度传感器' },
    { key: 'irrigation', label: '灌溉设备', type: '灌溉设备' },
  ]
  const stats = knownTypes.map((item) => ({
    ...item,
    count: devices.value.filter((device) => device.type === item.type).length,
  }))
  const knownCount = stats.reduce((sum, item) => sum + item.count, 0)
  return [...stats, { key: 'other', label: '其他设备', count: Math.max(0, totalCount.value - knownCount) }]
})

function percentage(count) {
  if (!totalCount.value) return '0%'
  const value = count * 100 / totalCount.value
  return `${Number.isInteger(value) ? value : value.toFixed(1)}%`
}

async function getExcelJS() {
  if (!excelModule) excelModule = (await import('exceljs')).default
  return excelModule
}

function add() {
  Object.assign(form, { deviceNo: '', deviceUuid: '', type: '温度传感器', farmId: currentFarmId.value, plotNo: '' })
  dialog.value = true
}

async function save() {
  if (!form.deviceNo || !form.deviceUuid || !form.plotNo) return ElMessage.warning('请填写设备编号、设备 UUID 并选择所属地块')
  if (!UUID_PATTERN.test(form.deviceUuid)) return ElMessage.warning('设备 UUID 格式无效')
  const selectedPlot = plots.value.find((item) => item.plotNo === form.plotNo)
  form.farmId = selectedPlot?.farmId || currentFarmId.value
  try {
    await platformStore.addDevice({ ...form })
    await refreshData(true)
    dialog.value = false
    ElMessage.success('设备录入成功')
  } catch (error) {
    ElMessage.error(error.message || '设备录入失败')
  }
}

function openBind(row) {
  current.value = row
  form.plotNo = row.plotNo || row.plotId || ''
  bindDialog.value = true
}

async function saveBind() {
  if (!form.plotNo) return ElMessage.warning('请选择目标地块')
  try {
    await platformStore.bindDevice(current.value.id, form.plotNo)
    await refreshData(true)
    bindDialog.value = false
    ElMessage.success('设备绑定已更新')
  } catch (error) {
    ElMessage.error(error.message || '绑定失败')
  }
}

function unbind(row) {
  ElMessageBox.confirm(`解绑 ${row.deviceNo} 后，该地块的数据监测或远程控制可能受影响，历史记录会继续保留。`, '确认解绑', {
    type: 'warning',
    confirmButtonText: '确认解绑',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await platformStore.unbindDevice(row.id)
      await refreshData(true)
      ElMessage.success('设备已解绑，历史记录已保留')
    } catch (error) {
      ElMessage.error(error.message || '解绑失败')
    }
  }).catch(() => {})
}

function openImport() {
  importRows.value = []
  importFileName.value = ''
  importDialog.value = true
}

function selectImportFile() {
  importInput.value?.click()
}

function cellText(row, column) {
  const value = row.getCell(column).value
  if (value && typeof value === 'object') return String(value.text || value.result || value.hyperlink || '')
  return String(value ?? '').trim()
}

async function readExcel(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!/\.xlsx$/i.test(file.name)) return ElMessage.warning('请选择 .xlsx 格式文件')
  try {
    const ExcelJS = await getExcelJS()
    const workbook = new ExcelJS.Workbook()
    await workbook.xlsx.load(await file.arrayBuffer())
    const sheet = workbook.worksheets[0]
    if (!sheet) throw new Error('工作簿中没有可读取的工作表')
    const headers = {}
    sheet.getRow(1).eachCell((cell, column) => { headers[String(cell.value || '').trim()] = column })
    const noColumn = headers['设备编号'] || headers.deviceNo
    const uuidColumn = headers['设备 UUID'] || headers.deviceUuid
    const typeColumn = headers['设备类型'] || headers.type
    const plotColumn = headers['所属地块'] || headers.plotNo
    if (!noColumn || !uuidColumn || !typeColumn) throw new Error('表头必须包含“设备编号”、“设备 UUID”和“设备类型”')

    const existing = new Set(platformStore.devices.map((item) => String(item.deviceNo).toUpperCase()))
    const seen = new Set()
    const rows = []
    sheet.eachRow((row, rowNumber) => {
      if (rowNumber === 1) return
      const deviceNo = cellText(row, noColumn)
      const deviceUuid = cellText(row, uuidColumn)
      const type = cellText(row, typeColumn)
      const plotNo = plotColumn ? cellText(row, plotColumn) : ''
      if (!deviceNo && !type && !plotNo) return
      const errors = []
      if (!deviceNo) errors.push('设备编号为空')
      if (!deviceUuid) errors.push('设备 UUID 为空')
      else if (!UUID_PATTERN.test(deviceUuid)) errors.push('设备 UUID 格式无效')
      if (!plotNo) errors.push('所属地块为空')
      if (!DEVICE_TYPES.includes(type)) errors.push('设备类型无效')
      if (plotNo && !plots.value.some((item) => item.plotNo === plotNo)) errors.push('所属地块不存在或无权限')
      if (existing.has(deviceNo.toUpperCase()) || seen.has(deviceNo.toUpperCase())) errors.push('设备编号重复')
      if (deviceNo) seen.add(deviceNo.toUpperCase())
      const plot = plots.value.find((item) => item.plotNo === plotNo)
      rows.push({ rowNumber, deviceNo, deviceUuid, type, plotNo, farmId: plot?.farmId || currentFarmId.value, valid: !errors.length, error: errors.join('；') })
    })
    importRows.value = rows
    importFileName.value = file.name
    if (!rows.length) ElMessage.warning('文件中没有可导入的数据')
  } catch (error) {
    importRows.value = []
    ElMessage.error(error.message || 'Excel 文件解析失败')
  }
}

async function confirmImport() {
  const rows = importRows.value.filter((item) => item.valid)
  if (!rows.length) return ElMessage.warning('没有可导入的有效数据')
  importing.value = true
  let success = 0
  for (const row of rows) {
    try {
      await platformStore.addDevice({ deviceNo: row.deviceNo, deviceUuid: row.deviceUuid, type: row.type, plotNo: row.plotNo, farmId: row.farmId })
      success += 1
    } catch (error) {
      row.valid = false
      row.error = error.message || '导入失败'
    }
  }
  importing.value = false
  if (success) await refreshData(true)
  if (success === rows.length) importDialog.value = false
  ElMessage.success(`成功导入 ${success} 台设备`)
}

async function downloadTemplate() {
  const ExcelJS = await getExcelJS()
  const workbook = new ExcelJS.Workbook()
  const sheet = workbook.addWorksheet('设备导入模板')
  sheet.columns = [
    { header: '设备编号', key: 'deviceNo', width: 22 },
    { header: '设备 UUID', key: 'deviceUuid', width: 38 },
    { header: '设备类型', key: 'type', width: 20 },
    { header: '所属地块', key: 'plotNo', width: 18 },
  ]
  sheet.addRow({ deviceNo: 'SENSOR-010', deviceUuid: '123e4567-e89b-42d3-a456-426614174000', type: '湿度传感器', plotNo: plots.value[0]?.plotNo || '' })
  sheet.getRow(1).font = { bold: true }
  const blob = new Blob([await workbook.xlsx.writeBuffer()], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '设备批量导入模板.xlsx'
  link.click()
  URL.revokeObjectURL(url)
}

async function refreshData(force = true) {
  refreshing.value = true
  try {
    await platformStore.loadData(force)
    dataUpdatedAt.value = formatDateTime(new Date())
  } catch (error) {
    ElMessage.error(error.message || '设备数据加载失败')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => refreshData(false))
watch([keyword, status, deviceType], () => { currentPage.value = 1 })
</script>

<template>
  <div class="farmer-page device-management-page">
    <section class="device-overview-head">
      <div>
        <h1>设备监测与管理</h1>
        <p>查看所有地块设备的实时状态、运行数据与告警信息，并进行设备管理操作。</p>
      </div>
      <div class="device-update-status">
        <span>数据更新于 {{ dataUpdatedAt }}</span>
        <button type="button" title="刷新数据" :disabled="refreshing" @click="refreshData(true)">
          <el-icon :class="{ rotating: refreshing }"><RefreshRight /></el-icon>
        </button>
      </div>
    </section>

    <section class="device-stat-grid">
      <article class="device-stat-card total-card">
        <span class="device-stat-icon">
          <svg viewBox="0 0 48 48" aria-hidden="true">
            <path d="m7 16 17-9 17 9-17 9Z" />
            <path d="m9 24 15 8 15-8" />
            <path d="m9 32 15 8 15-8" />
          </svg>
        </span>
        <div class="device-stat-content">
          <span class="device-stat-label">设备总数</span>
          <strong>{{ totalCount }} <em>台</em></strong>
          <small>全部设备</small>
        </div>
      </article>

      <article class="device-stat-card online-card">
        <span class="device-stat-icon">
          <svg viewBox="0 0 48 48" aria-hidden="true">
            <circle cx="24" cy="24" r="17" />
            <path d="m16 24 6 6 11-13" />
          </svg>
        </span>
        <div class="device-stat-content">
          <span class="device-stat-label">在线设备</span>
          <div class="device-stat-value"><strong>{{ onlineCount }} <em>台</em></strong><b>{{ percentage(onlineCount) }}</b></div>
          <small>运行正常</small>
        </div>
      </article>

      <article class="device-stat-card abnormal-card">
        <span class="device-stat-icon">
          <svg viewBox="0 0 48 48" aria-hidden="true">
            <circle cx="24" cy="24" r="17" />
            <path d="m18 18 12 12M30 18 18 30" />
          </svg>
        </span>
        <div class="device-stat-content">
          <span class="device-stat-label">异常设备</span>
          <div class="device-stat-value"><strong>{{ abnormalCount }} <em>台</em></strong><b>{{ percentage(abnormalCount) }}</b></div>
          <small>需要检查</small>
        </div>
      </article>

      <article class="device-stat-card unbound-card">
        <span class="device-stat-icon">
          <svg viewBox="0 0 48 48" aria-hidden="true">
            <path d="M21 30 17 34a8 8 0 0 1-11-11l7-7a8 8 0 0 1 11 0" />
            <path d="m27 18 4-4a8 8 0 0 1 11 11l-7 7a8 8 0 0 1-11 0" />
            <path d="m17 24 14 0" />
          </svg>
        </span>
        <div class="device-stat-content">
          <span class="device-stat-label">未绑定设备</span>
          <div class="device-stat-value"><strong>{{ unboundCount }} <em>台</em></strong><b>{{ percentage(unboundCount) }}</b></div>
          <small>可绑定到地块</small>
        </div>
      </article>
    </section>

    <section class="device-insights-grid">
      <article class="device-status-card">
        <h2>设备状态分布</h2>
        <div class="device-status-body">
          <div class="status-donut" role="img" aria-label="设备状态分布图">
            <svg viewBox="0 0 260 260" aria-hidden="true">
              <circle class="donut-track" cx="130" cy="130" r="78" pathLength="100" />
              <circle
                v-for="segment in statusSegments"
                :key="segment.key"
                class="donut-segment"
                cx="130"
                cy="130"
                r="78"
                pathLength="100"
                :stroke="segment.color"
                :stroke-dasharray="`${segment.dashLength} ${100 - segment.dashLength}`"
                :stroke-dashoffset="segment.dashOffset"
              />
              <text
                v-for="segment in statusSegments.filter((item) => item.count)"
                :key="`${segment.key}-label`"
                :x="segment.labelX"
                :y="segment.labelY"
                :fill="segment.color"
              >{{ segment.count }}</text>
            </svg>
          </div>
          <div class="status-legend">
            <div v-for="segment in statusSegments" :key="segment.key" class="status-legend-item">
              <i :style="{ backgroundColor: segment.color }"></i>
              <span>{{ segment.label }}</span>
              <strong>{{ segment.count }}（{{ percentage(segment.count) }}）</strong>
            </div>
          </div>
        </div>
        <button class="device-alert-link" type="button" @click="router.push('/farm/alerts')">
          查看设备告警 <el-icon><ArrowRight /></el-icon>
        </button>
      </article>

      <article class="device-type-card">
        <h2>设备类型统计</h2>
        <div class="device-type-list">
          <div v-for="item in deviceTypeStats" :key="item.key" class="device-type-item">
            <span class="device-type-icon">
              <svg v-if="item.key === 'temperature'" viewBox="0 0 40 40" aria-hidden="true">
                <path d="M16 22.5V8a5 5 0 0 1 10 0v14.5a9 9 0 1 1-10 0Z" />
                <path d="M21 11v15" />
                <circle cx="21" cy="29" r="3.5" />
                <path d="M17 38h8" />
              </svg>
              <svg v-else-if="item.key === 'humidity'" viewBox="0 0 40 40" aria-hidden="true">
                <path d="M20 3S8 17 8 25a12 12 0 0 0 24 0C32 17 20 3 20 3Z" />
                <circle cx="20" cy="25" r="5" />
                <circle cx="20" cy="25" r="1" />
              </svg>
              <svg v-else-if="item.key === 'irrigation'" viewBox="0 0 40 40" aria-hidden="true">
                <path d="M19 27V15" />
                <path d="M19 15c-6 0-9-3-9-7 0-4 4-6 8-5 5 1 9 5 9 9 0 3-3 5-8 3Z" />
                <path d="M19 22h9v6" />
                <circle cx="9" cy="30" r="4" />
                <circle cx="28" cy="32" r="4" />
              </svg>
              <svg v-else viewBox="0 0 40 40" aria-hidden="true">
                <rect x="7" y="10" width="26" height="22" rx="7" />
                <path d="M15 10V6h10v4M7 18H4m3 7H4m32-7h-3m3 7h-3" />
                <path d="M17 22h6" />
              </svg>
            </span>
            <span class="device-type-name">{{ item.label }}</span>
            <strong>{{ item.count }} 台</strong>
            <b>{{ percentage(item.count) }}</b>
          </div>
        </div>
      </article>
    </section>

    <section class="device-binding-card">
      <header class="device-binding-head">
        <h2>设备绑定管理</h2>
      </header>

      <div class="device-binding-toolbar">
        <div class="device-binding-filters">
          <el-input v-model="keyword" clearable placeholder="搜索设备ID或设备编号">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="deviceType" clearable placeholder="全部设备类型">
            <el-option v-for="item in DEVICE_TYPES" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select v-model="status" clearable placeholder="全部状态">
            <el-option v-for="item in ['在线', '异常', '离线']" :key="item" :label="item" :value="item" />
          </el-select>
        </div>
        <div class="device-binding-actions">
          <el-button plain @click="openImport"><el-icon><Upload /></el-icon>Excel 批量导入</el-button>
          <el-button type="primary" @click="add"><el-icon><Plus /></el-icon>录入设备</el-button>
        </div>
      </div>

      <el-table :data="pagedDevices" class="device-binding-table">
        <el-table-column prop="deviceNo" label="设备编号" min-width="180" />
        <el-table-column prop="type" label="设备类型" min-width="160" />
        <el-table-column prop="plotNo" label="所属地块" min-width="130">
          <template #default="scope">{{ scope.row.plotNo || '未绑定' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="scope">
            <span :class="['binding-status', { danger: scope.row.status === '异常' }]">{{ scope.row.status }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170">
          <template #default="scope">
            <el-button link type="primary" @click="openBind(scope.row)">{{ scope.row.plotNo ? '换绑' : '绑定' }}</el-button>
            <el-button v-if="scope.row.plotNo" link type="danger" @click="unbind(scope.row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <footer class="device-binding-footer">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          background
          layout="prev, pager, next, sizes"
          :page-sizes="[10, 20, 50]"
          :total="filteredDevices.length"
        />
      </footer>
    </section>

    <el-dialog v-model="dialog" title="录入设备" width="520px">
      <el-form label-position="top">
        <el-form-item label="设备编号"><el-input v-model="form.deviceNo" placeholder="例如 SENSOR-010" /></el-form-item>
        <el-form-item label="设备 UUID"><el-input v-model="form.deviceUuid" placeholder="例如 123e4567-e89b-42d3-a456-426614174000" /></el-form-item>
        <el-form-item label="设备类型">
          <el-select v-model="form.type" style="width: 100%"><el-option v-for="item in DEVICE_TYPES" :key="item" :label="item" :value="item" /></el-select>
        </el-form-item>
        <el-form-item label="所属地块">
          <el-select v-model="form.plotNo" style="width: 100%" placeholder="请选择所属地块">
            <el-option v-for="item in plots" :key="item.plotNo" :label="`${item.plotNo} · ${item.name}`" :value="item.plotNo" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="dialog = false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="bindDialog" title="绑定设备" width="460px">
      <el-alert title="换绑或解绑不会删除设备已经产生的历史数据" type="warning" :closable="false" show-icon />
      <el-form label-position="top" class="bind-form">
        <el-form-item label="目标地块">
          <el-select v-model="form.plotNo" style="width: 100%">
            <el-option v-for="item in plots" :key="item.plotNo" :label="`${item.plotNo} · ${item.name}`" :value="item.plotNo" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="bindDialog = false">取消</el-button><el-button type="primary" @click="saveBind">确认绑定</el-button></template>
    </el-dialog>

    <el-dialog v-model="importDialog" title="Excel 批量导入设备" width="760px" class="import-dialog">
      <input ref="importInput" class="file-input" type="file" accept=".xlsx" @change="readExcel">
      <div class="import-guide">
        <div class="import-icon"><el-icon><DocumentAdd /></el-icon></div>
        <div><strong>{{ importFileName || '选择设备 Excel 文件' }}</strong><p>必填列：设备编号、设备 UUID、设备类型、所属地块</p></div>
        <el-button @click="selectImportFile">选择文件</el-button>
        <el-button link type="primary" @click="downloadTemplate">下载模板</el-button>
      </div>
      <el-alert title="设备类型仅支持：温度传感器、湿度传感器、灌溉设备。无效行不会被导入。" type="info" :closable="false" show-icon />
      <el-table v-if="importRows.length" :data="importRows" max-height="330" class="import-preview">
        <el-table-column prop="rowNumber" label="行号" width="70" />
        <el-table-column prop="deviceNo" label="设备编号" min-width="130" />
        <el-table-column prop="deviceUuid" label="设备 UUID" min-width="280" />
        <el-table-column prop="type" label="设备类型" min-width="120" />
        <el-table-column prop="plotNo" label="所属地块" width="110"><template #default="scope">{{ scope.row.plotNo || '未绑定' }}</template></el-table-column>
        <el-table-column label="校验结果" min-width="180"><template #default="scope"><el-tag :type="scope.row.valid ? 'success' : 'danger'" effect="plain">{{ scope.row.valid ? '可导入' : scope.row.error }}</el-tag></template></el-table-column>
      </el-table>
      <template #footer>
        <span class="import-count">{{ importRows.length ? `共 ${importRows.length} 行，${validImportCount} 行可导入` : '' }}</span>
        <el-button @click="importDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" :disabled="!validImportCount" @click="confirmImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.device-management-page { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.device-overview-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; margin: 4px 4px 24px; }
.device-overview-head h1 { margin: 0; color: #123d30; font-size: 34px; font-weight: 800; line-height: 1.25; }
.device-overview-head p { margin: 9px 0 0; color: #65746e; font-size: 15px; }
.device-update-status { display: flex; align-items: center; gap: 8px; padding-top: 8px; color: #78867f; font-size: 12px; white-space: nowrap; }
.device-update-status button { width: 30px; height: 30px; display: grid; place-items: center; padding: 0; border: 0; color: #365f53; background: transparent; font-size: 21px; cursor: pointer; }
.device-update-status button:disabled { cursor: wait; opacity: .6; }
.rotating { animation: rotate .8s linear infinite; }
@keyframes rotate { to { transform: rotate(360deg); } }
.device-stat-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; margin-bottom: 22px; }
.device-stat-card { min-width: 0; min-height: 156px; display: grid; grid-template-columns: 72px minmax(0, 1fr); align-items: center; gap: 20px; padding: 24px 24px; border: 1px solid #dfe7e3; border-radius: 12px; background: #fff; box-shadow: 0 7px 24px rgba(20, 69, 53, .045); }
.device-stat-icon { width: 72px; height: 72px; display: grid; place-items: center; border-radius: 16px; color: #137653; background: #edf7f2; }
.device-stat-icon svg { width: 42px; height: 42px; fill: none; stroke: currentColor; stroke-width: 3.2; stroke-linecap: round; stroke-linejoin: round; }
.device-stat-content { min-width: 0; }
.device-stat-label { display: block; margin-bottom: 8px; color: #45554f; font-size: 15px; font-weight: 650; }
.device-stat-content strong { color: #123f31; font-size: 31px; font-weight: 800; line-height: 1.1; white-space: nowrap; }
.device-stat-content strong em { font-size: 14px; font-style: normal; font-weight: 650; }
.device-stat-content small { display: block; margin-top: 13px; color: #687670; font-size: 12px; }
.device-stat-value { display: flex; align-items: baseline; flex-wrap: wrap; gap: 9px 16px; }
.device-stat-value b { color: #169b5b; font-size: 17px; font-weight: 800; white-space: nowrap; }
.abnormal-card .device-stat-icon { color: #ed3838; background: #fff0ef; }
.abnormal-card .device-stat-content strong,.abnormal-card .device-stat-value b { color: #ed3838; }
.unbound-card .device-stat-icon { color: #f08b0a; background: #fff5e7; }
.unbound-card .device-stat-content strong,.unbound-card .device-stat-value b { color: #f08b0a; }
.device-insights-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-bottom: 22px; }
.device-status-card { min-width: 0; min-height: 374px; display: flex; flex-direction: column; padding: 26px 28px 20px; border: 1px solid #dfe7e3; border-radius: 12px; background: #fff; box-shadow: 0 7px 24px rgba(20, 69, 53, .045); }
.device-status-card h2 { margin: 0; color: #173f32; font-size: 21px; font-weight: 800; line-height: 1.25; }
.device-status-body { min-width: 0; display: grid; grid-template-columns: minmax(230px, .95fr) minmax(220px, 1.05fr); align-items: center; gap: 18px; flex: 1; }
.status-donut { width: min(100%, 270px); aspect-ratio: 1; justify-self: center; }
.status-donut svg { width: 100%; height: 100%; display: block; overflow: visible; }
.donut-track,.donut-segment { fill: none; stroke-width: 47; }
.donut-track { stroke: #edf1ef; }
.donut-segment { transform: rotate(-90deg); transform-origin: 130px 130px; }
.status-donut text { font-size: 17px; font-weight: 800; text-anchor: middle; dominant-baseline: middle; }
.status-legend { display: grid; gap: 26px; padding-right: 2px; }
.status-legend-item { min-width: 0; display: grid; grid-template-columns: 17px minmax(70px, 1fr) auto; align-items: center; gap: 13px; color: #314b42; }
.status-legend-item i { width: 17px; height: 17px; border-radius: 3px; }
.status-legend-item span { font-size: 15px; white-space: nowrap; }
.status-legend-item strong { font-size: 14px; font-weight: 600; white-space: nowrap; }
.device-alert-link { align-self: flex-end; display: inline-flex; align-items: center; gap: 4px; padding: 5px 0; border: 0; color: #248557; background: transparent; font-size: 13px; font-weight: 700; cursor: pointer; }
.device-alert-link .el-icon { font-size: 16px; }
.device-type-card { min-width: 0; min-height: 374px; padding: 26px 32px 24px; border: 1px solid #dfe7e3; border-radius: 12px; background: #fff; box-shadow: 0 7px 24px rgba(20, 69, 53, .045); }
.device-type-card h2 { margin: 0; color: #173f32; font-size: 21px; font-weight: 800; line-height: 1.25; }
.device-type-list { display: grid; align-content: center; gap: 25px; min-height: 294px; padding-top: 14px; }
.device-type-item { min-width: 0; display: grid; grid-template-areas: "icon name count percent"; grid-template-columns: 38px minmax(130px, 1fr) auto 72px; align-items: center; gap: 18px; color: #285f53; }
.device-type-icon { grid-area: icon; width: 38px; height: 38px; display: grid; place-items: center; }
.device-type-icon svg { width: 34px; height: 34px; fill: none; stroke: currentColor; stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.device-type-name { grid-area: name; color: #344d44; font-size: 16px; white-space: nowrap; }
.device-type-item strong,.device-type-item b { color: #344d44; font-size: 15px; font-weight: 600; white-space: nowrap; }
.device-type-item strong { grid-area: count; }
.device-type-item b { grid-area: percent; text-align: right; }
.device-binding-card { margin-bottom: 22px; overflow: hidden; border: 1px solid #dfe7e3; border-radius: 12px; background: #fff; box-shadow: 0 7px 24px rgba(20, 69, 53, .045); }
.device-binding-head { padding: 24px 28px 20px; }
.device-binding-head h2 { margin: 0; color: #173f32; font-size: 21px; font-weight: 800; line-height: 1.25; }
.device-binding-actions { display: flex; align-items: center; flex: 0 0 auto; gap: 12px; margin-left: auto; }
.device-binding-actions :deep(.el-button) { min-height: 40px; margin: 0; padding-inline: 17px; border-radius: 7px; }
.device-binding-actions :deep(.el-button--primary) { border-color: #1b805d; background: #1b805d; }
.device-binding-toolbar { display: flex; align-items: center; gap: 12px; padding: 0 28px 22px; }
.device-binding-filters { min-width: 0; display: grid; grid-template-columns: minmax(260px, 380px) repeat(2, minmax(160px, 210px)); gap: 12px; flex: 1; }
.device-binding-filters :deep(.el-input),.device-binding-filters :deep(.el-select) { width: 100%; }
.device-binding-toolbar :deep(.el-input__wrapper),.device-binding-toolbar :deep(.el-select__wrapper) { min-height: 42px; border-radius: 7px; box-shadow: 0 0 0 1px #d7e0dc inset; }
.device-binding-table { width: calc(100% - 56px); margin: 0 28px 24px; }
.device-binding-table::before { display: none; }
.device-binding-table :deep(.el-table__header th) { height: 56px; color: #53685f; background: #f2f7f4; font-size: 13px; font-weight: 750; }
.device-binding-table :deep(.el-table__row td) { height: 62px; color: #59635f; font-size: 13px; }
.device-binding-table :deep(.el-table__cell) { border-bottom-color: #e8eeeb; }
.device-binding-table :deep(.el-button.is-link) { font-size: 13px; font-weight: 650; }
.device-binding-table :deep(.el-button--primary.is-link) { color: #16805a; }
.binding-status { display: inline-flex; align-items: center; min-height: 30px; padding: 0 10px; border-radius: 8px; color: #16805a; background: #e9f7f0; font-size: 12px; }
.binding-status.danger { color: #dc4744; background: #fff0ef; }
.device-binding-footer { display: flex; justify-content: flex-end; padding: 0 28px 24px; }
.device-binding-footer :deep(.el-pagination) { gap: 8px; }
.device-binding-footer :deep(.btn-prev),.device-binding-footer :deep(.btn-next),.device-binding-footer :deep(.el-pager li) { min-width: 36px; height: 36px; border: 1px solid #d7e0dc; border-radius: 7px; background: #fff; color: #43554e; }
.device-binding-footer :deep(.el-pager li.is-active) { border-color: #16805a; color: #fff; background: #16805a; }
.device-binding-footer :deep(.el-select__wrapper) { min-height: 36px; border-radius: 7px; }
.bind-form { margin-top: 18px; }
.file-input { display: none; }
.import-guide { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; padding: 16px; border: 1px dashed #b9d5c7; border-radius: 10px; background: #f6fbf8; }
.import-guide>div:nth-child(2) { min-width: 0; flex: 1; }
.import-guide strong,.import-guide p { display: block; margin: 0; }
.import-guide strong { color: #315347; }
.import-guide p { margin-top: 5px; color: #84958e; font-size: 12px; }
.import-icon { width: 42px; height: 42px; display: grid; place-items: center; flex: 0 0 42px; border-radius: 10px; color: #27835d; background: #e2f3ea; font-size: 21px; }
.import-preview { margin-top: 14px; }
.import-count { margin-right: auto; color: #678078; font-size: 12px; }
:deep(.el-dialog__footer) { display: flex; align-items: center; }
@media (max-width: 1280px) {
  .device-stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .device-insights-grid { grid-template-columns: 1fr; }
  .device-status-card { max-width: none; }
  .device-binding-toolbar { align-items: flex-end; flex-wrap: wrap; }
  .device-binding-filters { flex-basis: 100%; grid-template-columns: minmax(240px, 1.4fr) repeat(2, minmax(150px, 1fr)); }
}
@media (max-width: 700px) {
  .device-overview-head { flex-direction: column; margin-inline: 0; }
  .device-overview-head h1 { font-size: 28px; }
  .device-update-status { align-self: flex-end; padding-top: 0; }
  .device-stat-grid { grid-template-columns: 1fr; }
  .device-stat-card { min-height: 140px; grid-template-columns: 62px minmax(0, 1fr); gap: 16px; padding: 20px; }
  .device-stat-icon { width: 62px; height: 62px; }
  .device-stat-icon svg { width: 37px; height: 37px; }
  .device-status-card { min-height: 0; padding: 22px 18px 18px; }
  .device-status-body { grid-template-columns: 1fr; gap: 4px; padding: 12px 0 18px; }
  .status-donut { width: min(100%, 250px); }
  .status-legend { gap: 16px; padding: 0 8px; }
  .status-legend-item { grid-template-columns: 16px minmax(0, 1fr) auto; gap: 10px; }
  .device-type-card { min-height: 0; padding: 22px 18px; }
  .device-type-list { min-height: 0; gap: 18px; padding-top: 24px; }
  .device-type-item { grid-template-areas: "icon name count" "icon name percent"; grid-template-columns: 34px minmax(0, 1fr) auto; gap: 3px 10px; }
  .device-type-item b { font-size: 12px; }
  .device-binding-actions { width: 100%; }
  .device-binding-actions :deep(.el-button) { flex: 1; }
  .device-binding-toolbar { align-items: stretch; flex-direction: column; }
  .device-binding-filters { width: 100%; display: flex; flex-direction: column; }
  .device-binding-table { width: calc(100% - 36px); margin-inline: 18px; }
  .device-binding-footer { justify-content: center; padding-inline: 18px; overflow-x: auto; }
  .import-guide { align-items: flex-start; flex-wrap: wrap; }
}
</style>
