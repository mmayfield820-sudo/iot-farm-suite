<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { completeFarmTask, createTemporaryTask, getTodayTasks, getUpcomingTasks, updateFarmTask } from '@/api/farmTask'
import { useFarmerStore } from '@/stores/farmer'
import { FARM_TASK_TYPES, farmTaskTypeLabel } from '@/utils/farmTask'

const store = useFarmerStore()
const tab = ref('today')
const rows = ref([])
const loading = ref(false)
const temporaryVisible = ref(false)
const completeVisible = ref(false)
const currentTask = ref(null)
const tempForm = reactive({ plotId: '', taskType: 'PATROL', taskName: '', plannedDate: '', taskNote: '' })
const completeForm = reactive({ completionNote: '', irrigationRecordId: null })

async function load() { loading.value = true; try { rows.value = tab.value === 'today' ? await getTodayTasks() : await getUpcomingTasks(7) } catch (error) { ElMessage.error(error.message || '任务加载失败') } finally { loading.value = false } }
function openTemporary() { Object.assign(tempForm, { plotId: store.selectedPlotId, taskType: 'PATROL', taskName: '', plannedDate: new Date().toISOString().slice(0, 10), taskNote: '' }); temporaryVisible.value = true }
async function saveTemporary() { try { await createTemporaryTask(tempForm); temporaryVisible.value = false; ElMessage.success('临时农事已记录'); await load() } catch (error) { ElMessage.error(error.message || '保存失败') } }
function openComplete(row) { currentTask.value = row; Object.assign(completeForm, { completionNote: '', irrigationRecordId: null }); completeVisible.value = true }
async function complete() { try { await completeFarmTask(currentTask.value.taskId, { completedAt: new Date().toISOString(), ...completeForm }); completeVisible.value = false; ElMessage.success('任务已完成'); await load() } catch (error) { ElMessage.error(error.message || '完成任务失败') } }
async function changeDate(row, value) { try { await updateFarmTask(row.taskId, { plannedDate: value }); ElMessage.success('计划日期已调整'); await load() } catch (error) { ElMessage.error(error.message || '调整失败') } }
onMounted(load)
</script>

<template>
  <div class="farmer-page"><div class="page-head"><div><h1 class="page-title">今日待办</h1><p class="page-subtitle">处理今日任务，并查看未来 7 天安排。</p></div><el-button type="primary" @click="openTemporary">记录临时农事</el-button></div>
    <el-card shadow="never"><el-tabs v-model="tab" @tab-change="load"><el-tab-pane label="今日" name="today" /><el-tab-pane label="未来 7 天" name="upcoming" /></el-tabs><el-table v-loading="loading" :data="rows"><el-table-column prop="plannedDate" label="计划日期" width="160"><template #default="{row}"><el-date-picker :model-value="row.plannedDate" type="date" value-format="YYYY-MM-DD" size="small" @change="changeDate(row,$event)" /></template></el-table-column><el-table-column prop="taskName" label="任务" min-width="220" /><el-table-column label="类型" width="170"><template #default="{ row }">{{ farmTaskTypeLabel(row.taskType) }}</template></el-table-column><el-table-column prop="taskSource" label="来源" width="110" /><el-table-column prop="taskStatus" label="状态" width="110" /><el-table-column label="操作" width="100"><template #default="{row}"><el-button link type="primary" @click="openComplete(row)">完成</el-button></template></el-table-column></el-table></el-card>
    <el-dialog v-model="temporaryVisible" title="记录临时农事" width="520px"><el-form label-position="top"><el-form-item label="地块"><el-select v-model="tempForm.plotId" style="width:100%"><el-option v-for="plot in store.accessiblePlots" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" /></el-select></el-form-item><el-form-item label="任务名称"><el-input v-model="tempForm.taskName" /></el-form-item><el-form-item label="任务类型"><el-select v-model="tempForm.taskType" style="width:100%"><el-option v-for="item in FARM_TASK_TYPES" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item><el-form-item label="日期"><el-date-picker v-model="tempForm.plannedDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item><el-form-item label="备注"><el-input v-model="tempForm.taskNote" type="textarea" /></el-form-item></el-form><template #footer><el-button @click="temporaryVisible=false">取消</el-button><el-button type="primary" @click="saveTemporary">保存</el-button></template></el-dialog>
    <el-dialog v-model="completeVisible" title="完成任务" width="480px"><p>{{ currentTask?.taskName }}</p><el-input v-model="completeForm.completionNote" type="textarea" :rows="4" placeholder="填写完成情况" /><template #footer><el-button @click="completeVisible=false">取消</el-button><el-button type="primary" @click="complete">确认完成</el-button></template></el-dialog>
  </div>
</template>

<style scoped>.page-head{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px}</style>
