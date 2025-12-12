<template>
  <div class="account-report">
    <div v-if="loading" class="loading">載入中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="reportData">
      <!-- 頁籤切換（放在最上方中間） -->
      <div v-if="hasData" class="account-tabs-container">
        <div class="account-tabs">
          <button
            :class="['account-tab-btn', accountTab === 'total' ? 'active' : '']"
            @click="accountTab = 'total'"
          >
            <span class="tab-icon material-icons">trending_up</span>
            總計
            <span class="tab-amount">${{ totalAmount.toFixed(2) }}</span>
          </button>
          <button
            :class="['account-tab-btn', accountTab === 'debit' ? 'active' : '']"
            @click="accountTab = 'debit'"
          >
            <span class="tab-icon material-icons">bar_chart</span>
            支出
            <span class="tab-amount">${{ totalDebit.toFixed(2) }}</span>
          </button>
          <button
            :class="['account-tab-btn', accountTab === 'credit' ? 'active' : '']"
            @click="accountTab = 'credit'"
          >
            <span class="tab-icon material-icons">payments</span>
            收入
            <span class="tab-amount">${{ totalCredit.toFixed(2) }}</span>
          </button>
        </div>
      </div>

      <!-- 圓餅圖 -->
      <div class="card">
        <h2>{{ tabTitle }}帳戶統計</h2>

        <!-- 圖表顯示區域 -->
        <div v-if="hasData" class="chart-display">
          <!-- 總計圓餅圖 -->
          <div v-show="accountTab === 'total'" class="chart-wrapper">
            <div v-if="reportData.account_stats.length > 0" ref="totalChartContainer" class="chart-container"></div>
            <p v-else class="empty-message">本期沒有交易記錄</p>
          </div>

          <!-- 支出圓餅圖 -->
          <div v-show="accountTab === 'debit'" class="chart-wrapper">
            <div v-if="totalDebit > 0" ref="debitChartContainer" class="chart-container"></div>
            <p v-else class="empty-message">本期沒有支出記錄</p>
          </div>

          <!-- 收入圓餅圖 -->
          <div v-show="accountTab === 'credit'" class="chart-wrapper">
            <div v-if="totalCredit > 0" ref="creditChartContainer" class="chart-container"></div>
            <p v-else class="empty-message">本期沒有收入記錄</p>
          </div>
        </div>

        <p v-else class="empty-message">本期沒有任何交易記錄</p>
      </div>

      <!-- 各帳戶收支明細（跟隨頁籤切換） -->
      <div class="card">
        <h2>{{ tabTitle }}帳戶明細</h2>
        <p v-if="filteredAccounts.length === 0" class="empty-message">
          本期沒有{{ accountTab === 'total' ? '交易' : (accountTab === 'debit' ? '支出' : '收入') }}記錄
        </p>
        <div v-else class="account-list">
          <div
            v-for="account in filteredAccounts"
            :key="account.account_id"
            :ref="el => setAccountItemRef(el, account.account_id)"
            class="account-item"
            @click="toggleAccount(account.account_id)"
          >
            <div class="account-header">
              <div class="account-name">{{ account.account_name }}</div>
              <div class="account-amounts">
                <template v-if="accountTab === 'total'">
                  <span class="balance">餘額: ${{ account.balance.toFixed(2) }}</span>
                  <span class="credit">收入: ${{ account.credit.toFixed(2) }}</span>
                  <span class="debit">支出: ${{ account.debit.toFixed(2) }}</span>
                  <span class="percentage">({{ account.percentage.toFixed(1) }}%)</span>
                </template>
                <template v-else>
                  <span :class="accountTab === 'debit' ? 'debit' : 'credit'">
                    {{ accountTab === 'debit' ? '支出' : '收入' }}: ${{ currentAmount(account).toFixed(2) }}
                  </span>
                  <span class="percentage">({{ currentPercentage(account).toFixed(1) }}%)</span>
                </template>
              </div>
              <span class="expand-icon material-icons">{{ expandedAccount === account.account_id ? 'expand_more' : 'chevron_right' }}</span>
            </div>

            <!-- 該帳戶的明細 -->
            <div v-if="expandedAccount === account.account_id" class="account-details">
              <div v-if="accountTransactions.length === 0" class="loading-details">載入中...</div>
              <div v-else class="transactions-list">
                <div
                  v-for="trans in accountTransactions"
                  :key="trans.id"
                  class="transaction-row"
                >
                  <div class="trans-date">{{ formatDate(trans.transaction_date) }}</div>
                  <div class="trans-info">
                    <div class="trans-desc">{{ trans.description }}</div>
                    <div class="trans-category">{{ trans.category || '未分類' }}</div>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/services/api'
import type { AccountReport, TransactionDetail } from '@/types'

interface Props {
  reportType: 'monthly' | 'daily' | 'custom'
  year: number
  month: number
  date: string
  startDate?: string
  endDate?: string
}

const props = defineProps<Props>()

const reportData = ref<AccountReport | null>(null)
const loading = ref(false)
const error = ref('')
const accountTab = ref<'total' | 'debit' | 'credit'>('total')
const totalChartContainer = ref<HTMLElement | null>(null)
const debitChartContainer = ref<HTMLElement | null>(null)
const creditChartContainer = ref<HTMLElement | null>(null)
let totalChartInstance: echarts.ECharts | null = null
let debitChartInstance: echarts.ECharts | null = null
let creditChartInstance: echarts.ECharts | null = null

const expandedAccount = ref<number | null>(null)
const accountTransactions = ref<TransactionDetail[]>([])
const accountItemRefs = ref<Map<number, HTMLElement>>(new Map())

const chartColors = [
  '#9966ff', '#ff9933', '#33ccff', '#ffcc00', '#ff6699',
  '#66ff99', '#ff6666', '#6699ff', '#ffcc99', '#cc99ff'
]

// Computed properties
const hasData = computed(() => {
  if (!reportData.value) return false
  return reportData.value.account_stats.length > 0
})

const totalAmount = computed(() => {
  return reportData.value?.total_amount || 0
})

const totalDebit = computed(() => {
  if (!reportData.value) return 0
  return reportData.value.account_stats.reduce((sum, acc) => sum + acc.debit, 0)
})

const totalCredit = computed(() => {
  if (!reportData.value) return 0
  return reportData.value.account_stats.reduce((sum, acc) => sum + acc.credit, 0)
})

const tabTitle = computed(() => {
  if (accountTab.value === 'total') return ''
  if (accountTab.value === 'debit') return '支出'
  return '收入'
})

// 根據當前頁籤過濾帳戶
const filteredAccounts = computed(() => {
  if (!reportData.value) return []

  if (accountTab.value === 'total') {
    return reportData.value.account_stats
      .filter(acc => acc.debit > 0 || acc.credit > 0)
      .sort((a, b) => b.amount - a.amount)
  }

  return reportData.value.account_stats.filter(acc => {
    if (accountTab.value === 'debit') {
      return acc.debit > 0
    } else {
      return acc.credit > 0
    }
  }).sort((a, b) => {
    const amountA = accountTab.value === 'debit' ? a.debit : a.credit
    const amountB = accountTab.value === 'debit' ? b.debit : b.credit
    return amountB - amountA
  })
})

// 獲取當前類型的金額
const currentAmount = (account: any) => {
  return accountTab.value === 'debit' ? account.debit : account.credit
}

// 計算當前類型的百分比
const currentPercentage = (account: any) => {
  const total = accountTab.value === 'debit' ? totalDebit.value : totalCredit.value
  const amount = currentAmount(account)
  return total > 0 ? (amount / total * 100) : 0
}

const setAccountItemRef = (el: any, accountId: number) => {
  if (el) {
    accountItemRefs.value.set(accountId, el)
  }
}

const fetchReport = async () => {
  loading.value = true
  error.value = ''
  expandedAccount.value = null

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getAccountReportMonthly(props.year, props.month)
    } else if (props.reportType === 'daily') {
      response = await api.getAccountReportDaily(props.date)
    } else if (props.reportType === 'custom' && props.startDate && props.endDate) {
      response = await api.getAccountReportCustom(props.startDate, props.endDate)
    }
    reportData.value = response.data

    // 智能設置初始頁籤
    if (totalDebit.value === 0 && totalCredit.value > 0) {
      accountTab.value = 'credit'
    } else if (totalCredit.value === 0 && totalDebit.value > 0) {
      accountTab.value = 'debit'
    } else {
      accountTab.value = 'total'
    }

    loading.value = false
    await nextTick()
    renderPieCharts()
  } catch (err: any) {
    loading.value = false
    error.value = err.response?.data?.detail || '載入報表失敗'
    console.error('Failed to fetch account report:', err)
  }
}

const renderPieCharts = () => {
  if (!reportData.value || reportData.value.account_stats.length === 0) {
    return
  }

  // Render total chart (based on debit amount)
  renderChart(
    totalChartContainer,
    totalChartInstance,
    'total',
    totalAmount.value,
    '總計'
  )

  // Render debit chart
  renderChart(
    debitChartContainer,
    debitChartInstance,
    'debit',
    totalDebit.value,
    '支出'
  )

  // Render credit chart
  renderChart(
    creditChartContainer,
    creditChartInstance,
    'credit',
    totalCredit.value,
    '收入'
  )
}

const renderChart = (
  containerRef: any,
  chartInstanceRef: echarts.ECharts | null,
  type: 'total' | 'debit' | 'credit',
  totalValue: number,
  label: string
) => {
  if (!containerRef.value || !reportData.value) {
    return
  }

  // Dispose existing chart
  if (chartInstanceRef) {
    chartInstanceRef.dispose()
    chartInstanceRef = null
  }

  // Filter accounts based on type
  let filteredStats = reportData.value.account_stats
  if (type === 'debit') {
    filteredStats = filteredStats.filter(acc => acc.debit > 0)
  } else if (type === 'credit') {
    filteredStats = filteredStats.filter(acc => acc.credit > 0)
  } else {
    filteredStats = filteredStats.filter(acc => acc.debit > 0 || acc.credit > 0)
  }

  if (filteredStats.length === 0) {
    return
  }

  // Create new chart instance
  const newChartInstance = echarts.init(containerRef.value)

  // Update the ref based on type
  if (type === 'total') {
    totalChartInstance = newChartInstance
  } else if (type === 'debit') {
    debitChartInstance = newChartInstance
  } else {
    creditChartInstance = newChartInstance
  }

  const chartData = filteredStats.map((acc, index) => ({
    name: acc.account_name,
    value: type === 'total' ? acc.amount : (type === 'debit' ? acc.debit : acc.credit),
    itemStyle: {
      color: chartColors[index % chartColors.length]
    }
  }))

  const option: echarts.EChartsOption = {
    title: {
      text: `總${label}\n$${totalValue.toFixed(2)}`,
      left: 'center',
      top: 'center',
      textStyle: {
        color: '#00d4ff',
        fontSize: 20,
        fontWeight: 'bold'
      },
      subtextStyle: {
        color: '#a0aec0',
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ${c} ({d}%)',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: '#00d4ff',
      borderWidth: 1,
      textStyle: {
        color: '#fff'
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      textStyle: {
        color: '#fff'
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 10,
          borderColor: 'rgba(0, 0, 0, 0.2)',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          color: '#fff',
          fontSize: 12
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 212, 255, 0.5)'
          }
        },
        data: chartData
      }
    ]
  }

  newChartInstance.setOption(option)

  newChartInstance.on('click', (params) => {
    if (params.componentType === 'series') {
      const accountName = params.name
      const value = params.value as number
      const percent = params.percent

      // Find account ID
      const account = reportData.value?.account_stats.find(acc => acc.account_name === accountName)

      // Update title
      newChartInstance?.setOption({
        title: {
          text: `${accountName}\n$${value.toFixed(2)}`,
          subtext: `${percent}%`
        }
      })

      // Expand list item
      if (account && expandedAccount.value !== account.account_id) {
        toggleAccount(account.account_id)
      }
    }
  })

  // Reset title when clicking on empty area (zrender event)
  newChartInstance.getZr().on('click', (params) => {
    if (!params.target) {
      newChartInstance?.setOption({
        title: {
          text: `總${label}\n$${totalValue.toFixed(2)}`,
          subtext: ''
        }
      })

      if (expandedAccount.value) {
        // Toggle off - need to pass the current ID to toggle it off
        toggleAccount(expandedAccount.value)
      }
    }
  })

  const handleResize = () => {
    newChartInstance?.resize()
  }
  window.addEventListener('resize', handleResize)
}

const toggleAccount = async (accountId: number) => {
  if (expandedAccount.value === accountId) {
    expandedAccount.value = null
    accountTransactions.value = []
    return
  }

  expandedAccount.value = accountId
  accountTransactions.value = []

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getAccountTransactionsMonthly(accountId, props.year, props.month)
    } else {
      response = await api.getAccountTransactionsDaily(accountId, props.date)
    }
    accountTransactions.value = response.data

    // Scroll to the account item after data is loaded
    await nextTick()
    scrollToAccountItem(accountId)
  } catch (err: any) {
    console.error('Failed to fetch account transactions:', err)
  }
}

const scrollToAccountItem = (accountId: number) => {
  const element = accountItemRefs.value.get(accountId)
  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

watch([() => props.reportType, () => props.year, () => props.month, () => props.date, () => props.startDate, () => props.endDate], () => {
  fetchReport()
})

// Watch accountTab to resize charts when switching
watch(accountTab, async () => {
  await nextTick()
  if (accountTab.value === 'total' && totalChartInstance) {
    totalChartInstance.resize()
  } else if (accountTab.value === 'debit' && debitChartInstance) {
    debitChartInstance.resize()
  } else if (accountTab.value === 'credit' && creditChartInstance) {
    creditChartInstance.resize()
  }
})

onMounted(() => {
  fetchReport()
})

onBeforeUnmount(() => {
  if (totalChartInstance) {
    totalChartInstance.dispose()
    totalChartInstance = null
  }
  if (debitChartInstance) {
    debitChartInstance.dispose()
    debitChartInstance = null
  }
  if (creditChartInstance) {
    creditChartInstance.dispose()
    creditChartInstance = null
  }
})
</script>

<style scoped>
.account-report {
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

/* 頁籤樣式 */
.account-tabs-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.account-tabs {
  display: inline-flex;
  gap: 15px;
  background: rgba(0, 0, 0, 0.2);
  padding: 8px;
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.account-tab-btn {
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

.account-tab-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  color: #fff;
  border-color: rgba(0, 212, 255, 0.3);
}

.account-tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.4) 0%, rgba(0, 212, 255, 0.4) 100%);
  border-color: #00d4ff;
  color: #00d4ff;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.tab-icon {
  font-size: 20px;
}

.tab-amount {
  margin-left: auto;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  font-size: 14px;
  font-weight: bold;
}

.account-tab-btn.active .tab-amount {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

@media (max-width: 768px) {
  .account-tabs-container {
    padding: 0 10px;
  }

  .account-tabs {
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }

  .account-tab-btn {
    width: 100%;
    justify-content: center;
  }

  .tab-amount {
    margin-left: 10px;
  }
}

.chart-display {
  position: relative;
}

.chart-wrapper {
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 500px;
  min-height: 400px;
}

.empty-message {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
  font-size: 16px;
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.account-item {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.account-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(0, 212, 255, 0.4);
}

.account-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 15px 20px;
}

.account-name {
  font-weight: 500;
  color: #00d4ff;
  min-width: 100px;
}

.account-amounts {
  flex: 1;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 14px;
}

.account-amounts .balance {
  color: #fff;
  font-weight: 500;
}

.account-amounts .credit {
  color: #51cf66;
}

.account-amounts .debit {
  color: #ff6b6b;
}

.account-amounts .percentage {
  color: #a0aec0;
}

.expand-icon {
  color: #00d4ff;
  font-size: 16px;
}

.account-details {
  border-top: 1px solid rgba(0, 212, 255, 0.2);
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
}

.loading-details {
  text-align: center;
  padding: 20px;
  color: #a0aec0;
}

.transactions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.transaction-row {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
}

.trans-date {
  font-size: 13px;
  color: #a0aec0;
  min-width: 100px;
}

.trans-info {
  flex: 1;
  min-width: 0;
}

.trans-desc {
  font-weight: 500;
  margin-bottom: 3px;
}

.trans-category {
  font-size: 12px;
  color: #a0aec0;
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
