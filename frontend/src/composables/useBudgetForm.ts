import { ref } from 'vue'
import type { BudgetCreate } from '@/types'
import { useDateTime } from './useDateTime'

export function useBudgetForm() {
  const dateTimeUtils = useDateTime()

  const startDateOnly = ref(dateTimeUtils.getCurrentDate())
  const endDateOnly = ref(dateTimeUtils.getNextMonthDate())

  const initialFormData: BudgetCreate = {
    name: '',
    category_names: [],
    amount: 0,
    daily_limit: undefined,
    range_mode: 'recurring',
    period: 'monthly',
    start_date: undefined,
    end_date: undefined,
    account_ids: []
  }

  const onRangeModeChange = (form: BudgetCreate) => {
    if (form.range_mode === 'recurring') {
      // 切換到週期模式,清空日期(由後端自動計算)
      form.start_date = undefined
      form.end_date = undefined
      form.period = 'monthly'
    } else {
      // 切換到自訂區間,設定日期預設值
      startDateOnly.value = dateTimeUtils.getCurrentDate()
      endDateOnly.value = dateTimeUtils.getNextMonthDate()
      form.start_date = `${startDateOnly.value}T00:00`
      form.end_date = `${endDateOnly.value}T23:59`
      form.period = undefined
    }
  }

  const updateStartDate = (form: BudgetCreate) => {
    form.start_date = `${startDateOnly.value}T00:00`
  }

  const updateEndDate = (form: BudgetCreate) => {
    form.end_date = `${endDateOnly.value}T23:59`
  }

  const resetDates = () => {
    startDateOnly.value = dateTimeUtils.getCurrentDate()
    endDateOnly.value = dateTimeUtils.getNextMonthDate()
  }

  return {
    startDateOnly,
    endDateOnly,
    initialFormData,
    onRangeModeChange,
    updateStartDate,
    updateEndDate,
    resetDates
  }
}
