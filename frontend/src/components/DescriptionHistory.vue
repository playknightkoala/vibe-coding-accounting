<template>
  <div class="description-history">
    <div class="history-scroll-container">
      <button
        v-for="desc in descriptions"
        :key="desc"
        @click="selectDescription(desc)"
        class="history-item"
        type="button"
      >
        {{ desc }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  descriptions: string[]
}>()

const emit = defineEmits<{
  (e: 'select', description: string): void
}>()

const selectDescription = (description: string) => {
  emit('select', description)
}
</script>

<style scoped>
.description-history {
  margin-top: 8px;
}

.history-scroll-container {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 4px 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 212, 255, 0.3) rgba(0, 0, 0, 0.2);
}

.history-scroll-container::-webkit-scrollbar {
  height: 6px;
}

.history-scroll-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.history-scroll-container::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 3px;
}

.history-scroll-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.5);
}

.history-item {
  flex-shrink: 0;
  padding: 6px 12px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  color: #00d4ff;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.history-item:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: #00d4ff;
  transform: translateY(-1px);
}

.history-item:active {
  transform: translateY(0);
}
</style>
