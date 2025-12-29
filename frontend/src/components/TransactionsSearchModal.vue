<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content" style="max-width: 1000px; max-height: 90vh; overflow-y: auto; position: relative;">
      <button @click="close" class="close-btn" type="button">✕</button>
      <h2 style="color: #00d4ff;">搜尋交易</h2>

      <div class="search-controls">
        <input type="text" v-model="localSearchQuery" placeholder="搜尋描述..." class="search-input" />
        <input type="text" v-model="localSearchCategory" placeholder="搜尋類別..." class="search-input" />
        <select v-model="localSearchType" class="search-select">
          <option value="">所有類型</option>
          <option value="credit">收入</option>
          <option value="debit">支出</option>
          <option value="installment">分期</option>
        </select>
        <div class="date-range-wrapper">
          <input type="date" v-model="localSearchStartDate" class="date-input" />
          <span class="date-separator">~</span>
          <input type="date" v-model="localSearchEndDate" class="date-input" />
        </div>
        <button @click="performSearch" class="btn btn-primary">搜尋</button>
        <button @click="clearLocalSearch" class="btn btn-secondary">清除</button>
      </div>

      <div v-if="hasSearched" style="margin-top: 20px;">
        <div v-if="searchResults.length > 0" style="overflow-x: auto;">
          <table class="table">
            <thead>
              <tr>
                <th>日期</th>
                <th>描述</th>
                <th>類型</th>
                <th>類別</th>
                <th>金額</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="transaction in searchResults" :key="transaction.id">
                <td>{{ formatDateTime(transaction.transaction_date) }}</td>
                <td>
                  {{ transaction.description }}
                  <span v-if="transaction.is_installment" style="color: #00d4ff; font-size: 0.85rem; margin-left: 5px;">
                    ({{ transaction.installment_number }}/{{ transaction.total_installments }})
                  </span>
                </td>
                <td>
                  {{ 
                    transaction.transaction_type === 'credit' ? '收入' : 
                    (transaction.transaction_type === 'installment' ? '分期' : 
                    (transaction.transaction_type === 'transfer_in' ? '轉入' : 
                    (transaction.transaction_type === 'transfer_out' ? '轉出' : '支出')))
                  }}
                </td>
                <td>{{ transaction.category || '無' }}</td>
                <td :style="{ color: 
                  transaction.transaction_type === 'credit' || transaction.transaction_type === 'transfer_in' ? '#51cf66' : '#ff6b6b' 
                }">
                  {{ transaction.transaction_type === 'credit' || transaction.transaction_type === 'transfer_in' ? '+' : '-' }}${{ formatAmount(transaction.amount) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else style="text-align: center;">找不到符合條件的交易</p>
      </div>
      <p v-else style="margin-top: 20px; text-align: center; color: rgba(255, 255, 255, 0.6);">
        請輸入搜尋條件以查看結果
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Transaction } from '@/types'
import { useDateTime } from '@/composables/useDateTime'
import { formatAmount } from '@/utils/format'

const props = defineProps<{
  modelValue: boolean
  transactions: Transaction[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const dateTimeUtils = useDateTime()

const localSearchQuery = ref('')
const localSearchCategory = ref('')
const localSearchType = ref('')
const { start: defaultStart, end: defaultEnd } = dateTimeUtils.getCurrentMonthRange()
const localSearchStartDate = ref(defaultStart)
const localSearchEndDate = ref(defaultEnd)

const searchResults = ref<Transaction[]>([])
const hasSearched = ref(false)

const performSearch = () => {
  hasSearched.value = true
  searchResults.value = props.transactions.filter(transaction => {
    const matchesDescription = localSearchQuery.value === '' ||
      transaction.description.toLowerCase().includes(localSearchQuery.value.toLowerCase())

    const matchesCategory = localSearchCategory.value === '' ||
      (transaction.category && transaction.category.toLowerCase().includes(localSearchCategory.value.toLowerCase()))

    const matchesDate = (!localSearchStartDate.value || transaction.transaction_date >= `${localSearchStartDate.value}T00:00:00`) &&
      (!localSearchEndDate.value || transaction.transaction_date <= `${localSearchEndDate.value}T23:59:59`)

    const matchesType = localSearchType.value === '' ||
      transaction.transaction_type === localSearchType.value

    return matchesDescription && matchesCategory && matchesDate && matchesType
  })
}

const clearLocalSearch = () => {
  localSearchQuery.value = ''
  localSearchCategory.value = ''
  localSearchType.value = ''
  const { start, end } = dateTimeUtils.getCurrentMonthRange()
  localSearchStartDate.value = start
  localSearchEndDate.value = end
  searchResults.value = []
  hasSearched.value = false
}

const formatDateTime = (dateString: string) => {
  return dateTimeUtils.formatDateTime(dateString)
}

const close = () => {
  emit('update:modelValue', false)
}

// Reset search when modal opens
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    clearLocalSearch()
  }
})
</script>

<style scoped>
.close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  color: white;
  font-size: 2rem;
  cursor: pointer;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
  line-height: 1;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #00d4ff;
}

.search-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.search-input {
  flex: 1;
  min-width: 150px;
  padding: 8px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.3);
  color: white;
}

.search-select {
  min-width: 100px;
  padding: 8px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.3);
  color: white;
}

.date-range-wrapper {
  display: flex;
  gap: 5px;
  align-items: center;
  flex-wrap: wrap;
}

.date-input {
  flex: 1;
  min-width: 130px;
  padding: 8px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.3);
  color: white;
}

.date-input::-webkit-calendar-picker-indicator {
  filter: invert(1);
  cursor: pointer;
}

.date-separator {
  color: #00d4ff;
}

@media (max-width: 768px) {
  .search-controls {
    flex-direction: column;
  }

  .search-input,
  .search-select,
  .date-range-wrapper {
    width: 100%;
    min-width: 0;
  }
}
</style>
