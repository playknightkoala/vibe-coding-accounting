<template>
  <div class="details-report">
    <div v-if="loading" class="loading">載入中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="reportData">
      <!-- 總計 -->
      <div class="summary-bar">
        <span>總收入: <strong class="credit">${{ reportData.total_credit.toFixed(2) }}</strong></span>
        <span>總支出: <strong class="debit">${{ reportData.total_debit.toFixed(2) }}</strong></span>
      </div>

      <!-- 每日明細 -->
      <div class="daily-list">
        <div v-for="daily in reportData.daily_transactions" :key="daily.date" class="daily-group">
          <div class="daily-header" @click="toggleDay(daily.date)">
            <div>
              <h3>{{ formatDate(daily.date) }}</h3>
              <span class="daily-summary">
                收入: ${{ daily.total_credit.toFixed(2) }} |
                支出: ${{ daily.total_debit.toFixed(2) }}
              </span>
            </div>
            <span class="toggle-icon">{{ expandedDays.includes(daily.date) ? '▼' : '▶' }}</span>
          </div>

          <div v-if="expandedDays.includes(daily.date)" class="transactions-list">
            <div
              v-for="trans in daily.transactions"
              :key="trans.id"
              class="transaction-row"
            >
              <div class="trans-time">{{ formatTime(trans.transaction_date) }}</div>
              <div class="trans-info">
                <div class="trans-desc">{{ trans.description }}</div>
                <div class="trans-meta">
                  <span>{{ trans.category || '未分類' }}</span>
                  <span>{{ trans.account_name }}</span>
                </div>
              </div>
              <div class="trans-amount" :class="trans.transaction_type">
                {{ trans.transaction_type === 'credit' ? '+' : '-' }}${{ trans.amount.toFixed(2) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import api from '@/services/api'
import type { DetailsReport as DetailsReportType } from '@/types'

interface Props {
  reportType: 'monthly' | 'daily'
  year: number
  month: number
  date: string
}

const props = defineProps<Props>()

const reportData = ref<DetailsReportType | null>(null)
const loading = ref(false)
const error = ref('')
const expandedDays = ref<string[]>([])

const fetchReport = async () => {
  loading.value = true
  error.value = ''

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getDetailsReportMonthly(props.year, props.month)
    } else {
      response = await api.getDetailsReportDaily(props.date)
    }
    reportData.value = response.data

    // Auto expand first day
    if (reportData.value.daily_transactions.length > 0) {
      expandedDays.value = [reportData.value.daily_transactions[0].date]
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || '載入報表失敗'
    console.error('Failed to fetch details report:', err)
  } finally {
    loading.value = false
  }
}

const toggleDay = (date: string) => {
  const index = expandedDays.value.indexOf(date)
  if (index > -1) {
    expandedDays.value.splice(index, 1)
  } else {
    expandedDays.value.push(date)
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${date.getMonth() + 1}月${date.getDate()}日 (${weekdays[date.getDay()]})`
}

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

watch([() => props.reportType, () => props.year, () => props.month, () => props.date], () => {
  fetchReport()
})

onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
.details-report {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.loading,
.error {
  text-align: center;
  padding: 40px;
  font-size: 16px;
}

.error {
  color: #ff6b6b;
}

.summary-bar {
  display: flex;
  gap: 30px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  justify-content: center;
  font-size: 16px;
}

.summary-bar .credit {
  color: #51cf66;
}

.summary-bar .debit {
  color: #ff6b6b;
}

.daily-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.daily-group {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  overflow: hidden;
}

.daily-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.daily-header:hover {
  background: rgba(0, 212, 255, 0.05);
}

.daily-header h3 {
  margin: 0 0 5px 0;
  color: #00d4ff;
  font-size: 18px;
}

.daily-summary {
  font-size: 14px;
  color: #a0aec0;
}

.toggle-icon {
  font-size: 18px;
  color: #00d4ff;
}

.transactions-list {
  border-top: 1px solid rgba(0, 212, 255, 0.2);
  padding: 10px;
}

.transaction-row {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 6px;
  margin-bottom: 8px;
}

.trans-time {
  font-size: 14px;
  color: #a0aec0;
  min-width: 50px;
}

.trans-info {
  flex: 1;
  min-width: 0;
}

.trans-desc {
  font-weight: 500;
  margin-bottom: 4px;
}

.trans-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #a0aec0;
}

.trans-meta span {
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.trans-amount {
  font-size: 16px;
  font-weight: bold;
  white-space: nowrap;
}

.trans-amount.credit {
  color: #51cf66;
}

.trans-amount.debit {
  color: #ff6b6b;
}
</style>
