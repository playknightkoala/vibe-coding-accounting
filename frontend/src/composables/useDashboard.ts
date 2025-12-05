import { computed, ref } from 'vue'
import { useAccountsStore } from '@/stores/accounts'
import { useTransactionsStore } from '@/stores/transactions'
import { useBudgetsStore } from '@/stores/budgets'
import type { Account, Budget } from '@/types'
import { useDateTime } from './useDateTime'

export type TimeRangeMode = 'total' | 'month' | 'day'

export function useDashboard() {
  const accountsStore = useAccountsStore()
  const transactionsStore = useTransactionsStore()
  const budgetsStore = useBudgetsStore()
  const { getTodayString } = useDateTime()

  const timeRangeMode = ref<TimeRangeMode>('month')

  const getMonthString = () => {
    const today = new Date()
    const year = today.getFullYear()
    const month = String(today.getMonth() + 1).padStart(2, '0')
    return `${year}-${month}`
  }

  const totalByCurrency = computed(() => {
    const totals: Record<string, number> = {}
    accountsStore.accounts.forEach(account => {
      if (!totals[account.currency]) {
        totals[account.currency] = 0
      }
      totals[account.currency] += account.balance
    })
    return totals
  })

  // 根據時間範圍計算收支統計
  const incomeExpenseStats = computed(() => {
    const today = getTodayString()
    const currentMonth = getMonthString()

    let filteredTransactions = transactionsStore.transactions

    if (timeRangeMode.value === 'day') {
      filteredTransactions = transactionsStore.transactions.filter(t =>
        t.transaction_date.startsWith(today)
      )
    } else if (timeRangeMode.value === 'month') {
      filteredTransactions = transactionsStore.transactions.filter(t =>
        t.transaction_date.startsWith(currentMonth)
      )
    }
    // timeRangeMode === 'total' 不過濾，使用全部交易

    const income = filteredTransactions
      .filter(t => t.transaction_type === 'credit')
      .reduce((sum, t) => sum + t.amount, 0)

    const expense = filteredTransactions
      .filter(t => t.transaction_type === 'debit' || t.transaction_type === 'installment')
      .reduce((sum, t) => sum + t.amount, 0)

    return {
      income,
      expense,
      net: income - expense
    }
  })

  const getBudgetStatus = (budget: Budget) => {
    const percentage = (budget.spent / budget.amount) * 100
    if (budget.spent > budget.amount) return '超支'
    if (percentage >= 80) return '警告'
    if (percentage >= 50) return '正常'
    return '良好'
  }

  const getBudgetStatusColor = (budget: Budget) => {
    const percentage = (budget.spent / budget.amount) * 100
    if (budget.spent > budget.amount) return '#f44336'
    if (percentage >= 80) return '#FF9800'
    if (percentage >= 50) return '#2196F3'
    return '#4CAF50'
  }

  const getDailySpent = (budget: Budget) => {
    const today = getTodayString()

    return transactionsStore.transactions
      .filter(t => {
        const isToday = t.transaction_date.startsWith(today)
        // 如果預算沒有綁定帳戶，則計算所有帳戶；否則只計算綁定的帳戶
        const isSameAccount = !budget.account_ids || budget.account_ids.length === 0 || budget.account_ids.includes(t.account_id)
        // 如果預算沒有綁定類別（空列表），則計算所有類別；否則只計算綁定的類別
        const isSameCategory = !budget.category_names || budget.category_names.length === 0 || (t.category && budget.category_names.includes(t.category))
        const isExpense = t.transaction_type === 'debit'
        return isToday && isSameAccount && isSameCategory && isExpense
      })
      .reduce((sum, t) => sum + t.amount, 0)
  }

  // 根據時間範圍計算每個帳戶的餘額變化
  const getAccountBalance = (accountId: number) => {
    const account = accountsStore.accounts.find(a => a.id === accountId)
    if (!account) return 0

    // 總體模式：返回當前餘額
    if (timeRangeMode.value === 'total') {
      return account.balance
    }

    const today = getTodayString()
    const currentMonth = getMonthString()

    // 過濾交易：根據時間範圍
    let filteredTransactions = transactionsStore.transactions.filter(t => t.account_id === accountId)

    if (timeRangeMode.value === 'day') {
      filteredTransactions = filteredTransactions.filter(t => t.transaction_date.startsWith(today))
    } else if (timeRangeMode.value === 'month') {
      filteredTransactions = filteredTransactions.filter(t => t.transaction_date.startsWith(currentMonth))
    }

    // 計算該時間範圍內的淨變化
    const netChange = filteredTransactions.reduce((sum, t) => {
      if (t.transaction_type === 'credit') {
        return sum + t.amount
      } else if (t.transaction_type === 'debit' || t.transaction_type === 'installment') {
        return sum - t.amount
      }
      return sum
    }, 0)

    return netChange
  }

  // 根據時間範圍計算總額（按幣別）
  const totalByCurrencyForTimeRange = computed(() => {
    const totals: Record<string, number> = {}

    if (timeRangeMode.value === 'total') {
      // 總體模式：顯示當前帳戶總額
      accountsStore.accounts.forEach(account => {
        if (!totals[account.currency]) {
          totals[account.currency] = 0
        }
        totals[account.currency] += account.balance
      })
    } else {
      // 本月/今日模式：顯示該時間範圍的淨變化
      accountsStore.accounts.forEach(account => {
        if (!totals[account.currency]) {
          totals[account.currency] = 0
        }
        totals[account.currency] += getAccountBalance(account.id)
      })
    }

    return totals
  })

  const setTimeRangeMode = (mode: TimeRangeMode) => {
    timeRangeMode.value = mode
  }

  return {
    totalByCurrency,
    totalByCurrencyForTimeRange,
    incomeExpenseStats,
    timeRangeMode,
    setTimeRangeMode,
    getAccountBalance,
    getBudgetStatus,
    getBudgetStatusColor,
    getDailySpent
  }
}
