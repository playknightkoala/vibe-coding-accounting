<template>
  <div class="category-report">
    <div v-if="loading" class="loading">載入中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="reportData">
      <!-- 頁籤切換（放在最上方中間） -->
      <div v-if="hasDebitOrCredit" class="category-tabs-container">
        <div class="category-tabs">
          <button
            :class="['category-tab-btn', categoryTab === 'debit' ? 'active' : '']"
            @click="categoryTab = 'debit'"
          >
            <span class="tab-icon">📊</span>
            支出類別
            <span class="tab-amount">${{ reportData.total_debit.toFixed(2) }}</span>
          </button>
          <button
            :class="['category-tab-btn', categoryTab === 'credit' ? 'active' : '']"
            @click="categoryTab = 'credit'"
          >
            <span class="tab-icon">💰</span>
            收入類別
            <span class="tab-amount">${{ reportData.total_credit.toFixed(2) }}</span>
          </button>
        </div>
      </div>

      <!-- 圓餅圖 -->
      <div class="card">
        <h2>{{ categoryTab === 'debit' ? '支出' : '收入' }}類別統計</h2>

        <!-- 圖表顯示區域 -->
        <div v-if="hasDebitOrCredit" class="chart-display">
          <!-- 支出圓餅圖 -->
          <div v-show="categoryTab === 'debit'" class="chart-wrapper">
            <div v-if="reportData.total_debit > 0" ref="debitChartContainer" class="chart-container"></div>
            <p v-else class="empty-message">本期沒有支出記錄</p>
          </div>

          <!-- 收入圓餅圖 -->
          <div v-show="categoryTab === 'credit'" class="chart-wrapper">
            <div v-if="reportData.total_credit > 0" ref="creditChartContainer" class="chart-container"></div>
            <p v-else class="empty-message">本期沒有收入記錄</p>
          </div>
        </div>

        <p v-else class="empty-message">本期沒有任何交易記錄</p>
      </div>

      <!-- 各類別收支明細（跟隨頁籤切換） -->
      <div class="card">
        <h2>{{ categoryTab === 'debit' ? '支出' : '收入' }}類別明細</h2>
        <p v-if="filteredCategories.length === 0" class="empty-message">
          本期沒有{{ categoryTab === 'debit' ? '支出' : '收入' }}記錄
        </p>
        <div v-else class="category-list">
          <div
            v-for="category in filteredCategories"
            :key="category.category"
            :ref="el => setCategoryItemRef(el, category.category)"
            class="category-item"
            @click="toggleCategory(category.category)"
          >
            <div class="category-header">
              <div class="category-name">{{ category.category }}</div>
              <div class="category-amounts">
                <span :class="categoryTab === 'debit' ? 'debit' : 'credit'">
                  {{ categoryTab === 'debit' ? '支出' : '收入' }}: ${{ currentAmount(category).toFixed(2) }}
                </span>
                <span class="percentage">({{ currentPercentage(category).toFixed(1) }}%)</span>
              </div>
              <div class="expand-icon">{{ expandedCategory === category.category ? '▼' : '▶' }}</div>
            </div>

            <!-- 該類別的明細 -->
            <div v-if="expandedCategory === category.category" class="category-details">
              <div v-if="categoryTransactions.length === 0" class="loading-details">載入中...</div>
              <div v-else class="transactions-list">
                <div
                  v-for="trans in categoryTransactions"
                  :key="trans.id"
                  class="transaction-row"
                >
                  <div class="trans-date">{{ formatDate(trans.transaction_date) }}</div>
                  <div class="trans-info">
                    <div class="trans-desc">{{ trans.description }}</div>
                    <div class="trans-account">{{ trans.account_name }}</div>
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
import type { CategoryReport as CategoryReportType, TransactionDetail } from '@/types'

interface Props {
  reportType: 'monthly' | 'daily' | 'custom'
  year: number
  month: number
  date: string
  startDate?: string
  endDate?: string
}

const props = defineProps<Props>()

const reportData = ref<CategoryReportType | null>(null)
const loading = ref(false)
const error = ref('')
const categoryTab = ref<'debit' | 'credit'>('debit')
const debitChartContainer = ref<HTMLElement | null>(null)
const creditChartContainer = ref<HTMLElement | null>(null)
let debitChartInstance: echarts.ECharts | null = null
let creditChartInstance: echarts.ECharts | null = null

const expandedCategory = ref<string>('')
const categoryTransactions = ref<TransactionDetail[]>([])
const categoryItemRefs = ref<Map<string, HTMLElement>>(new Map())

const chartColors = [
  '#9966ff', '#ff9933', '#33ccff', '#ffcc00', '#ff6699',
  '#66ff99', '#ff6666', '#6699ff', '#ffcc99', '#cc99ff'
]

const hasDebitOrCredit = computed(() => {
  if (!reportData.value) return false
  return reportData.value.total_debit > 0 || reportData.value.total_credit > 0
})

// 根據當前頁籤過濾類別（只顯示有對應類型交易的類別）
const filteredCategories = computed(() => {
  if (!reportData.value) return []

  return reportData.value.category_stats.filter(cat => {
    if (categoryTab.value === 'debit') {
      return cat.debit > 0
    } else {
      return cat.credit > 0
    }
  }).sort((a, b) => {
    // 根據當前頁籤類型排序
    const amountA = categoryTab.value === 'debit' ? a.debit : a.credit
    const amountB = categoryTab.value === 'debit' ? b.debit : b.credit
    return amountB - amountA
  })
})

// 獲取當前類型的金額
const currentAmount = (category: any) => {
  return categoryTab.value === 'debit' ? category.debit : category.credit
}

// 計算當前類型的百分比
const currentPercentage = (category: any) => {
  const total = categoryTab.value === 'debit'
    ? reportData.value?.total_debit || 0
    : reportData.value?.total_credit || 0

  const amount = currentAmount(category)
  return total > 0 ? (amount / total * 100) : 0
}

const setCategoryItemRef = (el: any, categoryName: string) => {
  if (el) {
    categoryItemRefs.value.set(categoryName, el)
  }
}

const fetchReport = async () => {
  loading.value = true
  error.value = ''
  expandedCategory.value = ''

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getCategoryReportMonthly(props.year, props.month)
    } else if (props.reportType === 'daily') {
      response = await api.getCategoryReportDaily(props.date)
    } else if (props.reportType === 'custom' && props.startDate && props.endDate) {
      response = await api.getCategoryReportCustom(props.startDate, props.endDate)
    }
    reportData.value = response.data

    // 智能設置初始頁籤：如果只有一種類型有數據，切換到該頁籤
    if (reportData.value.total_debit === 0 && reportData.value.total_credit > 0) {
      categoryTab.value = 'credit'
    } else {
      categoryTab.value = 'debit'
    }

    loading.value = false
    await nextTick()
    renderPieCharts()
  } catch (err: any) {
    loading.value = false
    error.value = err.response?.data?.detail || '載入報表失敗'
    console.error('Failed to fetch category report:', err)
  }
}

const renderPieCharts = () => {
  if (!reportData.value || reportData.value.category_stats.length === 0) {
    return
  }

  // Render debit chart
  renderChart(
    debitChartContainer,
    debitChartInstance,
    'debit',
    reportData.value.total_debit,
    '#ff6b6b',
    '支出'
  )

  // Render credit chart
  renderChart(
    creditChartContainer,
    creditChartInstance,
    'credit',
    reportData.value.total_credit,
    '#51cf66',
    '收入'
  )
}

const renderChart = (
  containerRef: any,
  chartInstanceRef: echarts.ECharts | null,
  type: 'debit' | 'credit',
  totalAmount: number,
  themeColor: string,
  label: string
) => {
  if (!containerRef.value || !reportData.value || totalAmount === 0) {
    return
  }

  // Dispose existing chart
  if (chartInstanceRef) {
    chartInstanceRef.dispose()
    chartInstanceRef = null
  }

  // Filter categories that have this type of transaction
  const filteredStats = reportData.value.category_stats.filter(cat =>
    type === 'debit' ? cat.debit > 0 : cat.credit > 0
  )

  if (filteredStats.length === 0) {
    return
  }

  // Create new chart instance
  const newChartInstance = echarts.init(containerRef.value)

  // Update the ref based on type
  if (type === 'debit') {
    debitChartInstance = newChartInstance
  } else {
    creditChartInstance = newChartInstance
  }

  const chartData = filteredStats.map((cat, index) => ({
    name: cat.category,
    value: type === 'debit' ? cat.debit : cat.credit,
    itemStyle: {
      color: chartColors[index % chartColors.length]
    }
  }))

  const option: echarts.EChartsOption = {
    title: {
      text: `總${label}\n$${totalAmount.toFixed(2)}`,
      left: 'center',
      top: 'center',
      textStyle: {
        color: themeColor,
        fontSize: 18,
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
      borderColor: themeColor,
      borderWidth: 1,
      textStyle: {
        color: '#fff'
      }
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      textStyle: {
        color: '#fff',
        fontSize: 11
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
          fontSize: 11
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: `rgba(${type === 'debit' ? '255, 107, 107' : '81, 207, 102'}, 0.5)`
          }
        },
        data: chartData
      }
    ]
  }

  newChartInstance.setOption(option)

  newChartInstance.on('click', (params) => {
    if (params.componentType === 'series') {
      const category = params.name
      const value = params.value as number
      const percent = params.percent

      // Update title
      newChartInstance?.setOption({
        title: {
          text: `${category}\n$${value.toFixed(2)}`,
          subtext: `${percent}%`
        }
      })

      // Expand list item
      if (expandedCategory.value !== category) {
        toggleCategory(category)
      }
    }
  })

  // Reset title when clicking on empty area
  newChartInstance.getZr().on('click', (params) => {
    if (!params.target) {
      newChartInstance?.setOption({
        title: {
          text: `總${label}\n$${totalAmount.toFixed(2)}`,
          subtext: ''
        }
      })

      if (expandedCategory.value) {
        toggleCategory(expandedCategory.value)
      }
    }
  })
}

const toggleCategory = async (category: string) => {
  if (expandedCategory.value === category) {
    expandedCategory.value = ''
    categoryTransactions.value = []
    return
  }

  expandedCategory.value = category
  categoryTransactions.value = []

  try {
    let response
    if (props.reportType === 'monthly') {
      response = await api.getCategoryTransactionsMonthly(category, props.year, props.month)
    } else {
      response = await api.getCategoryTransactionsDaily(category, props.date)
    }
    categoryTransactions.value = response.data

    // Scroll to the category item after data is loaded
    await nextTick()
    scrollToCategoryItem(category)
  } catch (err: any) {
    console.error('Failed to fetch category transactions:', err)
  }
}

const scrollToCategoryItem = (categoryName: string) => {
  const element = categoryItemRefs.value.get(categoryName)
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

// 當切換頁籤時，調整圖表大小
watch(categoryTab, async () => {
  await nextTick()
  if (categoryTab.value === 'debit' && debitChartInstance) {
    debitChartInstance.resize()
  } else if (categoryTab.value === 'credit' && creditChartInstance) {
    creditChartInstance.resize()
  }
})

onMounted(() => {
  fetchReport()
})

onBeforeUnmount(() => {
  if (debitChartInstance) {
    debitChartInstance.dispose()
    debitChartInstance = null
  }
  if (creditChartInstance) {
    creditChartInstance.dispose()
    creditChartInstance = null
  }
  window.removeEventListener('resize', () => {
    debitChartInstance?.resize()
    creditChartInstance?.resize()
  })
})
</script>

<style scoped>
.category-report {
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

/* 頁籤容器 - 居中顯示 */
.category-tabs-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

/* 頁籤切換樣式 */
.category-tabs {
  display: inline-flex;
  gap: 15px;
  background: rgba(0, 0, 0, 0.2);
  padding: 8px;
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.category-tab-btn {
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

.category-tab-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  color: #fff;
  border-color: rgba(0, 212, 255, 0.3);
}

.category-tab-btn.active {
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

.category-tab-btn.active .tab-amount {
  background: rgba(0, 212, 255, 0.2);
  color: #00d4ff;
}

/* 圖表顯示區域 */
.chart-display {
  margin-top: 20px;
}

.chart-wrapper {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chart-container {
  width: 100%;
  height: 550px;
  min-height: 450px;
}

@media (max-width: 768px) {
  .category-tabs-container {
    padding: 0 10px;
  }

  .category-tabs {
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }

  .category-tab-btn {
    width: 100%;
    justify-content: center;
  }

  .chart-container {
    height: 400px;
    min-height: 350px;
  }

  .tab-amount {
    margin-left: 10px;
  }
}

.empty-message {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
  font-size: 16px;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.category-item {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(0, 212, 255, 0.4);
}

.category-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 15px 20px;
}

.category-name {
  font-weight: 500;
  color: #00d4ff;
  min-width: 100px;
}

.category-amounts {
  flex: 1;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  font-size: 14px;
}

.category-amounts .credit {
  color: #51cf66;
}

.category-amounts .debit {
  color: #ff6b6b;
}

.category-amounts .percentage {
  color: #a0aec0;
}

.expand-icon {
  color: #00d4ff;
  font-size: 16px;
}

.category-details {
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

.trans-account {
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
