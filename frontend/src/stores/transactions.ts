import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Transaction, TransactionCreate, TransactionUpdate, TransferCreate } from '@/types'

export const useTransactionsStore = defineStore('transactions', () => {
  const transactions = ref<Transaction[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchTransactions = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.getTransactions()
      transactions.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '載入交易時發生錯誤'
      console.error('載入交易時發生錯誤:', err)
    } finally {
      loading.value = false
    }
  }

  const createTransaction = async (transactionData: TransactionCreate) => {
    loading.value = true
    error.value = null
    try {
      await api.createTransaction(transactionData)

      // 更新描述歷史記錄，將此描述移到最前面
      if (transactionData.description && transactionData.description.trim()) {
        try {
          await api.updateDescriptionHistory(transactionData.description.trim())
        } catch (err) {
          console.error('更新描述歷史失敗:', err)
          // 不影響交易建立的成功，所以不拋出錯誤
        }
      }

      await fetchTransactions()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '建立交易失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateTransaction = async (id: number, transactionData: TransactionUpdate) => {
    loading.value = true
    error.value = null
    try {
      await api.updateTransaction(id, transactionData)

      // 更新描述歷史記錄，將此描述移到最前面
      if (transactionData.description && transactionData.description.trim()) {
        try {
          await api.updateDescriptionHistory(transactionData.description.trim())
        } catch (err) {
          console.error('更新描述歷史失敗:', err)
          // 不影響交易更新的成功，所以不拋出錯誤
        }
      }

      await fetchTransactions()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '更新交易失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const transfer = async (data: TransferCreate) => {
    loading.value = true
    error.value = null
    try {
      await api.transfer(data)
      await fetchTransactions()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '轉帳失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteTransaction = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await api.deleteTransaction(id)
      await fetchTransactions()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '刪除交易失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    transactions,
    loading,
    error,
    fetchTransactions,
    createTransaction,
    updateTransaction,
    transfer,
    deleteTransaction
  }
})
