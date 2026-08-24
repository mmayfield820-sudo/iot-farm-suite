<script setup>
defineProps({ title:String, description:String, icon:{type:String,default:'🌱'}, items:Array })
</script>
<template><div><h1 class="page-title">{{ title }}</h1><p class="page-subtitle">{{ description }}</p><section class="placeholder-page panel"><div><span class="big-icon">{{ icon }}</span><h2>页面框架已就绪</h2><p>该模块已接入农户独立路由，后续可在本文件中继续开发，不会影响其他角色模块。</p><div class="chips"><span v-for="item in items" :key="item">{{ item }}</span></div></div></section></div></template>
<style scoped>.big-icon{font-size:54px}.chips{display:flex;justify-content:center;flex-wrap:wrap;gap:8px;margin-top:20px}.chips span{padding:7px 11px;border-radius:18px;color:#267b58;background:#eaf7f0;font-size:12px}</style>
