<script setup>
defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ['completed', 'pending', 'overdue'].includes(value),
  },
})
</script>

<template>
  <svg v-if="type === 'completed'" viewBox="0 0 32 32" aria-hidden="true">
    <path d="M11.5 7.5H8.8A2.8 2.8 0 0 0 6 10.3v14.9A2.8 2.8 0 0 0 8.8 28h14.4a2.8 2.8 0 0 0 2.8-2.8V10.3a2.8 2.8 0 0 0-2.8-2.8h-2.7" />
    <path d="M12 5h8c.7 0 1.3.6 1.3 1.3v3.2H10.7V6.3C10.7 5.6 11.3 5 12 5Z" />
    <path d="m11 18 3.3 3.3 7.3-7.3" />
  </svg>
  <svg v-else-if="type === 'pending'" viewBox="0 0 32 32" aria-hidden="true">
    <path d="M6 8.5h20v19H6zM10.5 4.5v7M21.5 4.5v7M6 13h20" />
    <path d="M10.5 18h2M15 18h2M19.5 18h2M10.5 22.5h2M15 22.5h2M19.5 22.5h2" />
  </svg>
  <svg v-else viewBox="0 0 32 32" aria-hidden="true">
    <circle cx="16" cy="16" r="11" />
    <path d="M16 9.5v8.8M16 23h.01" />
  </svg>
</template>

<style scoped>
svg{width:1em;height:1em;overflow:visible;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
</style>
