<template>
  <div v-if="modelValue" class="modal" @click.self="cancel">
    <div class="modal-content" style="max-width: 400px;">
      <h2 style="color: #00d4ff; margin-bottom: 20px;">{{ title }}</h2>
      <p style="margin-bottom: 30px; line-height: 1.6;">{{ message }}</p>
      <div style="display: flex; gap: 10px; justify-content: flex-end;">
        <button
          type="button"
          @click="cancel"
          class="btn btn-secondary"
          style="padding: 10px 20px;"
        >
          {{ cancelText }}
        </button>
        <button
          type="button"
          @click="confirm"
          class="btn"
          :style="{
            padding: '10px 20px',
            background: confirmType === 'danger' ? 'linear-gradient(135deg, #ff6b6b 0%, #c92a2a 100%)' : 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)',
            color: 'white'
          }"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmType?: 'primary' | 'danger'
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const confirm = () => {
  emit('confirm')
  emit('update:modelValue', false)
}

const cancel = () => {
  emit('cancel')
  emit('update:modelValue', false)
}
</script>

<script lang="ts">
export default {
  name: 'ConfirmModal'
}
</script>
