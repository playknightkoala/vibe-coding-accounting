<template>
  <div class="container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <h1 style="margin: 0;">報表</h1>
      <button
        type="button"
        @click="handleAIReportClick"
        style="padding: 12px 24px; background: linear-gradient(135deg, #00d4ff, #8a2be2); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3); display: flex; align-items: center; gap: 8px;"
      >
        <span class="material-icons">assessment</span>
        財務分析報告
      </button>
    </div>

    <!-- 報表類型與日期選擇器 -->
    <div class="card">
      <div class="controls">
        <div class="control-group">
          <label>報表類型：</label>
          <div class="btn-group">
            <button
              :class="['btn', reportType === 'monthly' ? 'btn-primary' : 'btn-secondary']"
              @click="reportType = 'monthly'"
            >
              月報
            </button>
            <button
            :class="['btn', reportType === 'daily' ? 'btn-primary' : 'btn-secondary']"
            @click="reportType = 'daily'"
          >
            日報
          </button>
          <button
            :class="['btn', reportType === 'custom' ? 'btn-primary' : 'btn-secondary']"
            @click="reportType = 'custom'"
          >
            自訂
          </button>
          </div>
        </div>

        <div class="control-group" v-if="reportType === 'monthly'">
          <label>選擇月份：</label>
          <div class="date-selector">
            <button @click="previousPeriod" class="nav-btn"><span class="material-icons">chevron_left</span></button>
            <span class="date-display">{{ currentYear }}年 {{ currentMonth }}月</span>
            <button @click="nextPeriod" class="nav-btn"><span class="material-icons">chevron_right</span></button>
          </div>
        </div>

        <div class="control-group" v-else-if="reportType === 'daily'">
          <label>選擇日期：</label>
          <input type="date" v-model="selectedDate" class="date-input" />
        </div>

        <div class="control-group" v-else-if="reportType === 'custom'">
          <label>選擇區間：</label>
          <div class="date-range-selector">
            <input type="date" v-model="customStartDate" class="date-input" placeholder="開始日期" />
            <span class="date-separator">至</span>
            <input type="date" v-model="customEndDate" class="date-input" placeholder="結束日期" />
          </div>
        </div>
      </div>
    </div>

    <!-- 子模組選單 -->
    <div class="card">
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          :class="['tab-btn', activeTab === tab.value ? 'active' : '']"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- 總覽子模組 -->
    <div v-if="activeTab === 'overview'" class="reports-section">
      <OverviewReport
        :report-type="reportType"
        :year="currentYear"
        :month="currentMonth"
        :date="selectedDate"
        :start-date="customStartDate"
        :end-date="customEndDate"
      />
    </div>

    <!-- 明細子模組 -->
    <div v-else-if="activeTab === 'details'" class="reports-section">
      <DetailsReport
        :report-type="reportType"
        :year="currentYear"
        :month="currentMonth"
        :date="selectedDate"
        :start-date="customStartDate"
        :end-date="customEndDate"
      />
    </div>

    <!-- 類別子模組 -->
    <div v-else-if="activeTab === 'category'" class="reports-section">
      <CategoryReport
        :report-type="reportType"
        :year="currentYear"
        :month="currentMonth"
        :date="selectedDate"
        :start-date="customStartDate"
        :end-date="customEndDate"
      />
    </div>

    <!-- 排行子模組 -->
    <div v-else-if="activeTab === 'ranking'" class="reports-section">
      <RankingReport
        :report-type="reportType"
        :year="currentYear"
        :month="currentMonth"
        :date="selectedDate"
        :start-date="customStartDate"
        :end-date="customEndDate"
      />
    </div>

    <!-- 帳戶子模組 -->
    <div v-else-if="activeTab === 'account'" class="reports-section">
      <AccountReportView
        :report-type="reportType"
        :year="currentYear"
        :month="currentMonth"
        :date="selectedDate"
        :start-date="customStartDate"
        :end-date="customEndDate"
      />
    </div>

    <!-- 預算子模組 -->
    <div v-else-if="activeTab === 'budget'" class="reports-section">
      <BudgetReport
        :stats="budgetStats"
        :transactions="budgetTransactions"
      />
    </div>

    <!-- AI財務報告模態框 -->
    <AIFinancialReportModal v-model="showAIReport" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import OverviewReport from '@/components/reports/OverviewReport.vue'
import DetailsReport from '@/components/reports/DetailsReport.vue'
import CategoryReport from '@/components/reports/CategoryReport.vue'
import RankingReport from '@/components/reports/RankingReport.vue'
import AccountReportView from '@/components/reports/AccountReportView.vue'
import BudgetReport from '@/components/reports/BudgetReport.vue'
import AIFinancialReportModal from '@/components/AIFinancialReportModal.vue'
import { useDateTime } from '@/composables/useDateTime'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const { getTodayString } = useDateTime()
const authStore = useAuthStore()

const reportType = ref<'monthly' | 'daily' | 'custom'>('monthly')
const activeTab = ref('overview')
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const selectedDate = ref(getTodayString())
const customStartDate = ref(getTodayString())
const customEndDate = ref(getTodayString())
const showAIReport = ref(false)

const handleAIReportClick = () => {
  showAIReport.value = true
}

const budgetStats = ref({
  total_budget: 0,
  total_spent: 0,
  remaining: 0,
  daily_average: 0,
  status: 'on_track'
})
const budgetTransactions = ref([])

const tabs = [
  { label: '總覽', value: 'overview' },
  { label: '明細', value: 'details' },
  { label: '類別', value: 'category' },
  { label: '排行', value: 'ranking' },
  { label: '帳戶', value: 'account' },
  { label: '預算', value: 'budget' }
]

const fetchBudgetData = async () => {
  try {
    let response
    
    if (reportType.value === 'monthly') {
      response = await api.getBudgetReportMonthly(currentYear.value, currentMonth.value)
    } else if (reportType.value === 'daily') {
      response = await api.getBudgetReportDaily(selectedDate.value)
    } else if (reportType.value === 'custom') {
      response = await api.getBudgetReportCustom(customStartDate.value, customEndDate.value)
    }
    
    budgetStats.value = response.data.stats
    budgetTransactions.value = response.data.transactions
  } catch (error) {
    console.error('Failed to fetch budget report:', error)
  }
}

// Watch for changes to fetch data
import { watch } from 'vue'
watch([reportType, currentYear, currentMonth, selectedDate, customStartDate, customEndDate, activeTab], () => {
  if (activeTab.value === 'budget') {
    fetchBudgetData()
  }
}, { immediate: true })

const previousPeriod = () => {
  if (reportType.value === 'monthly') {
    if (currentMonth.value === 1) {
      currentMonth.value = 12
      currentYear.value--
    } else {
      currentMonth.value--
    }
  } else {
    const date = new Date(selectedDate.value)
    date.setDate(date.getDate() - 1)
    selectedDate.value = date.toISOString().split('T')[0]
  }
}

const nextPeriod = () => {
  if (reportType.value === 'monthly') {
    if (currentMonth.value === 12) {
      currentMonth.value = 1
      currentYear.value++
    } else {
      currentMonth.value++
    }
  } else {
    const date = new Date(selectedDate.value)
    date.setDate(date.getDate() + 1)
    selectedDate.value = date.toISOString().split('T')[0]
  }
}
</script>

<style scoped>
.controls {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
  align-items: center;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-group label {
  font-weight: 500;
  color: #00d4ff;
}

.btn-group {
  display: flex;
  gap: 5px;
}

.date-selector {
  display: flex;
  align-items: center;
  gap: 15px;
}

.nav-btn {
  background: rgba(0, 212, 255, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.4);
  color: #00d4ff;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  background: rgba(0, 212, 255, 0.3);
  border-color: #00d4ff;
}

.date-display {
  min-width: 120px;
  text-align: center;
  font-weight: 500;
  color: #fff;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid rgba(0, 212, 255, 0.4);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.2);
  color: #fff;
  font-size: 14px;
}

.date-input::-webkit-calendar-picker-indicator {
  filter: invert(1);
}

.date-range-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-separator {
  color: #00d4ff;
  font-weight: 500;
}

.tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 10px 20px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 15px;
}

.tab-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.4);
  color: #fff;
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.3) 0%, rgba(0, 212, 255, 0.3) 100%);
  border-color: #00d4ff;
  color: #00d4ff;
  font-weight: 500;
}

.reports-section {
  margin-top: 20px;
}
</style>
