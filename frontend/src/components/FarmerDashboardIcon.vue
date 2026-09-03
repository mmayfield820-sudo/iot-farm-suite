<script setup>
defineProps({
  name: {
    type: String,
    required: true,
    validator: (value) => ['tasks', 'warning'].includes(value),
  },
})
</script>

<template>
  <svg
    v-if="name === 'tasks'"
    class="farmer-dashboard-icon"
    viewBox="0 0 32 32"
    fill="none"
    aria-hidden="true"
  >
    <path d="M11.5 7.5H8.75A2.75 2.75 0 0 0 6 10.25v15A2.75 2.75 0 0 0 8.75 28h14.5A2.75 2.75 0 0 0 26 25.25v-15a2.75 2.75 0 0 0-2.75-2.75H20.5" />
    <path d="M12.25 5.25h7.5c.69 0 1.25.56 1.25 1.25v3h-10v-3c0-.69.56-1.25 1.25-1.25Z" />
    <path d="m11 18 3.25 3.25L21.5 14" />
  </svg>

  <svg
    v-else
    class="farmer-dashboard-icon"
    viewBox="0 0 32 32"
    fill="none"
    aria-hidden="true"
  >
    <path d="M13.53 5.35a2.85 2.85 0 0 1 4.94 0l10.17 17.62a2.85 2.85 0 0 1-2.47 4.28H5.83a2.85 2.85 0 0 1-2.47-4.28L13.53 5.35Z" />
    <path d="M16 11.2v7.6" />
    <path d="M16 23.15h.01" />
  </svg>
</template>

<style scoped>
.farmer-dashboard-icon {
  width: 1em;
  height: 1em;
  overflow: visible;
  stroke: currentColor;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
