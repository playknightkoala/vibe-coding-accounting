import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Account, AccountCreate, AccountUpdate } from '@/types'

export const useAccountsStore = defineStore('accounts', () => {
  const accounts = ref<Account[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchAccounts = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.getAccounts()
      accounts.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '載入帳戶時發生錯誤'
      console.error('載入帳戶時發生錯誤:', err)
    } finally {
      loading.value = false
    }
  }

  const createAccount = async (accountData: AccountCreate) => {
    loading.value = true
    error.value = null
    try {
      await api.createAccount(accountData)
      await fetchAccounts()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '建立帳戶失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateAccount = async (id: number, accountData: AccountUpdate) => {
    loading.value = true
    error.value = null
    try {
      await api.updateAccount(id, accountData)
      await fetchAccounts()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '更新帳戶失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteAccount = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await api.deleteAccount(id)
      await fetchAccounts()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '刪除帳戶失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const getAccountById = (id: number) => {
    return accounts.value.find(account => account.id === id)
  }

  const getAccountTypeText = (type: string) => {
    const accountTypeMap: Record<string, string> = {
      cash: '現金',
      bank: '銀行',
      credit_card: '信用卡',
      stored_value: '儲值卡',
      securities: '證券戶',
      other: '其他'
    }
    return accountTypeMap[type] || type
  }

  return {
    accounts,
    loading,
    error,
    fetchAccounts,
    createAccount,
    updateAccount,
    deleteAccount,
    getAccountById,
    getAccountTypeText
  }
})
