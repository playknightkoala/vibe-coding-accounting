<template>
  <div class="overview-report">
    <div v-if="loading" class="loading">載入中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="reportData">
      <!-- 統計卡片 -->
      <div class="stats-grid">
        <div class="stat-card income">
          <h3>收入總額</h3>
          <p class="amount">${{ formatAmount(reportData.total_credit) }}</p>
        </div>
        <div class="stat-card expense">
          <h3>支出總額</h3>
          <p class="amount">${{ formatAmount(reportData.total_debit) }}</p>
        </div>
        <div class="stat-card net" :class="reportData.net_amount >= 0 ? 'positive' : 'negative'">
          <h3>總計</h3>
          <p class="amount">${{ formatAmount(reportData.net_amount) }}</p>
        </div>
      </div>

      <!-- 各類別圓餅圖網格 -->
      <div class="card">
        <h2>類別收支統計</h2>
        <div v-if="reportData.category_stats.length > 0" class="charts-grid">
          <div
            v-for="(category, index) in reportData.category_stats"
            :key="category.category"
            class="chart-item"
          >
            <div class="chart-wrapper" :ref="el => setChartRef(el, index)"></div>
            <div class="chart-footer">
              <div class="category-name" :style="{ color: getCategoryColor(index) }">{{ category.category }}</div>
              <div
                class="net-amount"
                :class="{ 'positive': getNetAmount(category) >= 0, 'negative': getNetAmount(category) < 0 }"
              >
                {{ getNetAmount(category) >= 0 ? '+' : '' }}${{ formatAmount(getNetAmount(category)) }}
              </div>
            </div>
          </div>
        </div>
        <p v-else class="empty-message">本期沒有交易記錄</p>
      </div>

      <!-- 前五名最高消費 -->
      <div class="card">
        <div class="card-header">
          <h2>前五名{{ topTransactionType === 'expense' ? '支出' : '收入' }}</h2>
          <div class="toggle-group">
            <button
              class="toggle-btn"
              :class="{ active: topTransactionType === 'expense' }"
              @click="topTransactionType = 'expense'"
            >
              支出
            </button>
            <button
              class="toggle-btn"
              :class="{ active: topTransactionType === 'income' }"
              @click="topTransactionType = 'income'"
            >
              收入
            </button>
          </div>
        </div>

        <div class="top-transactions">
          <div v-if="currentTopTransactions.length === 0" class="empty">
            尚無交易記錄
          </div>
          <div
            v-for="(trans, index) in currentTopTransactions"
            :key="trans.id"
            class="transaction-item"
          >
            <div class="rank">{{ index + 1 }}</div>
            <div class="transaction-info">
              <div class="description">{{ trans.description }}</div>
              <div class="meta">
                <span class="category">{{ trans.category || '未分類' }}</span>
                <span class="account">{{ trans.account_name }}</span>
                <span class="date">{{ formatDate(trans.transaction_date) }}</span>
              </div>
            </div>
            <div class="trans-amount" :class="trans.transaction_type">
              ${{ formatAmount(trans.amount) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import api from '@/services/api'
import type { OverviewReport as OverviewReportType, CategoryStats } from '@/types'
import { formatAmount } from '@/utils/format'

interface Props {
  reportType: 'monthly' | 'daily' | 'custom'
  year: number
  month: number
  date: string
  startDate?: string
  endDate?: string
}

const props = defineProps<Props>()

const reportData = ref<OverviewReportType | null>(null)
const loading = ref(false)
const error = ref('')
const chartRefs = ref<(HTMLElement | null)[]>([])
const chartInstances = ref<(echarts.ECharts | null)[]>([])

const topTransactionType = ref<'expense' | 'income'>('expense')

const currentTopTransactions = computed(() => {
  if (!reportData.value) return []
  return topTransactionType.value === 'expense'
    ? reportData.value.top_five_expense
    : reportData.value.top_five_income
})

const setChartRef = (el: any, index: number) => {
  if (el) {
    chartRefs.value[index] = el
  }
}

const getNetAmount = (category: CategoryStats) => {
  return category.credit - category.debit
}

// Color palette for different categories
const categoryColors = [
  '#9966ff', '#ff9933', '#33ccff', '#ffcc00', '#ff6699',
  '#66ff99', '#ff6666', '#6699ff', '#ffcc99', '#cc99ff',
  '#99ffcc', '#ff99cc', '#cc66ff', '#66ccff', '#ffcc66'
]

const getCategoryColor = (index: number) => {
  return categoryColors[index % categoryColors.length]
}

const fetchReport = async () => {
  loading.value = true
  error.value = ''

  // Dispose old chart instances
  chartInstances.value.forEach(chart => {
    if (chart) chart.dispose()
  })
  chartInstances.value = []
  chartRefs.value = []

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getOverviewReportMonthly(props.year, props.month)
    } else if (props.reportType === 'daily') {
      response = await api.getOverviewReportDaily(props.date)
    } else if (props.reportType === 'custom' && props.startDate && props.endDate) {
      response = await api.getOverviewReportCustom(props.startDate, props.endDate)
    }
    reportData.value = response.data

    loading.value = false
    await nextTick()
    renderPieCharts()
  } catch (err: any) {
    loading.value = false
    error.value = err.response?.data?.detail || '載入報表失敗'
    console.error('Failed to fetch overview report:', err)
  }
}

const renderPieCharts = () => {
  if (!reportData.value || reportData.value.category_stats.length === 0) {
    return
  }

  // Calculate total amount for percentage calculation
  const totalAmount = reportData.value.category_stats.reduce((sum, cat) => {
    return sum + cat.credit + cat.debit
  }, 0)

  reportData.value.category_stats.forEach((category, index) => {
    const chartEl = chartRefs.value[index]
    if (!chartEl) return

    const chart = echarts.init(chartEl)
    chartInstances.value[index] = chart

    const categoryTotal = category.credit + category.debit
    const categoryPercentage = totalAmount > 0 ? (categoryTotal / totalAmount * 100) : 0
    const categoryColor = getCategoryColor(index)

    // Create data with category portion and empty portion
    const chartData = [
      {
        name: category.category,
        value: categoryPercentage,
        itemStyle: { color: categoryColor }
      },
      {
        name: '其他',
        value: 100 - categoryPercentage,
        itemStyle: {
          color: 'rgba(255, 255, 255, 0.05)',
          borderWidth: 0
        },
        label: {
          show: false
        },
        tooltip: {
          show: false
        }
      }
    ]

    const option: echarts.EChartsOption = {
      title: {
        text: `${categoryPercentage.toFixed(1)}%`,
        left: 'center',
        top: 'center',
        textStyle: {
          color: categoryColor,
          fontSize: 24,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.name === '其他') return ''
          return `${params.name}: ${params.value.toFixed(1)}%<br/>收入: $${formatAmount(category.credit)}<br/>支出: $${formatAmount(category.debit)}`
        },
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        borderColor: categoryColor,
        borderWidth: 1,
        textStyle: {
          color: '#fff'
        }
      },
      series: [
        {
          type: 'pie',
          radius: ['50%', '75%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 8,
            borderColor: 'rgba(0, 0, 0, 0.2)',
            borderWidth: 2
          },
          label: {
            show: false
          },
          emphasis: {
            scale: true,
            scaleSize: 10,
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: `${categoryColor}80`
            }
          },
          data: chartData
        }
      ]
    }

    chart.setOption(option)
  })

  const handleResize = () => {
    chartInstances.value.forEach(chart => {
      if (chart) chart.resize()
    })
  }
  window.addEventListener('resize', handleResize)
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

onBeforeUnmount(() => {
  chartInstances.value.forEach(chart => {
    if (chart) chart.dispose()
  })
  chartInstances.value = []
  window.removeEventListener('resize', () => {
    chartInstances.value.forEach(chart => {
      if (chart) chart.resize()
    })
  })
})
</script>

<style scoped>
.overview-report {
  display: flex;
  flex-direction: column;
  gap: 30px;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 10px;
}

.stat-card {
  padding: 25px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-card h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #a0aec0;
}

.stat-card .amount {
  margin: 0;
  font-size: 32px;
  font-weight: bold;
}

.stat-card.income {
  background: linear-gradient(135deg, rgba(81, 207, 102, 0.1) 0%, rgba(81, 207, 102, 0.05) 100%);
  border-color: rgba(81, 207, 102, 0.3);
}

.stat-card.income .amount {
  color: #51cf66;
}

.stat-card.expense {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 107, 107, 0.05) 100%);
  border-color: rgba(255, 107, 107, 0.3);
}

.stat-card.expense .amount {
  color: #ff6b6b;
}

.stat-card.net {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
  border-color: rgba(0, 212, 255, 0.3);
}

.stat-card.net.positive .amount {
  color: #51cf66;
}

.stat-card.net.negative .amount {
  color: #ff6b6b;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

.chart-item {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  padding: 20px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.chart-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(0, 212, 255, 0.4);
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 212, 255, 0.2);
}

.chart-wrapper {
  width: 100%;
  height: 200px;
}

.chart-footer {
  width: 100%;
  text-align: center;
  margin-top: 10px;
}

.category-name {
  font-weight: 600;
  color: #00d4ff;
  font-size: 16px;
  margin-bottom: 8px;
}

.net-amount {
  font-size: 20px;
  font-weight: bold;
  margin-top: 5px;
}

.net-amount.positive {
  color: #51cf66;
}

.net-amount.negative {
  color: #ff6b6b;
}

.empty-message {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
  font-size: 16px;
}

.top-transactions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.top-transactions .empty {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
}

.transaction-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  transition: all 0.2s;
}

.transaction-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(0, 212, 255, 0.4);
}

.rank {
  min-width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 212, 255, 0.1) 100%);
  border-radius: 50%;
  color: #00d4ff;
}

.transaction-info {
  flex: 1;
  min-width: 0;
}

.description {
  font-weight: 500;
  margin-bottom: 5px;
  color: #fff;
}

.meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 13px;
  color: #a0aec0;
}

.meta span {
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h2 {
  margin: 0;
}

.toggle-group {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 20px;
  padding: 4px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.toggle-btn {
  background: transparent;
  border: none;
  color: #a0aec0;
  padding: 6px 16px;
  border-radius: 16px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.toggle-btn.active {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
  font-weight: 500;
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

@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
  }

  .chart-wrapper {
    height: 180px;
  }

  .category-name {
    font-size: 14px;
  }

  .net-amount {
    font-size: 18px;
  }
}
</style>
