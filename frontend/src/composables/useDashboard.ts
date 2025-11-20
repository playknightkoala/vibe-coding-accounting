import { computed } from 'vue'
import { useAccountsStore } from '@/stores/accounts'
import { useTransactionsStore } from '@/stores/transactions'
import { useBudgetsStore } from '@/stores/budgets'
import type { Account, Budget } from '@/types'

export function useDashboard() {
  const accountsStore = useAccountsStore()
  const transactionsStore = useTransactionsStore()
  const budgetsStore = useBudgetsStore()

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
    const today = new Date().toISOString().split('T')[0]

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

  return {
    totalByCurrency,
    getBudgetStatus,
    getBudgetStatusColor,
    getDailySpent
  }
}
