<template>
  <div class="container">
    <h1>帳戶</h1>

    <div class="card">
      <button @click="showModal = true" class="btn btn-primary">新增帳戶</button>

      <div style="overflow-x: auto;" v-if="accounts.length > 0">
        <table class="table" style="margin-top: 20px;">
          <thead>
            <tr>
              <th>名稱</th>
              <th>類型</th>
              <th>餘額</th>
              <th>幣別</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="account in accounts" :key="account.id">
              <td>{{ account.name }}</td>
              <td>{{ getAccountTypeText(account.account_type) }}</td>
              <td>${{ account.balance.toFixed(2) }}</td>
              <td>{{ account.currency }}</td>
              <td>
                <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                  <button @click="editAccount(account)" class="btn btn-primary" style="padding: 5px 10px;">
                    編輯
                  </button>
                  <button @click="deleteAccount(account.id)" class="btn btn-danger" style="padding: 5px 10px;">
                    刪除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else style="margin-top: 20px;">尚無帳戶</p>
    </div>

    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <h2>{{ editingAccountId ? '編輯帳戶' : '新增帳戶' }}</h2>
        <form @submit.prevent="editingAccountId ? updateAccount() : createAccount()">
          <div class="form-group">
            <label>帳戶名稱</label>
            <input v-model="form.name" required />
          </div>
          <div class="form-group">
            <label>帳戶類型</label>
            <select v-model="form.account_type" required>
              <option value="asset">資產</option>
              <option value="liability">負債</option>
              <option value="equity">權益</option>
              <option value="revenue">收入</option>
              <option value="expense">費用</option>
            </select>
          </div>
          <div class="form-group">
            <label>幣別</label>
            <select v-model="form.currency" required>
              <option value="NTD">NTD</option>
              <option value="USD">USD</option>
              <option value="JPY">JPY</option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="form.description"></textarea>
          </div>
          <div v-if="error" class="error">{{ error }}</div>
          <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button type="submit" class="btn btn-primary">建立</button>
            <button type="button" @click="closeModal" class="btn btn-secondary">取消</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import type { Account, AccountCreate } from '@/types'

const accounts = ref<Account[]>([])
const showModal = ref(false)
const error = ref('')
const editingAccountId = ref<number | null>(null)
const form = ref<AccountCreate>({
  name: '',
  account_type: 'asset',
  currency: 'NTD',
  description: ''
})

const accountTypeMap: Record<string, string> = {
  asset: '資產',
  liability: '負債',
  equity: '權益',
  revenue: '收入',
  expense: '費用'
}

const getAccountTypeText = (type: string) => {
  return accountTypeMap[type] || type
}

const loadAccounts = async () => {
  try {
    const response = await api.getAccounts()
    accounts.value = response.data
  } catch (err) {
    console.error('載入帳戶時發生錯誤:', err)
  }
}

const createAccount = async () => {
  try {
    error.value = ''
    await api.createAccount(form.value)
    showModal.value = false
    form.value = {
      name: '',
      account_type: 'asset',
      currency: 'NTD',
      description: ''
    }
    await loadAccounts()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '建立帳戶失敗'
  }
}

const editAccount = (account: Account) => {
  editingAccountId.value = account.id
  form.value = {
    name: account.name,
    account_type: account.account_type,
    currency: account.currency,
    description: account.description || ''
  }
  showModal.value = true
}

const updateAccount = async () => {
  if (!editingAccountId.value) return
  try {
    error.value = ''
    await api.updateAccount(editingAccountId.value, {
      name: form.value.name,
      description: form.value.description
    })
    showModal.value = false
    editingAccountId.value = null
    form.value = {
      name: '',
      account_type: 'asset',
      currency: 'NTD',
      description: ''
    }
    await loadAccounts()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '更新帳戶失敗'
  }
}

const deleteAccount = async (id: number) => {
  if (confirm('確定要刪除此帳戶嗎？')) {
    try {
      await api.deleteAccount(id)
      await loadAccounts()
    } catch (err) {
      console.error('刪除帳戶時發生錯誤:', err)
    }
  }
}

const closeModal = () => {
  showModal.value = false
  editingAccountId.value = null
  error.value = ''
  form.value = {
    name: '',
    account_type: 'asset',
    currency: 'NTD',
    description: ''
  }
}

onMounted(loadAccounts)
</script>
