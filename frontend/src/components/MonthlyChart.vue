<template>
  <div class="monthly-chart-container">
    <div class="chart-header">
      <h3>收入與支出趨勢</h3>
      <div class="month-selector">
        <button @click="previousMonth" class="month-btn"><span class="material-icons">chevron_left</span></button>
        <span class="current-month">{{ currentYear }}年 {{ currentMonth }}月</span>
        <button @click="nextMonth" class="month-btn"><span class="material-icons">chevron_right</span></button>
      </div>
    </div>
    <div class="chart-wrapper">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { Chart, registerables } from 'chart.js'
import type { MonthlyStats, Budget } from '@/types'
import api from '@/services/api'
import { formatAmount } from '@/utils/format'

Chart.register(...registerables)

const emit = defineEmits<{
  (e: 'dayClick', date: string): void
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const monthlyStats = ref<MonthlyStats | null>(null)
const budgets = ref<Budget[]>([])

const fetchMonthlyStats = async () => {
  try {
    const response = await api.getMonthlyStats(currentYear.value, currentMonth.value)
    monthlyStats.value = response.data
    await fetchBudgets()
    renderChart()
  } catch (error) {
    console.error('Failed to fetch monthly stats:', error)
  }
}

const fetchBudgets = async () => {
  try {
    const response = await api.getBudgets()
    // Filter budgets that overlap with current month
    const startOfMonth = new Date(currentYear.value, currentMonth.value - 1, 1)
    const endOfMonth = new Date(currentYear.value, currentMonth.value, 0, 23, 59, 59)

    budgets.value = response.data.filter(budget => {
      const budgetStart = new Date(budget.start_date)
      const budgetEnd = new Date(budget.end_date)
      // Check if budget period overlaps with current month
      return budgetStart <= endOfMonth && budgetEnd >= startOfMonth
    })
  } catch (error) {
    console.error('Failed to fetch budgets:', error)
    budgets.value = []
  }
}

const renderChart = () => {
  if (!chartCanvas.value || !monthlyStats.value) return

  // 銷毀舊圖表
  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) return

  const labels = monthlyStats.value.daily_stats.map(stat => {
    const date = new Date(stat.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  })

  const creditData = monthlyStats.value.daily_stats.map(stat => stat.credit)
  const debitData = monthlyStats.value.daily_stats.map(stat => stat.debit)

  // Prepare datasets
  const datasets: any[] = [
    {
      label: '收入',
      data: creditData,
      borderColor: '#51cf66',
      backgroundColor: 'rgba(81, 207, 102, 0.1)',
      tension: 0.3,
      fill: true,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: '#51cf66',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      order: 2,
    },
    {
      label: '支出',
      data: debitData,
      borderColor: '#ff6b6b',
      backgroundColor: 'rgba(255, 107, 107, 0.1)',
      tension: 0.3,
      fill: true,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: '#ff6b6b',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      order: 2,
    }
  ]

  // Add budget reference lines
  const budgetColors = ['#9966ff', '#ff9933', '#33ccff', '#ffcc00', '#ff6699']
  budgets.value.forEach((budget, index) => {
    const color = budgetColors[index % budgetColors.length]
    // Calculate daily budget limit
    const daysInMonth = monthlyStats.value!.daily_stats.length
    const dailyBudget = budget.daily_limit || (budget.amount / daysInMonth)

    datasets.push({
      label: `預算: ${budget.name}`,
      data: Array(daysInMonth).fill(dailyBudget),
      borderColor: color,
      backgroundColor: 'transparent',
      borderWidth: 2,
      borderDash: [5, 5],
      pointRadius: 0,
      pointHoverRadius: 0,
      fill: false,
      tension: 0,
      order: 1,
    })
  })

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      onClick: (event, elements) => {
        if (elements.length > 0) {
          const index = elements[0].index
          const date = monthlyStats.value!.daily_stats[index].date
          emit('dayClick', date)
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: '#fff',
            font: {
              size: 14,
              family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
            },
            usePointStyle: true,
            padding: 15
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: '#00d4ff',
          borderWidth: 1,
          padding: 12,
          displayColors: true,
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || ''
              if (label) {
                label += ': '
              }
              if (context.parsed.y !== null) {
                label += '$' + formatAmount(context.parsed.y)
              }
              return label
            },
            footer: function(tooltipItems) {
              const index = tooltipItems[0].dataIndex
              const credit = creditData[index]
              const debit = debitData[index]
              const net = credit - debit
              return `淨收入: $${formatAmount(net)}`
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
            drawOnChartArea: true,
          },
          ticks: {
            color: '#a0aec0',
            font: {
              size: 11
            },
            maxRotation: 45,
            minRotation: 0
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
          },
          ticks: {
            color: '#a0aec0',
            font: {
              size: 11
            },
            callback: function(value) {
              return '$' + value
            }
          }
        }
      }
    }
  })
}

const previousMonth = () => {
  if (currentMonth.value === 1) {
    currentMonth.value = 12
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

const nextMonth = () => {
  if (currentMonth.value === 12) {
    currentMonth.value = 1
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

const refresh = async () => {
  await fetchMonthlyStats()
}

watch([currentYear, currentMonth], () => {
  fetchMonthlyStats()
})

onMounted(() => {
  fetchMonthlyStats()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})

// Expose refresh method to parent component
defineExpose({
  refresh
})
</script>

<style scoped>
.monthly-chart-container {
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.05) 0%, rgba(0, 212, 255, 0.05) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.chart-header h3 {
  margin: 0;
  color: #00d4ff;
  font-size: 20px;
}

.month-selector {
  display: flex;
  align-items: center;
  gap: 15px;
}

.current-month {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  min-width: 120px;
  text-align: center;
}

.month-btn {
  background: rgba(0, 212, 255, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.4);
  color: #00d4ff;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s ease;
}

.month-btn:hover {
  background: rgba(0, 212, 255, 0.3);
  border-color: #00d4ff;
  transform: scale(1.05);
}

.month-btn:active {
  transform: scale(0.95);
}

.chart-wrapper {
  position: relative;
  height: 400px;
  width: 100%;
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: stretch;
  }

  .month-selector {
    justify-content: center;
  }

  .chart-wrapper {
    height: 300px;
  }
}
</style>
