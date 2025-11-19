<template>
  <div class="container">
    <h1>交易</h1>

    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">
        <button @click="showModal = true" class="btn btn-primary">新增交易</button>
        <div style="display: flex; gap: 10px; flex-wrap: wrap; flex: 1; justify-content: flex-end; min-width: 250px;">
          <input type="text" v-model="searchQuery" placeholder="搜尋描述..." style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; flex: 1; min-width: 150px;" />
          <input type="text" v-model="searchCategory" placeholder="搜尋類別..." style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; flex: 1; min-width: 150px;" />
          <input type="date" v-model="searchDate" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; flex: 1; min-width: 150px;" />
          <button @click="clearSearch" class="btn btn-secondary" style="padding: 8px 15px;">清除</button>
        </div>
      </div>

      <div style="overflow-x: auto;" v-if="filteredTransactions.length > 0">
        <table class="table" style="margin-top: 20px;">
          <thead>
            <tr>
              <th>日期</th>
              <th>描述</th>
              <th>類型</th>
              <th>類別</th>
              <th>金額</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in filteredTransactions" :key="transaction.id">
              <td>{{ formatDateTime(transaction.transaction_date) }}</td>
              <td>{{ transaction.description }}</td>
              <td>{{ transaction.transaction_type === 'credit' ? '收入' : '支出' }}</td>
              <td>{{ transaction.category || '無' }}</td>
              <td :style="{ color: transaction.transaction_type === 'credit' ? '#51cf66' : '#ff6b6b' }">
                ${{ transaction.amount.toFixed(2) }}
              </td>
              <td>
                <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                  <button @click="editTransaction(transaction)" class="btn btn-primary" style="padding: 5px 10px;">
                    編輯
                  </button>
                  <button @click="deleteTransaction(transaction.id)" class="btn btn-danger" style="padding: 5px 10px;">
                    刪除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else style="margin-top: 20px;">尚無交易記錄</p>
    </div>

    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <h2>{{ editingTransactionId ? '編輯交易' : '新增交易' }}</h2>
        <div v-if="accounts.length === 0" class="error" style="margin-bottom: 15px;">
          請先建立帳戶才能新增交易。
        </div>
        <form @submit.prevent="editingTransactionId ? updateTransaction() : createTransaction()" v-if="accounts.length > 0">
          <div class="form-group">
            <label>帳戶</label>
            <select v-model="form.account_id" required>
              <option v-for="account in accounts" :key="account.id" :value="account.id">
                {{ account.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="form.description" required />
          </div>
          <div class="form-group">
            <label>金額</label>
            <input type="number" step="0.01" v-model.number="form.amount" required />
          </div>
          <div class="form-group">
            <label>交易類型</label>
            <select v-model="form.transaction_type" required>
              <option value="credit">收入</option>
              <option value="debit">支出</option>
            </select>
          </div>
          <CategorySelector
            v-model="form.category"
            :categories="categories"
            @open-management="showCategoryModal = true"
          />
          <div class="form-group">
            <label>日期時間</label>
            <input type="datetime-local" v-model="form.transaction_date" required />
          </div>
          <div v-if="error" class="error">{{ error }}</div>
          <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button type="submit" class="btn btn-primary">建立</button>
            <button type="button" @click="closeModal" class="btn btn-secondary">取消</button>
          </div>
        </form>
        <div v-else style="margin-top: 20px;">
          <button type="button" @click="closeModal" class="btn btn-secondary">關閉</button>
        </div>
      </div>
    </div>

    <!-- 類別管理彈窗 -->
    <CategoryManagementModal
      v-model="showCategoryModal"
      :categories="categories"
      @categories-changed="loadData"
      @show-message="handleShowMessage"
    />

    <!-- 消息提示彈窗 -->
    <MessageModal
      v-model="showMessageModal"
      :type="messageType"
      :message="message"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { Transaction, TransactionCreate, Account, Category } from '@/types'
import CategorySelector from '@/components/CategorySelector.vue'
import CategoryManagementModal from '@/components/CategoryManagementModal.vue'
import MessageModal from '@/components/MessageModal.vue'
import { formatDateTime, formatDateTimeForBackend, formatDateTimeForInput } from '@/utils/dateFormat'

const transactions = ref<Transaction[]>([])
const accounts = ref<Account[]>([])
const showModal = ref(false)
const error = ref('')
const editingTransactionId = ref<number | null>(null)
const searchQuery = ref('')
const searchCategory = ref('')
const searchDate = ref('')

// Category management
const categories = ref<Category[]>([])
const showCategoryModal = ref(false)

// Message modal
const showMessageModal = ref(false)
const messageType = ref<'success' | 'error'>('success')
const message = ref('')

const handleShowMessage = (type: 'success' | 'error', msg: string) => {
  messageType.value = type
  message.value = msg
  showMessageModal.value = true
}
const getCurrentDateTime = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const form = ref<TransactionCreate>({
  account_id: 0,
  description: '',
  amount: 0,
  transaction_type: 'debit',
  category: '',
  transaction_date: getCurrentDateTime()
})

const filteredTransactions = computed(() => {
  return transactions.value.filter(transaction => {
    const matchesDescription = searchQuery.value === '' ||
      transaction.description.toLowerCase().includes(searchQuery.value.toLowerCase())

    const matchesCategory = searchCategory.value === '' ||
      (transaction.category && transaction.category.toLowerCase().includes(searchCategory.value.toLowerCase()))

    const matchesDate = searchDate.value === '' ||
      transaction.transaction_date.startsWith(searchDate.value)

    return matchesDescription && matchesCategory && matchesDate
  })
})

const clearSearch = () => {
  searchQuery.value = ''
  searchCategory.value = ''
  searchDate.value = ''
}

const loadData = async () => {
  try {
    const [transactionsRes, accountsRes, categoriesRes] = await Promise.all([
      api.getTransactions(),
      api.getAccounts(),
      api.getCategories()
    ])
    transactions.value = transactionsRes.data
    accounts.value = accountsRes.data
    categories.value = categoriesRes.data
    // 自動選擇第一個帳戶
    if (accounts.value.length > 0 && form.value.account_id === 0) {
      form.value.account_id = accounts.value[0].id
    }
    // 自動選擇第一個類別
    if (categories.value.length > 0 && form.value.category === '') {
      form.value.category = categories.value[0].name
    }
  } catch (err) {
    console.error('載入資料時發生錯誤:', err)
  }
}

const createTransaction = async () => {
  try {
    error.value = ''
    const transactionData = {
      ...form.value,
      transaction_date: formatDateTimeForBackend(form.value.transaction_date)
    }
    await api.createTransaction(transactionData)
    showModal.value = false
    form.value = {
      account_id: 0,
      description: '',
      amount: 0,
      transaction_type: 'debit',
      category: '',
      transaction_date: getCurrentDateTime()
    }
    await loadData()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '建立交易失敗'
  }
}

const editTransaction = (transaction: Transaction) => {
  editingTransactionId.value = transaction.id
  form.value = {
    account_id: transaction.account_id,
    description: transaction.description,
    amount: transaction.amount,
    transaction_type: transaction.transaction_type,
    category: transaction.category || '',
    transaction_date: formatDateTimeForInput(transaction.transaction_date)
  }
  showModal.value = true
}

const updateTransaction = async () => {
  if (!editingTransactionId.value) return
  try {
    error.value = ''
    await api.updateTransaction(editingTransactionId.value, {
      description: form.value.description,
      amount: form.value.amount,
      category: form.value.category,
      transaction_date: formatDateTimeForBackend(form.value.transaction_date)
    })
    showModal.value = false
    editingTransactionId.value = null
    form.value = {
      account_id: 0,
      description: '',
      amount: 0,
      transaction_type: 'debit',
      category: '',
      transaction_date: getCurrentDateTime()
    }
    await loadData()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '更新交易失敗'
  }
}

const deleteTransaction = async (id: number) => {
  if (confirm('確定要刪除此交易嗎？')) {
    try {
      await api.deleteTransaction(id)
      await loadData()
    } catch (err) {
      console.error('刪除交易時發生錯誤:', err)
    }
  }
}

const closeModal = () => {
  showModal.value = false
  editingTransactionId.value = null
  error.value = ''
  form.value = {
    account_id: 0,
    description: '',
    amount: 0,
    transaction_type: 'debit',
    category: '',
    transaction_date: getCurrentDateTime()
  }
}

onMounted(() => {
  loadData()
})
</script>
