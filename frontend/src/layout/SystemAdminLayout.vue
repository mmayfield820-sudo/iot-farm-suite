<script setup>
import { computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import { usePlatformStore } from '@/stores/platform'
const platformStore = usePlatformStore()
onMounted(() => platformStore.loadData().catch(() => ElMessage.error(platformStore.loadError || '平台数据加载失败')))
const menu = [
  { label: '运行概况', path: '/admin/dashboard', icon: 'DataBoard' },
  { label: '全局告警', path: '/admin/alerts', icon: 'Warning' },
  { label: '用户管理', path: '/admin/users', icon: 'UserFilled' },
  { label: '橙园档案', path: '/admin/farm-archives', icon: 'OfficeBuilding' },
  { label: '地块档案', path: '/admin/plot-archives', icon: 'MapLocation' },
  { label: '员工导入', path: '/admin/employees', icon: 'UploadFilled' },
  { label: '管理模板', path: '/admin/cultivation-templates', icon: 'Collection' },
  { label: '系统参数', path: '/admin/settings', icon: 'Setting' },
  { label: '操作日志', path: '/admin/logs', icon: 'Document' },
]
const contextStatus = computed(() => platformStore.loadError ? '数据加载异常' : platformStore.offlineDevices || platformStore.unhandledAlerts ? '存在待处理事项' : '运行正常')
</script>
<template><AppShell title="橙心如意" subtitle="SYSTEM ADMIN" context-label="脐橙平台运行中心" :context-status="contextStatus" :context-status-tone="contextStatus === '运行正常' ? 'success' : 'warning'" :menu="menu" accent="#c85f18" /></template>
