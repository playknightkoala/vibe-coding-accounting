<template>
  <div v-if="modelValue" class="modal" @click.self="cancel">
    <div class="modal-content" style="max-width: 400px;">
      <h2 style="color: #00d4ff; margin-bottom: 20px;">{{ title }}</h2>
      <p style="margin-bottom: 30px; line-height: 1.6; white-space: pre-line;">{{ message }}</p>

      <!-- 確認文字輸入框 -->
      <div v-if="requireConfirmText" style="margin-bottom: 20px;">
        <label
          :for="'confirm-input-' + _uid"
          style="display: block; margin-bottom: 8px; color: #ff9999; font-weight: 500;"
        >
          請輸入「{{ confirmText }}」以確認：
        </label>
        <input
          :id="'confirm-input-' + _uid"
          v-model="inputText"
          type="text"
          :placeholder="confirmTextPlaceholder"
          style="width: 100%; padding: 10px; border-radius: 4px; border: 1px solid rgba(255, 107, 107, 0.3); background: rgba(255, 255, 255, 0.05); color: #e0e6ed;"
        />
      </div>

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
          :disabled="requireConfirmText && inputText !== confirmTextPlaceholder"
          :style="{
            padding: '10px 20px',
            background: confirmType === 'danger' ? 'linear-gradient(135deg, #ff6b6b 0%, #c92a2a 100%)' : 'linear-gradient(135deg, #00d4ff 0%, #0099cc 100%)',
            color: 'white',
            opacity: (requireConfirmText && inputText !== confirmTextPlaceholder) ? 0.5 : 1,
            cursor: (requireConfirmText && inputText !== confirmTextPlaceholder) ? 'not-allowed' : 'pointer'
          }"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, getCurrentInstance } from 'vue'

const props = defineProps<{
  modelValue: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmType?: 'primary' | 'danger'
  requireConfirmText?: boolean
  confirmTextPlaceholder?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const inputText = ref('')
const instance = getCurrentInstance()
const _uid = instance?.uid || 0

// 重置輸入框當模態框關閉時
watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    inputText.value = ''
  }
})

const confirm = () => {
  // 如果需要確認文字但輸入不匹配，則不執行
  if (props.requireConfirmText && inputText.value !== props.confirmTextPlaceholder) {
    return
  }
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
