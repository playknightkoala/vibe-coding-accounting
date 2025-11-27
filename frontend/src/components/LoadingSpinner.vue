<template>
  <div class="loading-overlay" v-if="show">
    <div class="loading-spinner">
      <div class="spinner"></div>
      <div class="loading-text">{{ text }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  show: boolean
  text?: string
}>()
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(10, 14, 39, 0.9);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(0, 212, 255, 0.1);
  border-radius: 50%;
  border-top-color: #00d4ff;
  border-right-color: #00d4ff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: #00d4ff;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}
</style>
