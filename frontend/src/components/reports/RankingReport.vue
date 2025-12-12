<template>
  <div class="ranking-report">
    <div v-if="loading" class="loading">載入中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="reportData">
      <!-- 切換按鈕 -->
      <!-- 切換按鈕 -->
      <div class="ranking-tabs-container">
        <div class="ranking-tabs">
          <button
            :class="['ranking-tab-btn', rankingType === 'expense' ? 'active' : '']"
            @click="rankingType = 'expense'"
          >
            <span class="tab-icon material-icons">bar_chart</span>
            支出排行
          </button>
          <button
            :class="['ranking-tab-btn', rankingType === 'income' ? 'active' : '']"
            @click="rankingType = 'income'"
          >
            <span class="tab-icon material-icons">payments</span>
            收入排行
          </button>
        </div>
      </div>

      <!-- 排行榜 -->
      <div class="card">
        <h2>{{ rankingType === 'expense' ? '支出排行' : '收入排行' }}</h2>
        <div v-if="currentRanking.length === 0" class="no-data">
          暫無數據
        </div>
        <div v-else class="ranking-list">
          <div
            v-for="(trans, index) in currentRanking"
            :key="trans.id"
            class="ranking-item"
          >
            <div class="rank-number" :class="getRankClass(index)">
              {{ index + 1 }}
            </div>
            <div class="transaction-info">
              <div class="trans-header">
                <span class="trans-desc">{{ trans.description }}</span>
                <span class="trans-date">{{ formatDate(trans.transaction_date) }}</span>
              </div>
              <div class="trans-meta">
                <span class="trans-category">{{ trans.category || '未分類' }}</span>
                <span class="trans-account">{{ trans.account_name }}</span>
              </div>
            </div>
            <div class="trans-amount" :class="trans.transaction_type">
              ${{ trans.amount.toFixed(2) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'
import type { RankingReport as RankingReportType, TransactionDetail } from '@/types'

interface Props {
  reportType: 'monthly' | 'daily' | 'custom'
  year: number
  month: number
  date: string
  startDate?: string
  endDate?: string
}

const props = defineProps<Props>()

const reportData = ref<RankingReportType | null>(null)
const loading = ref(false)
const error = ref('')
const rankingType = ref<'expense' | 'income'>('expense')

const currentRanking = computed(() => {
  if (!reportData.value) return []
  return rankingType.value === 'expense'
    ? reportData.value.expense_ranking
    : reportData.value.income_ranking
})

const fetchReport = async () => {
  loading.value = true
  error.value = ''

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getRankingReportMonthly(props.year, props.month)
    } else if (props.reportType === 'daily') {
      response = await api.getRankingReportDaily(props.date)
    } else if (props.reportType === 'custom' && props.startDate && props.endDate) {
      response = await api.getRankingReportCustom(props.startDate, props.endDate)
    }
    reportData.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || '載入報表失敗'
    console.error('Failed to fetch ranking report:', err)
  } finally {
    loading.value = false
  }
}

const getRankClass = (index: number) => {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return ''
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

watch([() => props.reportType, () => props.year, () => props.month, () => props.date, () => props.startDate, () => props.endDate], () => {
  fetchReport()
})

onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
.ranking-report {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.loading,
.error,
.no-data {
  text-align: center;
  padding: 40px;
  font-size: 16px;
}

.error {
  color: #ff6b6b;
}

.no-data {
  color: #a0aec0;
}

/* 頁籤容器 - 居中顯示 */
.ranking-tabs-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

/* 頁籤切換樣式 */
.ranking-tabs {
  display: inline-flex;
  gap: 15px;
  background: rgba(0, 0, 0, 0.2);
  padding: 8px;
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.ranking-tab-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: transparent;
  border: 2px solid transparent;
  border-radius: 8px;
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 15px;
  font-weight: 500;
  white-space: nowrap;
}

.ranking-tab-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  color: #fff;
  border-color: rgba(0, 212, 255, 0.3);
}

.ranking-tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.4) 0%, rgba(0, 212, 255, 0.4) 100%);
  border-color: #00d4ff;
  color: #00d4ff;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.tab-icon {
  font-size: 20px;
}

@media (max-width: 768px) {
  .ranking-tabs-container {
    padding: 0 10px;
  }

  .ranking-tabs {
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }

  .ranking-tab-btn {
    width: 100%;
    justify-content: center;
  }
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  transition: all 0.2s;
}

.ranking-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(0, 212, 255, 0.4);
}

.rank-number {
  min-width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  color: #a0aec0;
}

.rank-number.rank-1 {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #000;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
}

.rank-number.rank-2 {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  color: #000;
  box-shadow: 0 0 15px rgba(192, 192, 192, 0.5);
}

.rank-number.rank-3 {
  background: linear-gradient(135deg, #cd7f32 0%, #e8a56f 100%);
  color: #000;
  box-shadow: 0 0 15px rgba(205, 127, 50, 0.5);
}

.transaction-info {
  flex: 1;
  min-width: 0;
}

.trans-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  gap: 10px;
}

.trans-desc {
  font-weight: 500;
  font-size: 16px;
  color: #fff;
}

.trans-date {
  font-size: 13px;
  color: #a0aec0;
  white-space: nowrap;
}

.trans-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
}

.trans-category,
.trans-account {
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  color: #a0aec0;
}

.trans-amount {
  font-size: 20px;
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
