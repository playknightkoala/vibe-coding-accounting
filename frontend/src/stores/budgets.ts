import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import type { Budget, BudgetCreate, BudgetUpdate } from '@/types'
import { useAccountsStore } from './accounts'

export const useBudgetsStore = defineStore('budgets', () => {
  const budgets = ref<Budget[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchBudgets = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.getBudgets()
      budgets.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '載入預算時發生錯誤'
      console.error('載入預算時發生錯誤:', err)
    } finally {
      loading.value = false
    }
  }

  const createBudget = async (budgetData: BudgetCreate) => {
    loading.value = true
    error.value = null
    try {
      await api.createBudget(budgetData)
      await fetchBudgets()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '建立預算失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateBudget = async (id: number, budgetData: BudgetUpdate) => {
    loading.value = true
    error.value = null
    try {
      await api.updateBudget(id, budgetData)
      await fetchBudgets()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '更新預算失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteBudget = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await api.deleteBudget(id)
      await fetchBudgets()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '刪除預算失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const getPeriodText = (period: string) => {
    const periodMap: Record<string, string> = {
      daily: '每日',
      weekly: '每週',
      monthly: '每月',
      quarterly: '每季',
      yearly: '每年'
    }
    return periodMap[period] || period
  }

  const getAccountNames = (accountIds: number[]) => {
    const accountsStore = useAccountsStore()
    if (!accountIds || accountIds.length === 0) {
      return '所有帳戶'
    }
    const names = accountIds
      .map(id => {
        const account = accountsStore.getAccountById(id)
        return account ? account.name : '未知帳戶'
      })
      .join('、')
    return names
  }

  return {
    budgets,
    loading,
    error,
    fetchBudgets,
    createBudget,
    updateBudget,
    deleteBudget,
    getPeriodText,
    getAccountNames
  }
})
