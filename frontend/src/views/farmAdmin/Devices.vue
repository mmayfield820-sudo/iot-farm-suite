<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePlatformStore } from '@/stores/platform'
import { useFarmAdminStore } from '@/stores/farmAdmin'

const DEVICE_TYPES = ['温度传感器', '湿度传感器', '灌溉设备']
const store = usePlatformStore()
const farmAdminStore = useFarmAdminStore()
const keyword = ref('')
const status = ref('')
const deviceType = ref('')
const dialog = ref(false)
const bindDialog = ref(false)
const importDialog = ref(false)
const importInput = ref(null)
const importRows = ref([])
const importFileName = ref('')
const importing = ref(false)
const current = ref(null)
const form = reactive({ deviceNo: '', deviceUuid: '', type: '温度传感器', farmId: '', plotNo: '' })
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const farmIds = computed(() => farmAdminStore.selectedFarmIds)
const currentFarmId = computed(() => farmAdminStore.selectedFarmId === farmAdminStore.ALL_FARMS ? farmIds.value[0] || '' : farmAdminStore.selectedFarmId)
const devices = computed(() => store.devices.filter((item) =>
  farmIds.value.includes(String(item.farmId)) &&
  (!keyword.value || `${item.id}${item.deviceNo}`.toLowerCase().includes(keyword.value.toLowerCase())) &&
  (!status.value || item.status === status.value) &&
  (!deviceType.value || item.type === deviceType.value)
))
const plots = computed(() => store.plots.filter((item) => farmIds.value.includes(String(item.farmId))))
const logs = computed(() => store.auditLogs.filter((item) => ['设备管理', '设备绑定'].includes(item.module)).slice(0, 8))
const latestHeartbeat = computed(() => devices.value.map((item) => item.lastHeartbeat).filter(Boolean).sort().at(-1) || '暂无')
const validImportCount = computed(() => importRows.value.filter((item) => item.valid).length)
let excelModule

watch(() => farmAdminStore.selectedFarmId, () => {
  keyword.value = ''
  status.value = ''
  deviceType.value = ''
  dialog.value = false
  bindDialog.value = false
  importDialog.value = false
})

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
  const selectedPlot = store.plots.find((item) => item.plotNo === form.plotNo)
  form.farmId = selectedPlot?.farmId || currentFarmId.value
  try {
    await store.addDevice({ ...form })
    dialog.value = false
    ElMessage.success('设备录入成功')
  } catch (error) { ElMessage.error(error.message || '设备录入失败') }
}

function openBind(row) {
  current.value = row
  form.plotNo = row.plotNo || row.plotId || ''
  bindDialog.value = true
}

async function saveBind() {
  if (!form.plotNo) return ElMessage.warning('请选择目标地块')
  try {
    await store.bindDevice(current.value.id, form.plotNo)
    bindDialog.value = false
    ElMessage.success('设备绑定已更新')
  } catch (error) { ElMessage.error(error.message || '绑定失败') }
}

function unbind(row) {
  ElMessageBox.confirm(`解绑 ${row.deviceNo} 后，该地块的数据监测或远程控制可能受影响，历史记录会继续保留。`, '确认解绑', { type: 'warning', confirmButtonText: '确认解绑' }).then(async () => {
    try {
      await store.unbindDevice(row.id)
      ElMessage.success('设备已解绑，历史记录已保留')
    } catch (error) { ElMessage.error(error.message || '解绑失败') }
  })
}

function openImport() {
  importRows.value = []
  importFileName.value = ''
  importDialog.value = true
}

function selectImportFile() { importInput.value?.click() }

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

    const existing = new Set(store.devices.map((item) => String(item.deviceNo).toUpperCase()))
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
      await store.addDevice({ deviceNo: row.deviceNo, deviceUuid: row.deviceUuid, type: row.type, plotNo: row.plotNo, farmId: row.farmId })
      success += 1
    } catch (error) {
      row.valid = false
      row.error = error.message || '导入失败'
    }
  }
  importing.value = false
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
</script>

<template>
  <div class="farmer-page">
    <div class="page-head">
      <div><h1 class="page-title">设备管理</h1><p class="page-subtitle">录入设备并维护数据库中的设备编号、类型、所属地块和最后心跳。</p></div>
      <div class="page-actions">
        <el-button plain @click="openImport"><el-icon><Upload /></el-icon>Excel 批量导入</el-button>
        <el-button type="primary" @click="add"><el-icon><Plus /></el-icon>录入设备</el-button>
      </div>
    </div>

    <section class="farmer-stat-grid">
      <div class="farmer-stat"><div class="stat-symbol"><el-icon><Connection/></el-icon></div><div><label>在线设备</label><strong>{{ devices.filter(x => x.status === '在线').length }}</strong><small>心跳正常</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol red"><el-icon><Warning/></el-icon></div><div><label>异常设备</label><strong>{{ devices.filter(x => ['异常','离线'].includes(x.status)).length }}</strong><small>需要检查</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol orange"><el-icon><Remove/></el-icon></div><div><label>未绑定设备</label><strong>{{ devices.filter(x => !x.plotNo).length }}</strong><small>可绑定到地块</small></div></div>
      <div class="farmer-stat"><div class="stat-symbol blue"><el-icon><MessageBox/></el-icon></div><div><label>最近设备心跳</label><strong class="heartbeat-value">{{ latestHeartbeat.slice(11) || latestHeartbeat }}</strong><small>随设备上报动态变化</small></div></div>
    </section>

    <section class="content-panel device-table">
      <div class="toolbar">
        <el-input v-model="keyword" clearable placeholder="搜索设备ID或设备编号"><template #prefix><el-icon><Search/></el-icon></template></el-input>
        <el-select v-model="deviceType" clearable placeholder="全部设备类型"><el-option v-for="item in DEVICE_TYPES" :key="item" :label="item" :value="item"/></el-select>
        <el-select v-model="status" clearable placeholder="全部状态"><el-option v-for="item in ['在线','异常','离线']" :key="item" :label="item" :value="item"/></el-select>
      </div>
      <el-table :data="devices" class="compact-table">
        <el-table-column prop="id" label="设备ID" width="85"/>
        <el-table-column prop="deviceNo" label="设备编号" min-width="125"/>
        <el-table-column prop="type" label="设备类型" min-width="120"/>
        <el-table-column prop="plotNo" label="所属地块" width="100"><template #default="scope">{{ scope.row.plotNo || '未绑定' }}</template></el-table-column>
        <el-table-column prop="status" label="通信状态" width="105"><template #default="scope"><span :class="['status-pill',scope.row.status === '离线' ? 'danger' : '']">{{ scope.row.status }}</span></template></el-table-column>
        <el-table-column prop="workStatus" label="采集状态" width="125"><template #default="scope"><span :class="['status-pill',scope.row.workStatus === '已停止采集' ? 'info' : '']">{{ scope.row.workStatus }}</span></template></el-table-column>
        <el-table-column prop="lastHeartbeat" label="最后心跳" min-width="170"/>
        <el-table-column label="操作" fixed="right" width="160"><template #default="scope"><el-button link type="primary" @click="openBind(scope.row)">{{ scope.row.plotNo ? '换绑' : '绑定' }}</el-button><el-button v-if="scope.row.plotNo" link type="danger" @click="unbind(scope.row)">解绑</el-button></template></el-table-column>
      </el-table>
    </section>

    <section class="content-panel logs"><div class="section-head"><div><h3>设备操作记录</h3><p>记录设备录入、绑定、换绑和解绑操作</p></div></div><el-table :data="logs" class="compact-table"><el-table-column prop="time" label="时间" min-width="170"/><el-table-column prop="user" label="操作人" min-width="130"/><el-table-column prop="module" label="类型" width="110"/><el-table-column prop="action" label="操作内容" min-width="260"/><el-table-column prop="result" label="结果" width="90"/></el-table></section>

    <el-dialog v-model="dialog" title="录入设备" width="520px"><el-form label-position="top"><el-form-item label="设备编号"><el-input v-model="form.deviceNo" placeholder="例如 SENSOR-010"/></el-form-item><el-form-item label="设备 UUID"><el-input v-model="form.deviceUuid" placeholder="例如 123e4567-e89b-42d3-a456-426614174000"/></el-form-item><el-form-item label="设备类型"><el-select v-model="form.type" style="width:100%"><el-option v-for="item in DEVICE_TYPES" :key="item" :label="item" :value="item"/></el-select></el-form-item><el-form-item label="所属地块"><el-select v-model="form.plotNo" style="width:100%" placeholder="请选择所属地块"><el-option v-for="item in plots" :key="item.plotNo" :label="`${item.farmName || item.farmId} · ${item.plotNo} · ${item.name}`" :value="item.plotNo"/></el-select></el-form-item></el-form><template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template></el-dialog>

    <el-dialog v-model="bindDialog" title="绑定设备" width="460px"><el-alert title="换绑或解绑不会删除设备已经产生的历史数据" type="warning" :closable="false" show-icon/><el-form label-position="top" class="bind-form"><el-form-item label="目标地块"><el-select v-model="form.plotNo" style="width:100%"><el-option v-for="item in plots" :key="item.plotNo" :label="`${item.farmName || item.farmId} · ${item.plotNo} · ${item.name}`" :value="item.plotNo"/></el-select></el-form-item></el-form><template #footer><el-button @click="bindDialog=false">取消</el-button><el-button type="primary" @click="saveBind">确认绑定</el-button></template></el-dialog>

    <el-dialog v-model="importDialog" title="Excel 批量导入设备" width="760px" class="import-dialog">
      <input ref="importInput" class="file-input" type="file" accept=".xlsx" @change="readExcel">
      <div class="import-guide">
        <div class="import-icon"><el-icon><DocumentAdd/></el-icon></div>
        <div><strong>{{ importFileName || '选择设备 Excel 文件' }}</strong><p>必填列：设备编号、设备 UUID、设备类型、所属地块</p></div>
        <el-button @click="selectImportFile">选择文件</el-button>
        <el-button link type="primary" @click="downloadTemplate">下载模板</el-button>
      </div>
      <el-alert title="设备类型仅支持：温度传感器、湿度传感器、灌溉设备。无效行不会被导入。" type="info" :closable="false" show-icon/>
      <el-table v-if="importRows.length" :data="importRows" max-height="330" class="import-preview">
        <el-table-column prop="rowNumber" label="行号" width="70"/>
        <el-table-column prop="deviceNo" label="设备编号" min-width="130"/>
        <el-table-column prop="deviceUuid" label="设备 UUID" min-width="280"/>
        <el-table-column prop="type" label="设备类型" min-width="120"/>
        <el-table-column prop="plotNo" label="所属地块" width="110"><template #default="scope">{{ scope.row.plotNo || '未绑定' }}</template></el-table-column>
        <el-table-column label="校验结果" min-width="180"><template #default="scope"><el-tag :type="scope.row.valid ? 'success' : 'danger'" effect="plain">{{ scope.row.valid ? '可导入' : scope.row.error }}</el-tag></template></el-table-column>
      </el-table>
      <template #footer><span class="import-count">{{ importRows.length ? `共 ${importRows.length} 行，${validImportCount} 行可导入` : '' }}</span><el-button @click="importDialog=false">取消</el-button><el-button type="primary" :loading="importing" :disabled="!validImportCount" @click="confirmImport">确认导入</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.device-table{margin-bottom:18px}.toolbar{display:flex;gap:10px;margin-bottom:18px}.toolbar .el-input{width:300px}.toolbar .el-select{width:170px}.heartbeat-value{font-size:14px!important;white-space:nowrap}.bind-form{margin-top:18px}.file-input{display:none}.import-guide{display:flex;align-items:center;gap:12px;margin-bottom:14px;padding:16px;border:1px dashed #b9d5c7;border-radius:13px;background:#f6fbf8}.import-guide>div:nth-child(2){min-width:0;flex:1}.import-guide strong,.import-guide p{display:block;margin:0}.import-guide strong{color:#315347}.import-guide p{margin-top:5px;color:#84958e;font-size:12px}.import-icon{width:42px;height:42px;display:grid;place-items:center;flex:0 0 42px;border-radius:12px;color:#27835d;background:#e2f3ea;font-size:21px}.import-preview{margin-top:14px}.import-count{margin-right:auto;color:#678078;font-size:12px}:deep(.el-dialog__footer){display:flex;align-items:center}@media(max-width:650px){.toolbar{flex-direction:column}.toolbar .el-input,.toolbar .el-select{width:100%}.import-guide{align-items:flex-start;flex-wrap:wrap}.page-actions{width:100%}.page-actions .el-button{flex:1;margin:0}}
</style>
