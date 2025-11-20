<template>
  <div class="account-report">
    <div v-if="loading" class="loading">載入中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="reportData">
      <!-- 圓餅圖 -->
      <div class="card">
        <h2>帳戶統計</h2>
        <div v-if="reportData.account_stats.length > 0" ref="chartContainer" class="chart-container"></div>
        <p v-else class="empty-message">本期沒有交易記錄</p>
      </div>

      <!-- 各帳戶收支總覽 -->
      <div class="card">
        <h2>帳戶收支</h2>
        <div class="account-list">
          <div
            v-for="account in reportData.account_stats"
            :key="account.account_id"
            class="account-item"
            @click="toggleAccount(account.account_id)"
          >
            <div class="account-header">
              <div class="account-name">{{ account.account_name }}</div>
              <div class="account-amounts">
                <span class="balance">餘額: ${{ account.balance.toFixed(2) }}</span>
                <span class="credit">收入: ${{ account.credit.toFixed(2) }}</span>
                <span class="debit">支出: ${{ account.debit.toFixed(2) }}</span>
                <span class="percentage">({{ account.percentage.toFixed(1) }}%)</span>
              </div>
              <div class="expand-icon">{{ expandedAccount === account.account_id ? '▼' : '▶' }}</div>
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
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/services/api'
import type { AccountReport, TransactionDetail } from '@/types'

interface Props {
  reportType: 'monthly' | 'daily'
  year: number
  month: number
  date: string
}

const props = defineProps<Props>()

const reportData = ref<AccountReport | null>(null)
const loading = ref(false)
const error = ref('')
const chartContainer = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const expandedAccount = ref<number | null>(null)
const accountTransactions = ref<TransactionDetail[]>([])

const chartColors = [
  '#9966ff', '#ff9933', '#33ccff', '#ffcc00', '#ff6699',
  '#66ff99', '#ff6666', '#6699ff', '#ffcc99', '#cc99ff'
]

const fetchReport = async () => {
  loading.value = true
  error.value = ''
  expandedAccount.value = null

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getAccountReportMonthly(props.year, props.month)
    } else {
      response = await api.getAccountReportDaily(props.date)
    }
    reportData.value = response.data

    loading.value = false
    await nextTick()
    renderPieChart()
  } catch (err: any) {
    loading.value = false
    error.value = err.response?.data?.detail || '載入報表失敗'
    console.error('Failed to fetch account report:', err)
  }
}

const renderPieChart = () => {
  if (!chartContainer.value || !reportData.value || reportData.value.account_stats.length === 0) {
    return
  }

  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  chartInstance = echarts.init(chartContainer.value)

  const chartData = reportData.value.account_stats.map((acc, index) => ({
    name: acc.account_name,
    value: acc.amount,
    itemStyle: {
      color: chartColors[index % chartColors.length]
    }
  }))

  const totalAmount = reportData.value.total_amount

  const option: echarts.EChartsOption = {
    title: {
      text: `總金額\n$${totalAmount.toFixed(2)}`,
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

  chartInstance.setOption(option)

  chartInstance.on('click', (params) => {
    if (params.componentType === 'series') {
      const accountName = params.name
      const value = params.value as number
      const percent = params.percent
      
      // Find account ID
      const account = reportData.value?.account_stats.find(acc => acc.account_name === accountName)
      
      // Update title
      chartInstance?.setOption({
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
  chartInstance.getZr().on('click', (params) => {
    if (!params.target) {
      chartInstance?.setOption({
        title: {
          text: `總金額\n$${totalAmount.toFixed(2)}`,
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
    chartInstance?.resize()
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
  } catch (err: any) {
    console.error('Failed to fetch account transactions:', err)
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

watch([() => props.reportType, () => props.year, () => props.month, () => props.date], () => {
  fetchReport()
})

onMounted(() => {
  fetchReport()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  window.removeEventListener('resize', () => chartInstance?.resize())
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
