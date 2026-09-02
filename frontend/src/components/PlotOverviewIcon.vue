<script setup>
defineProps({ type: { type: String, required: true } })
</script>

<template>
  <svg v-if="type === 'area'" viewBox="0 0 32 32" aria-hidden="true"><path d="M5 7.5h22v19H5zM9 22l4-5 3 2 6-7M7 7.5V5m18 2.5V5M7 26.5V29m18-2.5V29" /></svg>
  <svg v-else-if="type === 'management'" viewBox="0 0 32 32" aria-hidden="true"><path d="M14.5 14.5c-4.8.3-7.2-2-7-6.9 4.9-.2 7.3 2.2 7 6.9ZM17.5 14.5c-.3-4.7 2-7.1 6.9-6.9.2 4.9-2.2 7.2-6.9 6.9ZM14.5 17.5c.3 4.7-2 7.1-6.9 6.9-.2-4.9 2.2-7.2 6.9-6.9ZM17.5 17.5c4.8-.3 7.2 2 7 6.9-4.9.2-7.3-2.2-7-6.9Z" /></svg>
  <svg v-else-if="type === 'farming'" class="farming" viewBox="0 0 32 32" aria-hidden="true">
    <path d="M15.1 27.8c.2-5.2 1.3-9.2 3.8-12.5 1.7-2.2 3.5-3.7 5.8-5.1" />
    <path d="M17.3 17.3c-5.4.4-9.2-2.2-10.1-7.2 5.2-.7 9.2 2 10.1 7.2Z" />
    <path d="M18.2 13.7c-.3-5.1 2.5-8.5 7.4-9.2.5 4.9-2.4 8.5-7.4 9.2Z" />
    <path d="M14.8 23.8c-4.3.3-7.4-1.8-8.1-5.7 4.2-.5 7.4 1.6 8.1 5.7Z" />
  </svg>
  <svg v-else-if="type === 'location'" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 27V13M16 17c-5.6 0-9-3-9-8 5.6 0 9 3 9 8ZM16 13c0-4.9 3-7.5 8-7.5 0 4.9-3 7.5-8 7.5ZM9 27h14" /></svg>
  <svg v-else-if="type === 'irrigation'" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 4S8 14.1 8 20a8 8 0 0 0 16 0C24 14.1 16 4 16 4Z" /><path d="M12 21.5a4.3 4.3 0 0 0 2.2 2.4" /></svg>
  <svg v-else-if="type === 'moisture'" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 4S8 14.1 8 20a8 8 0 0 0 16 0C24 14.1 16 4 16 4Z" /><path d="m12.5 21 7-7M13 14.5h.01M19 21h.01" /></svg>
  <svg v-else-if="type === 'temperature'" viewBox="0 0 32 32" aria-hidden="true"><path d="M13 18.3V7a3 3 0 0 1 6 0v11.3a6 6 0 1 1-6 0Z" /><path d="M16 11v11M21.5 8H25M21.5 13H24" /></svg>
  <svg v-else-if="type === 'irrigation-status'" viewBox="0 0 32 32" aria-hidden="true"><path d="M6 13h11v8H6zM17 15h4M10 13V9h4v4M9 25h5M22 13c2.8 2.8 4.2 5.2 4.2 7.2a4.2 4.2 0 0 1-8.4 0c0-2 1.4-4.4 4.2-7.2Z" /></svg>
  <svg v-else-if="type === 'stage'" viewBox="0 0 32 32" aria-hidden="true"><path d="M13 28v-8H9.5A5.5 5.5 0 0 1 7 9.6 6 6 0 0 1 18.2 7 5.5 5.5 0 0 1 25 12.4a5.5 5.5 0 0 1-2.5 10.4H19V28M10 28h12M16 10v13M12.5 14.5 16 18l3.5-3.5" /></svg>
  <svg v-else-if="type === 'planting'" viewBox="0 0 32 32" aria-hidden="true"><path d="M6 8h20v20H6zM10 4v7M22 4v7M6 13h20M11 19h4M11 23h8" /></svg>
  <svg v-else viewBox="0 0 32 32" aria-hidden="true"><path d="M13 28v-7.2A7 7 0 0 1 9.2 8.1 7 7 0 0 1 22 10a6.5 6.5 0 0 1-.8 12.9H19V28M10 28h12M16 12v16M12 17l4 4 4-4" /></svg>
</template>

<style scoped>
svg{width:1em;height:1em;overflow:visible;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
svg.farming{stroke-width:2.5}
</style>
