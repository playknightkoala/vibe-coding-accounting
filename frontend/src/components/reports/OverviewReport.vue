<template>
  <div class="overview-report">
    <div v-if="loading" class="loading">載入中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="reportData">
      <!-- 統計卡片 -->
      <div class="stats-grid">
        <div class="stat-card income">
          <h3>收入總額</h3>
          <p class="amount">${{ reportData.total_credit.toFixed(2) }}</p>
        </div>
        <div class="stat-card expense">
          <h3>支出總額</h3>
          <p class="amount">${{ reportData.total_debit.toFixed(2) }}</p>
        </div>
        <div class="stat-card net" :class="reportData.net_amount >= 0 ? 'positive' : 'negative'">
          <h3>淨收入</h3>
          <p class="amount">${{ reportData.net_amount.toFixed(2) }}</p>
        </div>
      </div>

      <!-- 類別占比圓餅圖 -->
      <div class="card">
        <h2>類別占比</h2>
        <div v-if="reportData.category_stats.length > 0" ref="chartContainer" class="chart-container"></div>
        <p v-else class="empty-message">本期沒有支出記錄</p>
      </div>

      <!-- 前五名最高消費 -->
      <div class="card">
        <h2>前五名最高消費</h2>
        <div class="top-transactions">
          <div v-if="reportData.top_five_transactions.length === 0" class="empty">
            尚無交易記錄
          </div>
          <div
            v-for="(trans, index) in reportData.top_five_transactions"
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
            <div class="amount" :class="trans.transaction_type">
              ${{ trans.amount.toFixed(2) }}
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
import type { OverviewReport as OverviewReportType } from '@/types'

interface Props {
  reportType: 'monthly' | 'daily'
  year: number
  month: number
  date: string
}

const props = defineProps<Props>()

const reportData = ref<OverviewReportType | null>(null)
const loading = ref(false)
const error = ref('')
const chartContainer = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const chartColors = [
  '#9966ff', '#ff9933', '#33ccff', '#ffcc00', '#ff6699',
  '#66ff99', '#ff6666', '#6699ff', '#ffcc99', '#cc99ff'
]

const fetchReport = async () => {
  loading.value = true
  error.value = ''

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getOverviewReportMonthly(props.year, props.month)
    } else {
      response = await api.getOverviewReportDaily(props.date)
    }
    reportData.value = response.data

    console.log('=== Overview Report Data ===')
    console.log('Full response:', response.data)
    console.log('Category stats:', response.data.category_stats)
    console.log('Category stats length:', response.data.category_stats?.length)

    await nextTick()
    renderPieChart()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '載入報表失敗'
    console.error('Failed to fetch overview report:', err)
  } finally {
    loading.value = false
  }
}

const renderPieChart = () => {
  console.log('=== renderPieChart called ===')
  console.log('chartContainer.value:', chartContainer.value)
  console.log('reportData.value:', reportData.value)
  console.log('category_stats length:', reportData.value?.category_stats?.length)

  if (!chartContainer.value) {
    console.error('Chart container is null!')
    return
  }

  if (!reportData.value) {
    console.error('Report data is null!')
    return
  }

  if (reportData.value.category_stats.length === 0) {
    console.warn('No category stats data!')
    return
  }

  // 如果圖表實例已存在，先銷毀
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  console.log('Initializing ECharts...')
  // 初始化 ECharts
  chartInstance = echarts.init(chartContainer.value)
  console.log('ECharts instance created:', chartInstance)

  // 準備數據
  const chartData = reportData.value.category_stats.map((cat, index) => ({
    name: cat.category,
    value: cat.debit,
    itemStyle: {
      color: chartColors[index % chartColors.length]
    }
  }))

  // 配置選項
  const option: echarts.EChartsOption = {
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
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 10,
          borderColor: 'rgba(0, 0, 0, 0.2)',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          color: '#fff'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
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

  // 設置選項
  console.log('Setting chart option:', option)
  chartInstance.setOption(option)
  console.log('Chart option set successfully!')

  // 添加窗口 resize 監聽
  const handleResize = () => {
    chartInstance?.resize()
  }
  window.addEventListener('resize', handleResize)
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
.overview-report {
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
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

.amount {
  font-size: 20px;
  font-weight: bold;
  white-space: nowrap;
}

.amount.credit {
  color: #51cf66;
}

.amount.debit {
  color: #ff6b6b;
}
</style>
