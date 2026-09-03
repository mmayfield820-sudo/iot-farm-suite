<script setup>
import { computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppShell from '@/components/AppShell.vue'
import { usePlatformStore } from '@/stores/platform'
const platformStore = usePlatformStore()
onMounted(() => platformStore.loadData().catch(() => ElMessage.error(platformStore.loadError || '平台数据加载失败')))
const menu = [
  { label: '基础档案', path: '/admin/archives', icon: 'FolderOpened' },
  { label: '全局告警', path: '/admin/alerts', icon: 'Warning' },
  { label: '用户管理', path: '/admin/users', icon: 'UserFilled' },
  { label: '品种模板', path: '/admin/templates', icon: 'CollectionTag' },
  { label: '操作日志', path: '/admin/logs', icon: 'Document' },
]
const contextStatus = computed(() => platformStore.loadError ? '数据加载异常' : '档案数据已同步')
</script>
<template><AppShell title="橙心如意" subtitle="智慧农业管理平台" context-label="平台基础资料" :context-status="contextStatus" :context-status-tone="contextStatus === '档案数据已同步' ? 'success' : 'warning'" :menu="menu" accent="#6b5bb5" /></template>
