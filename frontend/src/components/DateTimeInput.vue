<template>
  <div class="datetime-input-wrapper">
    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 150px;">
        <input
          type="date"
          :value="dateValue"
          @input="updateDate"
          :required="required"
          style="width: 100%; padding: 8px; border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 4px; background: rgba(0, 0, 0, 0.3); color: white;"
        />
      </div>
      <div style="display: flex; gap: 5px; align-items: center;">
        <select
          :value="hourValue"
          @change="updateHour"
          :required="required"
          style="padding: 8px; border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 4px; background: rgba(0, 0, 0, 0.3); color: white; width: 70px;"
        >
          <option v-for="hour in 24" :key="hour - 1" :value="String(hour - 1).padStart(2, '0')">
            {{ String(hour - 1).padStart(2, '0') }}
          </option>
        </select>
        <span style="color: white;">:</span>
        <select
          :value="minuteValue"
          @change="updateMinute"
          :required="required"
          style="padding: 8px; border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 4px; background: rgba(0, 0, 0, 0.3); color: white; width: 70px;"
        >
          <option v-for="minute in 60" :key="minute - 1" :value="String(minute - 1).padStart(2, '0')">
            {{ String(minute - 1).padStart(2, '0') }}
          </option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: string // 格式: YYYY-MM-DDTHH:mm
  required?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const dateValue = computed(() => {
  if (!props.modelValue) return ''
  return props.modelValue.split('T')[0]
})

const hourValue = computed(() => {
  if (!props.modelValue) return '00'
  const timePart = props.modelValue.split('T')[1]
  return timePart ? timePart.split(':')[0] : '00'
})

const minuteValue = computed(() => {
  if (!props.modelValue) return '00'
  const timePart = props.modelValue.split('T')[1]
  return timePart ? timePart.split(':')[1] : '00'
})

const updateDate = (event: Event) => {
  const target = event.target as HTMLInputElement
  const newDate = target.value
  const newValue = `${newDate}T${hourValue.value}:${minuteValue.value}`
  emit('update:modelValue', newValue)
}

const updateHour = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const newHour = target.value
  const newValue = `${dateValue.value}T${newHour}:${minuteValue.value}`
  emit('update:modelValue', newValue)
}

const updateMinute = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const newMinute = target.value
  const newValue = `${dateValue.value}T${hourValue.value}:${newMinute}`
  emit('update:modelValue', newValue)
}
</script>

<style scoped>
.datetime-input-wrapper select {
  cursor: pointer;
}

.datetime-input-wrapper select:focus,
.datetime-input-wrapper input:focus {
  outline: none;
  border-color: #00d4ff;
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
}

.datetime-input-wrapper input[type="date"]::-webkit-calendar-picker-indicator {
  filter: invert(1);
  cursor: pointer;
}
</style>
