<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createFarmArchive, getFarmArchives, updateFarmArchive } from '@/api/adminPhase2'

const rows=ref([]);const dialog=ref(false);const editing=ref('');const form=reactive({farmName:'',province:'重庆市',city:'奉节县',address:'',areaMu:null,adminUserId:null,remark:'',status:'ACTIVE'})
async function load(){rows.value=await getFarmArchives()}
function open(row){editing.value=row?.id||'';Object.assign(form,row||{farmName:'',province:'重庆市',city:'奉节县',address:'',areaMu:null,adminUserId:null,remark:'',status:'ACTIVE'});dialog.value=true}
async function save(){if(editing.value)await updateFarmArchive(editing.value,form);else await createFarmArchive(form);dialog.value=false;await load();ElMessage.success('橙园档案已保存')}
onMounted(load)
</script>
<template><div class="farmer-page"><div class="page-head"><div><h1 class="page-title">橙园档案</h1><p class="page-subtitle">由系统管理员统一建立、编辑和停用橙园。</p></div><el-button type="primary" @click="open()">新增橙园</el-button></div><section class="content-panel"><el-table :data="rows"><el-table-column prop="id" label="编号" width="90"/><el-table-column prop="farmName" label="橙园名称"/><el-table-column label="地区"><template #default="s">{{s.row.province}} {{s.row.city}}</template></el-table-column><el-table-column prop="areaMu" label="面积（亩）"/><el-table-column prop="status" label="状态" width="100"/><el-table-column label="操作" width="100"><template #default="s"><el-button link type="primary" @click="open(s.row)">编辑</el-button></template></el-table-column></el-table></section><el-dialog v-model="dialog" :title="editing?'编辑橙园':'新增橙园'" width="600px"><el-form label-width="90px"><el-form-item label="名称"><el-input v-model="form.farmName"/></el-form-item><el-form-item label="省 / 市"><div class="inline"><el-input v-model="form.province"/><el-input v-model="form.city"/></div></el-form-item><el-form-item label="地址"><el-input v-model="form.address"/></el-form-item><el-form-item label="面积"><el-input-number v-model="form.areaMu" :min="0"/></el-form-item><el-form-item label="状态"><el-switch v-model="form.status" active-value="ACTIVE" inactive-value="INACTIVE" active-text="启用" inactive-text="停用"/></el-form-item><el-form-item label="备注"><el-input v-model="form.remark" type="textarea"/></el-form-item></el-form><template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></template></el-dialog></div></template>
<style scoped>.inline{display:grid;grid-template-columns:1fr 1fr;gap:10px;width:100%}</style>
