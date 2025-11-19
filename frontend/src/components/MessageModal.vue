<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content">
      <h2 :style="{ color: type === 'success' ? '#51cf66' : '#ff6b6b' }">
        {{ type === 'success' ? '成功' : '錯誤' }}
      </h2>
      <p style="margin: 20px 0; color: #a0aec0;">{{ message }}</p>
      <button @click="$emit('update:modelValue', false)" class="btn btn-primary" style="width: 100%;">
        確定
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  type: 'success' | 'error'
  message: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

defineProps<Props>()
defineEmits<Emits>()
</script>
