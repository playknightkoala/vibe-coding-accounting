<template>
  <div class="container">
    <h1>預算</h1>

    <div class="card">
      <button @click="openCreateModal" class="btn btn-primary">新增預算</button>

      <div v-if="budgets.length > 0" style="margin-top: 20px;">
        <div v-for="budget in budgets" :key="budget.id" class="card">
          <h3>{{ budget.name }}</h3>
          <p><strong>類別：</strong>{{ budget.category }}</p>
          <p><strong>週期：</strong>{{ getPeriodText(budget.period) }}</p>
          <p><strong>綁定帳戶：</strong>{{ getAccountName(budget.account_id) }}</p>
          <p><strong>預算：</strong>${{ budget.amount.toFixed(2) }}</p>
          <p v-if="budget.daily_limit"><strong>每日預算：</strong>${{ budget.daily_limit.toFixed(2) }}</p>
          <p><strong>已使用：</strong>${{ budget.spent.toFixed(2) }}</p>
          <p><strong>剩餘：</strong>${{ (budget.amount - budget.spent).toFixed(2) }}</p>

          <div style="background-color: rgba(0, 0, 0, 0.3); height: 20px; border-radius: 10px; overflow: hidden; margin: 10px 0;">
            <div
              :style="{
                width: Math.min((budget.spent / budget.amount) * 100, 100) + '%',
                backgroundColor: budget.spent > budget.amount ? '#ff6b6b' : '#51cf66',
                height: '100%',
                boxShadow: budget.spent > budget.amount ? '0 0 10px rgba(255, 107, 107, 0.5)' : '0 0 10px rgba(81, 207, 102, 0.5)'
              }"
            ></div>
          </div>

          <p><small>{{ formatDateTime(budget.start_date) }} - {{ formatDateTime(budget.end_date) }}</small></p>
          <div style="display: flex; gap: 5px; flex-wrap: wrap; margin-top: 10px;">
            <button @click="editBudget(budget)" class="btn btn-primary" style="padding: 5px 10px;">
              編輯
            </button>
            <button @click="deleteBudget(budget.id)" class="btn btn-danger" style="padding: 5px 10px;">
              刪除
            </button>
          </div>
        </div>
      </div>
      <p v-else style="margin-top: 20px;">尚無預算</p>
    </div>

    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <h2>{{ editingBudgetId ? '編輯預算' : '新增預算' }}</h2>
        <div v-if="accounts.length === 0 && !editingBudgetId" class="error" style="margin-bottom: 15px;">
          請先建立帳戶才能新增預算。
        </div>
        <form @submit.prevent="editingBudgetId ? updateBudget() : createBudget()" v-if="accounts.length > 0 || editingBudgetId">
          <div class="form-group">
            <label>預算名稱</label>
            <input v-model="form.name" required />
          </div>
          <CategorySelector
            v-model="form.category"
            :categories="categories"
            :required="true"
            @open-management="showCategoryModal = true"
          />
          <div class="form-group">
            <label>金額</label>
            <input type="number" step="0.01" v-model.number="form.amount" required />
          </div>
          <div class="form-group">
            <label>每日預算 (選填)</label>
            <input type="number" step="0.01" v-model.number="form.daily_limit" />
          </div>
          <div class="form-group">
            <label>週期</label>
            <select v-model="form.period" required>
              <option value="monthly">每月</option>
              <option value="quarterly">每季</option>
              <option value="yearly">每年</option>
            </select>
          </div>
          <div class="form-group">
            <label>開始日期時間</label>
            <input type="datetime-local" v-model="form.start_date" required />
          </div>
          <div class="form-group">
            <label>結束日期時間</label>
            <input type="datetime-local" v-model="form.end_date" required />
          </div>
          <div class="form-group">
            <label>綁定帳戶</label>
            <select v-model="form.account_id" required>
              <option v-for="account in accounts" :key="account.id" :value="account.id">
                {{ account.name }}
              </option>
            </select>
          </div>
          <div v-if="error" class="error">{{ error }}</div>
          <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button type="submit" class="btn btn-primary">{{ editingBudgetId ? '更新' : '建立' }}</button>
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
      @categories-changed="loadCategories"
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
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import type { Budget, BudgetCreate, Account, Category } from '@/types'
import CategorySelector from '@/components/CategorySelector.vue'
import CategoryManagementModal from '@/components/CategoryManagementModal.vue'
import MessageModal from '@/components/MessageModal.vue'
import { formatDateTime, formatDateTimeForBackend, formatDateTimeForInput } from '@/utils/dateFormat'

const getCurrentDateTime = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const getNextMonthDateTime = () => {
  const now = new Date()
  const nextMonth = new Date(now.setMonth(now.getMonth() + 1))
  const year = nextMonth.getFullYear()
  const month = String(nextMonth.getMonth() + 1).padStart(2, '0')
  const day = String(nextMonth.getDate()).padStart(2, '0')
  const hours = String(nextMonth.getHours()).padStart(2, '0')
  const minutes = String(nextMonth.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const budgets = ref<Budget[]>([])
const accounts = ref<Account[]>([])
const categories = ref<Category[]>([])
const showModal = ref(false)
const error = ref('')
const editingBudgetId = ref<number | null>(null)

// Category management
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
const form = ref<BudgetCreate>({
  name: '',
  category: '',
  amount: 0,
  daily_limit: undefined,
  period: 'monthly',
  start_date: getCurrentDateTime(),
  end_date: getNextMonthDateTime(),
  account_id: 0
})

const periodMap: Record<string, string> = {
  monthly: '每月',
  quarterly: '每季',
  yearly: '每年'
}

const getPeriodText = (period: string) => {
  return periodMap[period] || period
}

const getAccountName = (accountId: number) => {
  const account = accounts.value.find(a => a.id === accountId)
  return account ? account.name : '未知帳戶'
}

const loadBudgets = async () => {
  try {
    const response = await api.getBudgets()
    budgets.value = response.data
  } catch (err) {
    console.error('載入預算時發生錯誤:', err)
  }
}

const loadAccounts = async () => {
  try {
    const response = await api.getAccounts()
    accounts.value = response.data
    // 自動選擇第一個帳戶
    if (accounts.value.length > 0 && form.value.account_id === 0) {
      form.value.account_id = accounts.value[0].id
    }
  } catch (err) {
    console.error('載入帳戶時發生錯誤:', err)
  }
}

const loadCategories = async () => {
  try {
    const response = await api.getCategories()
    categories.value = response.data
    // 自動選擇第一個類別
    if (categories.value.length > 0 && form.value.category === '') {
      form.value.category = categories.value[0].name
    }
  } catch (err) {
    console.error('載入類別時發生錯誤:', err)
  }
}

const createBudget = async () => {
  try {
    error.value = ''
    const budgetData = {
      ...form.value,
      start_date: formatDateTimeForBackend(form.value.start_date),
      end_date: formatDateTimeForBackend(form.value.end_date)
    }
    await api.createBudget(budgetData)
    showModal.value = false
    form.value = {
      name: '',
      category: '',
      amount: 0,
      daily_limit: undefined,
      period: 'monthly',
      start_date: getCurrentDateTime(),
      end_date: getNextMonthDateTime(),
      account_id: 0
    }
    await loadBudgets()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '建立預算失敗'
  }
}

const editBudget = (budget: Budget) => {
  editingBudgetId.value = budget.id
  form.value = {
    name: budget.name,
    category: budget.category,
    amount: budget.amount,
    daily_limit: budget.daily_limit,
    period: budget.period,
    start_date: formatDateTimeForInput(budget.start_date),
    end_date: formatDateTimeForInput(budget.end_date),
    account_id: budget.account_id
  }
  showModal.value = true
}

const updateBudget = async () => {
  if (!editingBudgetId.value) return
  try {
    error.value = ''
    await api.updateBudget(editingBudgetId.value, {
      name: form.value.name,
      category: form.value.category,
      amount: form.value.amount,
      daily_limit: form.value.daily_limit,
      period: form.value.period,
      start_date: formatDateTimeForBackend(form.value.start_date),
      end_date: formatDateTimeForBackend(form.value.end_date),
      account_id: form.value.account_id
    })
    showModal.value = false
    editingBudgetId.value = null
    form.value = {
      name: '',
      category: '',
      amount: 0,
      daily_limit: undefined,
      period: 'monthly',
      start_date: getCurrentDateTime(),
      end_date: getNextMonthDateTime(),
      account_id: 0
    }
    await loadBudgets()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '更新預算失敗'
  }
}

const deleteBudget = async (id: number) => {
  if (confirm('確定要刪除此預算嗎？')) {
    try {
      await api.deleteBudget(id)
      await loadBudgets()
    } catch (err) {
      console.error('刪除預算時發生錯誤:', err)
    }
  }
}

const openCreateModal = () => {
  if (accounts.value.length === 0) {
    // 如果沒有帳戶，仍然打開模態框但會顯示提示訊息
    showModal.value = true
  } else {
    showModal.value = true
  }
}

const closeModal = () => {
  showModal.value = false
  editingBudgetId.value = null
  error.value = ''
  form.value = {
    name: '',
    category: '',
    amount: 0,
    daily_limit: undefined,
    period: 'monthly',
    start_date: getCurrentDateTime(),
    end_date: getNextMonthDateTime(),
    account_id: 0
  }
}

onMounted(async () => {
  await Promise.all([loadBudgets(), loadAccounts(), loadCategories()])
})
</script>
