<template>
  <div class="calendar-layout">
    <div class="calendar-container">
      <div class="calendar-header">
        <button @click="previousMonth" class="btn btn-secondary calendar-nav-btn">
          ◄
        </button>
        <h3 class="calendar-title">{{ currentYear }} 年 {{ currentMonth }} 月</h3>
        <button @click="nextMonth" class="btn btn-secondary calendar-nav-btn">
          ►
        </button>
      </div>

      <div class="calendar-grid">
        <div class="calendar-weekday" v-for="day in weekDays" :key="day">
          {{ day }}
        </div>

        <div
          v-for="day in calendarDays"
          :key="day.date"
          :class="['calendar-day', {
            'other-month': !day.isCurrentMonth,
            'today': day.isToday,
            'has-transactions': day.hasTransactions && day.isCurrentMonth,
            'selected': day.date === internalSelectedDate
          }]"
          @click="selectDate(day)"
        >
          <div class="day-number">{{ day.dayNumber }}</div>
        </div>
      </div>
    </div>

    <div class="transactions-panel">
      <div v-if="internalSelectedDate" class="panel-header">
        <h3>{{ formatSelectedDate(internalSelectedDate) }}</h3>
      </div>
      <div class="transactions-list">
        <div v-if="selectedDateTransactions.length > 0">
          <div v-for="transaction in selectedDateTransactions" :key="transaction.id" class="transaction-item" @click="emit('edit-transaction', transaction)">
            <div class="transaction-info">
              <div class="transaction-time">{{ formatTime(transaction.transaction_date) }}</div>
              <div class="transaction-description">{{ transaction.description }}</div>
              <div class="transaction-category">{{ transaction.category || '無類別' }}</div>
            </div>
            <div :class="['transaction-amount', transaction.transaction_type]">
              {{ transaction.transaction_type === 'credit' ? '+' : '-' }}${{ transaction.amount.toFixed(2) }}
            </div>
          </div>
        </div>
        <div v-else class="no-transactions">
          <p v-if="internalSelectedDate">此日期無交易記錄</p>
          <p v-else>請選擇日期以查看交易明細</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Transaction } from '@/types'

const props = defineProps<{
  transactions: Transaction[]
  selectedDate?: string
}>()

const emit = defineEmits<{
  (e: 'date-selected', date: string): void
  (e: 'edit-transaction', transaction: Transaction): void
}>()

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const internalSelectedDate = ref('')

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

// Get transactions for the selected date
const selectedDateTransactions = computed(() => {
  if (!internalSelectedDate.value) return []
  return props.transactions.filter(t =>
    t.transaction_date.startsWith(internalSelectedDate.value)
  ).sort((a, b) =>
    new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime()
  )
})

// Format selected date for display
const formatSelectedDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const weekDay = ['日', '一', '二', '三', '四', '五', '六'][date.getDay()]
  return `${year} 年 ${month} 月 ${day} 日 (${weekDay})`
}

// Format time from datetime
const formatTime = (dateTimeStr: string) => {
  const date = new Date(dateTimeStr)
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${hours}:${minutes}`
}

interface CalendarDay {
  date: string
  dayNumber: number
  isCurrentMonth: boolean
  isToday: boolean
  hasTransactions: boolean
  transactionCount: number
  netAmount: number
}

const calendarDays = computed<CalendarDay[]>(() => {
  const year = currentYear.value
  const month = currentMonth.value

  // First day of the month
  const firstDay = new Date(year, month - 1, 1)
  const firstDayOfWeek = firstDay.getDay() // 0 = Sunday

  // Last day of the month
  const lastDay = new Date(year, month, 0)
  const daysInMonth = lastDay.getDate()

  // Previous month
  const prevMonthLastDay = new Date(year, month - 1, 0).getDate()

  const days: CalendarDay[] = []
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  // Previous month days
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const dayNum = prevMonthLastDay - i
    const prevMonth = month === 1 ? 12 : month - 1
    const prevYear = month === 1 ? year - 1 : year
    const dateStr = `${prevYear}-${String(prevMonth).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`

    days.push({
      date: dateStr,
      dayNumber: dayNum,
      isCurrentMonth: false,
      isToday: dateStr === todayStr,
      hasTransactions: false,
      transactionCount: 0,
      netAmount: 0
    })
  }

  // Current month days
  for (let i = 1; i <= daysInMonth; i++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    const dayTransactions = props.transactions.filter(t => t.transaction_date.startsWith(dateStr))

    let netAmount = 0
    dayTransactions.forEach(t => {
      if (t.transaction_type === 'credit') {
        netAmount += t.amount
      } else {
        netAmount -= t.amount
      }
    })

    days.push({
      date: dateStr,
      dayNumber: i,
      isCurrentMonth: true,
      isToday: dateStr === todayStr,
      hasTransactions: dayTransactions.length > 0,
      transactionCount: dayTransactions.length,
      netAmount: netAmount
    })
  }

  // Next month days to fill the grid
  const remainingDays = 42 - days.length // 6 rows * 7 days
  for (let i = 1; i <= remainingDays; i++) {
    const nextMonth = month === 12 ? 1 : month + 1
    const nextYear = month === 12 ? year + 1 : year
    const dateStr = `${nextYear}-${String(nextMonth).padStart(2, '0')}-${String(i).padStart(2, '0')}`

    days.push({
      date: dateStr,
      dayNumber: i,
      isCurrentMonth: false,
      isToday: dateStr === todayStr,
      hasTransactions: false,
      transactionCount: 0,
      netAmount: 0
    })
  }

  return days
})

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

const selectDate = (day: CalendarDay) => {
  if (day.isCurrentMonth) {
    internalSelectedDate.value = day.date
    emit('date-selected', day.date)
  }
}

// Watch for external changes to selectedDate
watch(() => props.selectedDate, (newDate) => {
  if (newDate) {
    internalSelectedDate.value = newDate
  }
}, { immediate: true })

// Watch for transaction changes
watch(() => props.transactions, () => {
  // Calendar will auto-update via computed
}, { deep: true })
</script>

<style scoped>
.calendar-layout {
  display: flex;
  gap: 20px;
  height: 600px;
}

.calendar-container {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.transactions-panel {
  flex: 0 0 350px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.3);
}

.panel-header h3 {
  margin: 0;
  color: #00d4ff;
  font-size: 1.1rem;
}

.transactions-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 212, 255, 0.3) rgba(0, 0, 0, 0.2);
}

.transactions-list::-webkit-scrollbar {
  width: 6px;
}

.transactions-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.transactions-list::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 3px;
}

.transactions-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 212, 255, 0.5);
}

.transaction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  transition: all 0.2s ease;
  cursor: pointer;
}

.transaction-item:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: #00d4ff;
}

.transaction-info {
  flex: 1;
  min-width: 0;
}

.transaction-time {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}

.transaction-description {
  font-size: 1rem;
  font-weight: 500;
  color: white;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.transaction-category {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
}

.transaction-amount {
  font-size: 1.1rem;
  font-weight: bold;
  margin-left: 12px;
  flex-shrink: 0;
}

.transaction-amount.credit {
  color: #51cf66;
}

.transaction-amount.debit {
  color: #ff6b6b;
}

.no-transactions {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.calendar-title {
  color: #00d4ff;
  margin: 0;
  font-size: 1.5rem;
}

.calendar-nav-btn {
  padding: 8px 16px;
  font-size: 1.2rem;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.calendar-weekday {
  text-align: center;
  padding: 10px;
  font-weight: bold;
  color: #00d4ff;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 4px;
}

.calendar-day {
  min-height: 50px;
  padding: 4px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.calendar-day:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: #00d4ff;
  transform: translateY(-2px);
}

.calendar-day.other-month {
  opacity: 0.3;
  cursor: not-allowed;
}

.calendar-day.other-month:hover {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(0, 212, 255, 0.2);
  transform: none;
}

.calendar-day.today {
  border-color: #00d4ff;
  border-width: 2px;
}

.calendar-day.has-transactions .day-number {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #51cf66;
  border-radius: 50%;
  background: rgba(81, 207, 102, 0.1);
}

.calendar-day.selected {
  background: rgba(0, 212, 255, 0.2);
  border-color: #00d4ff;
  border-width: 2px;
}

.day-number {
  font-size: 0.95rem;
  font-weight: bold;
  color: white;
}

@media (max-width: 768px) {
  .calendar-layout {
    flex-direction: column;
    height: auto;
  }

  .transactions-panel {
    flex: 0 0 auto;
    max-height: 400px;
  }

  .calendar-grid {
    gap: 2px;
  }

  .calendar-day {
    min-height: 40px;
    padding: 2px;
  }

  .day-number {
    font-size: 0.85rem;
  }

  .calendar-day.has-transactions .day-number {
    width: 28px;
    height: 28px;
  }

  .calendar-title {
    font-size: 1.2rem;
  }

  .calendar-nav-btn {
    padding: 6px 12px;
    font-size: 1rem;
  }

  .transaction-description {
    font-size: 0.95rem;
  }

  .transaction-amount {
    font-size: 1rem;
  }
}
</style>
