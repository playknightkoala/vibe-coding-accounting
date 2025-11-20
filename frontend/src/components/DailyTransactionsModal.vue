<template>
  <div v-if="modelValue" class="modal" @click.self="closeModal">
    <div class="modal-content daily-transactions-modal">
      <div class="modal-header">
        <h2>{{ formattedDate }} 消費明細</h2>
        <button @click="closeModal" class="close-btn">✕</button>
      </div>

      <div class="summary-section">
        <div class="summary-item income">
          <span class="label">收入</span>
          <span class="value">${{ totalCredit.toFixed(2) }}</span>
        </div>
        <div class="summary-item expense">
          <span class="label">支出</span>
          <span class="value">${{ totalDebit.toFixed(2) }}</span>
        </div>
        <div class="summary-item net" :class="{ positive: netAmount >= 0, negative: netAmount < 0 }">
          <span class="label">淨收入</span>
          <span class="value">${{ netAmount.toFixed(2) }}</span>
        </div>
      </div>

      <div class="transactions-list">
        <div v-if="loading" class="loading">載入中...</div>
        <div v-else-if="transactions.length === 0" class="empty-state">
          當日無交易記錄
        </div>
        <div v-else class="transaction-items">
          <div
            v-for="transaction in transactions"
            :key="transaction.id"
            class="transaction-item"
            :class="transaction.transaction_type"
          >
            <div class="transaction-main">
              <div class="transaction-info">
                <div class="transaction-description">{{ transaction.description }}</div>
                <div class="transaction-meta">
                  <span class="transaction-time">{{ formatTime(transaction.transaction_date) }}</span>
                  <span v-if="transaction.category" class="transaction-category">{{ transaction.category }}</span>
                  <span class="transaction-account">{{ getAccountName(transaction.account_id) }}</span>
                </div>
              </div>
              <div class="transaction-amount" :class="transaction.transaction_type">
                {{ transaction.transaction_type === 'credit' ? '+' : '-' }}${{ transaction.amount.toFixed(2) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn btn-secondary">關閉</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Transaction, Account } from '@/types'
import api from '@/services/api'
import { useAccountsStore } from '@/stores/accounts'

interface Props {
  modelValue: boolean
  date: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const accountsStore = useAccountsStore()
const transactions = ref<Transaction[]>([])
const loading = ref(false)

const formattedDate = computed(() => {
  if (!props.date) return ''
  const date = new Date(props.date)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  const weekday = weekdays[date.getDay()]
  return `${year}年${month}月${day}日 (${weekday})`
})

const totalCredit = computed(() => {
  return transactions.value
    .filter(t => t.transaction_type === 'credit')
    .reduce((sum, t) => sum + t.amount, 0)
})

const totalDebit = computed(() => {
  return transactions.value
    .filter(t => t.transaction_type === 'debit')
    .reduce((sum, t) => sum + t.amount, 0)
})

const netAmount = computed(() => {
  return totalCredit.value - totalDebit.value
})

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

const getAccountName = (accountId: number): string => {
  const account = accountsStore.accounts.find(a => a.id === accountId)
  return account ? account.name : '未知帳戶'
}

const fetchDailyTransactions = async () => {
  if (!props.date) return

  loading.value = true
  try {
    const response = await api.getDailyTransactions(props.date)
    transactions.value = response.data
  } catch (error) {
    console.error('Failed to fetch daily transactions:', error)
    transactions.value = []
  } finally {
    loading.value = false
  }
}

const closeModal = () => {
  emit('update:modelValue', false)
}

watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    fetchDailyTransactions()
  }
})

watch(() => props.date, (newValue) => {
  if (newValue && props.modelValue) {
    fetchDailyTransactions()
  }
})
</script>

<style scoped>
.daily-transactions-modal {
  max-width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid rgba(0, 212, 255, 0.3);
}

.modal-header h2 {
  margin: 0;
  color: #00d4ff;
  font-size: 22px;
}

.close-btn {
  background: none;
  border: none;
  color: #a0aec0;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.summary-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.summary-item {
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-item.income {
  background: linear-gradient(135deg, rgba(81, 207, 102, 0.1) 0%, rgba(81, 207, 102, 0.05) 100%);
  border-color: rgba(81, 207, 102, 0.3);
}

.summary-item.expense {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 107, 107, 0.05) 100%);
  border-color: rgba(255, 107, 107, 0.3);
}

.summary-item.net {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
  border-color: rgba(0, 212, 255, 0.3);
}

.summary-item .label {
  display: block;
  font-size: 13px;
  color: #a0aec0;
  margin-bottom: 8px;
}

.summary-item .value {
  display: block;
  font-size: 20px;
  font-weight: bold;
}

.summary-item.income .value {
  color: #51cf66;
}

.summary-item.expense .value {
  color: #ff6b6b;
}

.summary-item.net.positive .value {
  color: #51cf66;
}

.summary-item.net.negative .value {
  color: #ff6b6b;
}

.transactions-list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  min-height: 200px;
  max-height: 400px;
}

.loading,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #a0aec0;
  font-size: 16px;
}

.transaction-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.transaction-item {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 15px;
  transition: all 0.2s;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.transaction-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(0, 212, 255, 0.3);
  transform: translateY(-1px);
}

.transaction-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
}

.transaction-info {
  flex: 1;
  min-width: 0;
}

.transaction-description {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  margin-bottom: 6px;
  word-break: break-word;
}

.transaction-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #a0aec0;
}

.transaction-time,
.transaction-category,
.transaction-account {
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.transaction-amount {
  font-size: 18px;
  font-weight: bold;
  white-space: nowrap;
}

.transaction-amount.credit {
  color: #51cf66;
}

.transaction-amount.debit {
  color: #ff6b6b;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .daily-transactions-modal {
    max-width: 95%;
    margin: 20px auto;
  }

  .summary-section {
    grid-template-columns: 1fr;
  }

  .transaction-main {
    flex-direction: column;
    align-items: flex-start;
  }

  .transaction-amount {
    align-self: flex-end;
  }
}
</style>
