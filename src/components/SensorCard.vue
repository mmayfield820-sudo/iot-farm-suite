<script setup>
import * as Icons from '@element-plus/icons-vue'
defineProps({ item: Object })
</script>
<template>
  <div class="sensor-card panel"><div :class="['sensor-icon', item.tone]"><el-icon><component :is="Icons[item.icon]" /></el-icon></div><div><p>{{ item.label }}</p><strong>{{ item.value }}<small>{{ item.unit }}</small></strong><span>较昨日 <b>状态稳定</b></span></div></div>
</template>
<style scoped>
.sensor-card { padding:20px; display:flex; align-items:center; gap:15px; }.sensor-icon { width:48px; height:48px; display:grid; place-items:center; flex:0 0 auto; border-radius:14px; font-size:23px; }.orange{background:#fff0e4;color:#e37a2f}.blue{background:#e5f2ff;color:#3988ca}.yellow{background:#fff8dc;color:#c99016}.green{background:#e5f7ee;color:#2c9b68}.sensor-card p{margin:0 0 5px;color:#6c7e77;font-size:13px}.sensor-card strong{display:block;font-size:25px}.sensor-card small{margin-left:3px;font-size:12px;font-weight:500;color:#75857f}.sensor-card span{font-size:11px;color:#9aa6a1}.sensor-card b{color:#3b9b71;font-weight:500}
</style>
