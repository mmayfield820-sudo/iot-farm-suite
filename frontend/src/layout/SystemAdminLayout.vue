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
  { label: '系统参数', path: '/admin/settings', icon: 'Setting' },
  { label: '操作日志', path: '/admin/logs', icon: 'Document' },
]
const contextStatus = computed(() => platformStore.loadError ? '数据加载异常' : platformStore.offlineDevices || platformStore.unhandledAlerts ? '存在待处理事项' : '运行正常')
</script>
<template><AppShell title="系统管理平台" subtitle="SYSTEM ADMIN" context-label="全系统运行中心" :context-status="contextStatus" :context-status-tone="contextStatus === '运行正常' ? 'success' : 'warning'" :menu="menu" accent="#6b5bb5" /></template>
