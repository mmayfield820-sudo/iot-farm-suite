<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { completeFarmTask, createTemporaryTask, getCalendarTasks, getTodayTasks, getUpcomingTasks } from '@/api/farmTask'
import { useFarmerStore } from '@/stores/farmer'

const store = useFarmerStore()
const calendarDate = ref(new Date())
const calendarRows = ref([])
const todoRows = ref([])
const todoTab = ref('today')
const calendarLoading = ref(false)
const todoLoading = ref(false)
const temporaryVisible = ref(false)
const completeVisible = ref(false)
const currentTask = ref(null)
const tempForm = reactive({ plotId: '', taskType: 'PATROL', taskName: '', plannedDate: '', taskNote: '' })
const completeForm = reactive({ completionNote: '', irrigationRecordId: null })

const pad = (value) => String(value).padStart(2, '0')
const dateKey = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
const monthKey = computed(() => dateKey(calendarDate.value).slice(0, 7))
const calendarTitle = computed(() => `${calendarDate.value.getFullYear()} 年 ${calendarDate.value.getMonth() + 1} 月`)
const tasksByDate = computed(() => calendarRows.value.reduce((result, task) => {
  if (!result[task.plannedDate]) result[task.plannedDate] = []
  result[task.plannedDate].push(task)
  return result
}, {}))
const visibleTodos = computed(() => todoRows.value.filter((task) => !store.selectedPlotId || task.plotId === store.selectedPlotId))
const statusLabels = { PENDING: '待执行', OVERDUE: '已逾期', COMPLETED: '已完成', CANCELLED: '已取消', SUPERSEDED: '已替代' }
const typeLabels = { PATROL: '巡园', IRRIGATION: '灌溉', FERTILIZATION: '施肥', PRUNING: '修剪', PEST_CONTROL: '病虫害防治', WEEDING: '除草', HARVEST: '采收', OTHER: '其他农事' }

const dayTasks = (day) => tasksByDate.value[day] || []
const isToday = (day) => day === dateKey(new Date())

function changeMonth(offset) {
  const current = calendarDate.value
  calendarDate.value = new Date(current.getFullYear(), current.getMonth() + offset, 1)
}

function goToday() {
  calendarDate.value = new Date()
}

function noteTone(task) {
  if (task.taskStatus === 'OVERDUE') return 'rose'
  return { IRRIGATION: 'blue', FERTILIZATION: 'green', PEST_CONTROL: 'orange', PRUNING: 'purple' }[task.taskType] || 'yellow'
}

async function loadCalendar() {
  if (!store.selectedPlotId) return
  calendarLoading.value = true
  try { calendarRows.value = await getCalendarTasks(monthKey.value, store.selectedPlotId) }
  catch (error) { ElMessage.error(error.message || '农事日历加载失败') }
  finally { calendarLoading.value = false }
}

async function loadTodos() {
  todoLoading.value = true
  try { todoRows.value = todoTab.value === 'today' ? await getTodayTasks() : await getUpcomingTasks(7) }
  catch (error) { ElMessage.error(error.message || '待办任务加载失败') }
  finally { todoLoading.value = false }
}

function openTemporary() {
  Object.assign(tempForm, { plotId: store.selectedPlotId, taskType: 'PATROL', taskName: '', plannedDate: dateKey(new Date()), taskNote: '' })
  temporaryVisible.value = true
}

async function saveTemporary() {
  try {
    await createTemporaryTask(tempForm)
    temporaryVisible.value = false
    store.touchTimeline()
    ElMessage.success('临时农事已记录')
    await Promise.all([loadCalendar(), loadTodos()])
  } catch (error) { ElMessage.error(error.message || '保存失败') }
}

function openComplete(task) {
  currentTask.value = task
  Object.assign(completeForm, { completionNote: '', irrigationRecordId: null })
  completeVisible.value = true
}

async function complete() {
  try {
    await completeFarmTask(currentTask.value.taskId, { completedAt: new Date().toISOString(), ...completeForm })
    completeVisible.value = false
    store.touchTimeline()
    ElMessage.success('农事任务已完成')
    await Promise.all([loadCalendar(), loadTodos()])
  } catch (error) { ElMessage.error(error.message || '完成任务失败') }
}

watch([monthKey, () => store.selectedPlotId], loadCalendar, { immediate: true })
watch(todoTab, loadTodos, { immediate: true })
</script>

<template>
  <div class="farmer-page calendar-page">
    <div class="page-head">
      <div><h1 class="page-title">农事日历</h1><p class="page-subtitle">在月历中查看农事安排，并集中处理近期待办。</p></div>
      <el-select :model-value="store.selectedPlotId" class="plot-select" @change="store.selectPlot"><el-option v-for="plot in store.accessiblePlots" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" /></el-select>
    </div>

    <div class="calendar-layout">
      <section v-loading="calendarLoading" class="calendar-board">
        <el-calendar v-model="calendarDate">
          <template #header>
            <div class="calendar-head"><div><span>橙园农事月历</span><strong>{{ calendarTitle }}</strong></div><div><el-button text @click="changeMonth(-1)">上个月</el-button><el-button text @click="goToday">回到今天</el-button><el-button text @click="changeMonth(1)">下个月</el-button></div></div>
          </template>
          <template #date-cell="{ data }">
            <el-popover trigger="click" placement="right-start" :width="360" :disabled="!dayTasks(data.day).length">
              <div class="day-detail">
                <div class="day-detail-head"><div><span>当日农事安排</span><strong>{{ data.day }}</strong></div><em>共 {{ dayTasks(data.day).length }} 项</em></div>
                <div class="day-detail-list">
                  <article v-for="task in dayTasks(data.day)" :key="task.taskId" :class="['day-detail-task', noteTone(task)]">
                    <div><span>{{ typeLabels[task.taskType] || task.taskType }}</span><em>{{ statusLabels[task.taskStatus] || task.taskStatus }}</em></div>
                    <strong>{{ task.taskName }}</strong>
                    <p>{{ task.taskNote || '按管理计划完成本项农事，并记录现场情况。' }}</p>
                    <el-button v-if="['PENDING','OVERDUE'].includes(task.taskStatus)" link type="primary" @click="openComplete(task)">标记完成</el-button>
                  </article>
                </div>
              </div>
              <template #reference>
                <div class="calendar-cell" :class="{ today: isToday(data.day), actionable: dayTasks(data.day).length }">
                  <span class="day-number">{{ Number(data.day.slice(-2)) }}</span>
                  <div class="day-tasks">
                    <span v-for="task in dayTasks(data.day).slice(0, 2)" :key="task.taskId" :class="['calendar-task', noteTone(task)]">{{ task.taskName }}</span>
                    <small v-if="dayTasks(data.day).length > 2">另有 {{ dayTasks(data.day).length - 2 }} 项</small>
                  </div>
                </div>
              </template>
            </el-popover>
          </template>
        </el-calendar>
      </section>

      <aside class="todo-board">
        <div class="todo-head"><div><span>近期农事</span><strong>{{ todoTab === 'today' ? '今日待办' : '未来七天' }}</strong></div><el-button link type="primary" @click="openTemporary">＋ 临时农事</el-button></div>
        <div class="todo-tabs"><button :class="{ active: todoTab === 'today' }" @click="todoTab = 'today'">今日</button><button :class="{ active: todoTab === 'upcoming' }" @click="todoTab = 'upcoming'">未来七天</button></div>
        <div v-loading="todoLoading" class="notes-list">
          <article v-for="task in visibleTodos" :key="task.taskId" :class="['sticky-note', noteTone(task)]">
            <div class="note-pin"></div>
            <div class="note-meta"><span>{{ typeLabels[task.taskType] || task.taskType }}</span><time>{{ task.plannedDate }}</time></div>
            <h3>{{ task.taskName }}</h3>
            <p>{{ task.taskNote || '按管理计划完成本项农事，并记录现场情况。' }}</p>
            <div class="note-footer"><span>{{ statusLabels[task.taskStatus] || task.taskStatus }}</span><el-button link type="primary" @click="openComplete(task)">标记完成</el-button></div>
          </article>
          <div v-if="!todoLoading && !visibleTodos.length" class="empty-notes">当前没有需要处理的农事</div>
        </div>
      </aside>
    </div>

    <el-dialog v-model="temporaryVisible" title="记录临时农事" width="520px"><el-form label-position="top"><el-form-item label="地块"><el-select v-model="tempForm.plotId" style="width:100%"><el-option v-for="plot in store.accessiblePlots" :key="plot.plotId" :label="plot.plotName" :value="plot.plotId" /></el-select></el-form-item><el-form-item label="任务名称"><el-input v-model="tempForm.taskName" /></el-form-item><el-form-item label="任务类型"><el-select v-model="tempForm.taskType" style="width:100%"><el-option label="巡园检查" value="PATROL" /><el-option label="灌溉" value="IRRIGATION" /><el-option label="施肥" value="FERTILIZATION" /><el-option label="整形修剪" value="PRUNING" /><el-option label="病虫害防治" value="PEST_CONTROL" /><el-option label="其他农事" value="OTHER" /></el-select></el-form-item><el-form-item label="日期"><el-date-picker v-model="tempForm.plannedDate" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item><el-form-item label="备注"><el-input v-model="tempForm.taskNote" type="textarea" :rows="3" /></el-form-item></el-form><template #footer><el-button @click="temporaryVisible=false">取消</el-button><el-button type="primary" @click="saveTemporary">保存</el-button></template></el-dialog>
    <el-dialog v-model="completeVisible" title="完成农事任务" width="480px"><p class="complete-task-name">{{ currentTask?.taskName }}</p><el-input v-model="completeForm.completionNote" type="textarea" :rows="4" placeholder="填写完成情况、用量或现场说明" /><template #footer><el-button @click="completeVisible=false">取消</el-button><el-button type="primary" @click="complete">确认完成</el-button></template></el-dialog>
  </div>
</template>

<style scoped>
.page-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:18px}.plot-select{width:250px}.calendar-layout{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:20px;align-items:start}.calendar-board{overflow:hidden;border:1px solid rgba(226,194,169,.72);border-radius:20px;background:rgba(255,253,250,.78);box-shadow:0 14px 34px rgba(111,60,27,.06)}.calendar-board :deep(.el-calendar){background:transparent}.calendar-board :deep(.el-calendar__header){padding:18px 22px 14px;border-bottom:1px solid rgba(235,214,197,.78)}.calendar-board :deep(.el-calendar__body){padding:10px 14px 18px}.calendar-board :deep(.el-calendar-table th){padding:9px;color:#9a765e;font-size:12px;font-weight:600}.calendar-board :deep(.el-calendar-table td){border-color:rgba(236,220,207,.72)}.calendar-board :deep(.el-calendar-day){height:104px;padding:5px}.calendar-board :deep(.el-calendar-table td.is-selected){background:#fff6eb}.calendar-head{width:100%;display:flex;align-items:center;justify-content:space-between;gap:16px}.calendar-head>div:first-child{display:flex;flex-direction:column;gap:3px}.calendar-head span{color:#ad6b3d;font-size:11px;letter-spacing:.08em}.calendar-head strong{color:#4d2b18;font-size:20px}.calendar-cell{height:100%;position:relative}.day-number{width:25px;height:25px;display:grid;place-items:center;border-radius:50%;color:#765744;font-size:12px}.calendar-cell.today .day-number{color:#fff;background:#dc6d20}.day-tasks{display:grid;gap:3px;margin-top:4px}.calendar-task{overflow:hidden;padding:3px 5px;border-left:2px solid #df8d4e;border-radius:3px;color:#74513a;background:rgba(255,229,186,.64);font-size:9px;text-overflow:ellipsis;white-space:nowrap}.calendar-task.blue{border-color:#6ea8db;background:rgba(214,234,251,.7)}.calendar-task.green{border-color:#6fae85;background:rgba(219,239,224,.72)}.calendar-task.rose{border-color:#d77979;background:rgba(249,220,220,.72)}.calendar-task.purple{border-color:#a68ac4;background:rgba(235,225,247,.72)}.day-tasks small{color:#a58c7b;font-size:8px}.todo-board{min-height:620px;padding:18px;border:1px solid rgba(226,194,169,.6);border-radius:20px;background:linear-gradient(150deg,rgba(255,250,237,.88),rgba(255,245,224,.72));box-shadow:0 14px 34px rgba(111,60,27,.06)}.todo-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.todo-head>div{display:flex;flex-direction:column;gap:3px}.todo-head span{color:#b0784f;font-size:11px}.todo-head strong{color:#4d2b18;font-size:21px}.todo-tabs{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:15px 0}.todo-tabs button{padding:8px;border:0;border-radius:10px;color:#92705a;background:rgba(255,255,255,.58);cursor:pointer}.todo-tabs button.active{color:#fff;background:#d86a1e;box-shadow:0 5px 12px rgba(216,106,30,.18)}.notes-list{display:grid;gap:13px;max-height:580px;overflow-y:auto;padding:5px 4px 10px}.sticky-note{position:relative;padding:17px 16px 13px;border-radius:4px 4px 13px 4px;background:linear-gradient(145deg,#fff4b9,#f7e58e);box-shadow:0 8px 15px rgba(100,71,26,.12);transform:rotate(-.35deg)}.sticky-note:nth-child(even){transform:rotate(.45deg)}.sticky-note.blue{background:linear-gradient(145deg,#e9f5ff,#cfe8fa)}.sticky-note.green{background:linear-gradient(145deg,#edf8e9,#d6eccd)}.sticky-note.rose{background:linear-gradient(145deg,#fff0ee,#f6d2d0)}.sticky-note.orange{background:linear-gradient(145deg,#fff1dc,#f7d7ad)}.sticky-note.purple{background:linear-gradient(145deg,#f4effb,#dfd3ee)}.note-pin{width:8px;height:8px;position:absolute;top:7px;left:50%;border-radius:50%;background:#d55d43;box-shadow:0 2px 4px rgba(84,38,25,.24)}.note-meta,.note-footer{display:flex;align-items:center;justify-content:space-between;gap:12px}.note-meta{color:#8e745e;font-size:10px}.sticky-note h3{margin:8px 0 5px;color:#4e3523;font-size:15px}.sticky-note p{margin:0;color:#7b6656;font-size:11px;line-height:1.55}.note-footer{margin-top:11px;padding-top:8px;border-top:1px dashed rgba(113,80,48,.18);color:#98715a;font-size:10px}.empty-notes{padding:70px 10px;color:#a88f7c;font-size:12px;text-align:center}.complete-task-name{color:#5a3822;font-weight:700}@media(max-width:1150px){.calendar-layout{grid-template-columns:1fr}.todo-board{min-height:auto}.notes-list{grid-template-columns:repeat(2,minmax(0,1fr));max-height:none}}@media(max-width:720px){.page-head{flex-direction:column}.plot-select{width:100%}.calendar-head{align-items:flex-start;flex-direction:column}.calendar-board :deep(.el-calendar-day){height:84px}.calendar-task{max-width:76px}.notes-list{grid-template-columns:1fr}}
.calendar-layout{grid-template-columns:minmax(0,1.25fr) minmax(330px,.75fr);align-items:stretch}
.calendar-board,.todo-board{height:100%;box-sizing:border-box}
.calendar-cell.actionable{cursor:pointer}.calendar-cell.actionable:hover{background:rgba(255,243,227,.72)}
.day-detail{max-height:430px;overflow:hidden}.day-detail-head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:12px;border-bottom:1px solid rgba(226,194,169,.6)}.day-detail-head>div{display:flex;flex-direction:column;gap:3px}.day-detail-head span,.day-detail-head em{color:#a67a5d;font-size:11px;font-style:normal}.day-detail-head strong{color:#4d2b18;font-size:17px}.day-detail-list{display:grid;gap:10px;max-height:350px;overflow-y:auto;padding:12px 3px 2px}.day-detail-task{padding:12px 13px;border-left:3px solid #df9b52;border-radius:8px;background:#fff8ec}.day-detail-task.blue{border-color:#6ea8db;background:#f1f8fe}.day-detail-task.green{border-color:#6fae85;background:#f1f9f3}.day-detail-task.rose{border-color:#d77979;background:#fff3f3}.day-detail-task.purple{border-color:#a68ac4;background:#f7f2fb}.day-detail-task.orange{border-color:#df8d4e;background:#fff6ea}.day-detail-task>div{display:flex;align-items:center;justify-content:space-between;gap:12px;color:#9a755d;font-size:10px}.day-detail-task>div em{font-style:normal}.day-detail-task>strong{display:block;margin-top:7px;color:#52331f;font-size:14px}.day-detail-task p{margin:5px 0 0;color:#7c6859;font-size:11px;line-height:1.55}.day-detail-task .el-button{margin-top:5px;padding:0}
@media(max-width:1150px){.calendar-layout{grid-template-columns:1fr}.calendar-board,.todo-board{height:auto}}
</style>
