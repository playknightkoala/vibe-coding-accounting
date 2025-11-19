<template>
  <div class="form-group">
    <label>類別</label>
    <div style="display: flex; gap: 10px;">
      <select
        :value="modelValue"
        @input="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
        :required="required"
        style="flex: 1;"
      >
        <option value="">請選擇類別</option>
        <option v-for="category in categories" :key="category.id" :value="category.name">
          {{ category.name }}
        </option>
      </select>
      <button
        type="button"
        @click="$emit('openManagement')"
        class="btn btn-secondary"
        style="padding: 8px 15px; white-space: nowrap;"
      >
        管理類別
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Category } from '@/types'

interface Props {
  modelValue: string
  categories: Category[]
  required?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'openManagement'): void
}

defineProps<Props>()
defineEmits<Emits>()
</script>
