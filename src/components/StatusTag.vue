<script setup>defineProps({ status:String })</script>
<template><span :class="['status',status]"><i></i>{{ status === 'online' ? '在线' : status === 'standby' ? '待机' : '离线' }}</span></template>
<style scoped>.status{display:inline-flex;align-items:center;gap:6px;font-size:12px}.status i{width:7px;height:7px;border-radius:50%;background:#9aa6a1}.online{color:#288b61}.online i{background:#36af78}.standby{color:#b88225}.standby i{background:#dfaa4a}</style>
