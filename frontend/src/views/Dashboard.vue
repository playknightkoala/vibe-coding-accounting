<template>
  <div class="container">
    <h1>儀表板</h1>

    <div class="card">
      <h2>總覽</h2>

      <div style="margin-bottom: 30px;">
        <h3 style="margin-bottom: 15px;">帳戶狀況</h3>
        <div v-if="accounts.length > 0" style="display: grid; gap: 15px;">
          <div v-for="account in accounts" :key="account.id"
               style="border: 1px solid rgba(0, 212, 255, 0.2); padding: 15px; border-radius: 8px; background: rgba(0, 212, 255, 0.03); transition: all 0.3s ease;"
               @mouseenter="($event.currentTarget as HTMLElement).style.borderColor = 'rgba(0, 212, 255, 0.5)'"
               @mouseleave="($event.currentTarget as HTMLElement).style.borderColor = 'rgba(0, 212, 255, 0.2)'">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <h4 style="margin: 0 0 5px 0;">{{ account.name }}</h4>
                <p style="margin: 0; font-size: 14px; color: #a0aec0;">{{ getAccountTypeText(account.account_type) }} - {{ account.currency }}</p>
              </div>
              <div style="text-align: right; display: flex; align-items: center; gap: 15px;">
                <p style="margin: 0; font-size: 24px; font-weight: bold;"
                   :style="{ color: account.balance >= 0 ? '#51cf66' : '#ff6b6b' }">
                  {{ account.currency }} ${{ account.balance.toFixed(2) }}
                </p>
                <button @click="quickAddTransaction(account)" class="btn"
                        style="padding: 8px 15px; background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; white-space: nowrap;">
                  記帳
                </button>
              </div>
            </div>
          </div>
        </div>
        <p v-else style="color: #a0aec0;">尚無帳戶</p>
      </div>

      <div style="border-top: 2px solid rgba(0, 212, 255, 0.2); padding-top: 20px;">
        <h3 style="margin-bottom: 15px;">總額統計</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
          <div v-for="(total, currency) in totalByCurrency" :key="currency"
               style="text-align: center; padding: 15px; background: linear-gradient(135deg, rgba(0, 102, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%); border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
            <h4 style="margin: 0 0 10px 0; color: #a0aec0;">{{ currency }}</h4>
            <p style="margin: 0; font-size: 28px; font-weight: bold;"
               :style="{ color: total >= 0 ? '#51cf66' : '#ff6b6b' }">
              ${{ total.toFixed(2) }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>預算狀態</h2>
      <div v-if="budgets.length > 0" style="display: grid; gap: 15px;">
        <div v-for="budget in budgets" :key="budget.id" style="border: 1px solid rgba(0, 212, 255, 0.2); padding: 15px; border-radius: 8px; background: rgba(0, 212, 255, 0.03);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0;">{{ budget.name }}</h3>
            <span :style="{
              padding: '4px 12px',
              borderRadius: '4px',
              fontSize: '14px',
              backgroundColor: getBudgetStatusColor(budget),
              color: 'white'
            }">
              {{ getBudgetStatus(budget) }}
            </span>
          </div>
          <p style="margin: 5px 0;"><strong>類別：</strong>{{ budget.category }}</p>
          <p style="margin: 5px 0;"><strong>預算：</strong>${{ budget.amount.toFixed(2) }}</p>
          <p style="margin: 5px 0;"><strong>已使用：</strong>${{ budget.spent.toFixed(2) }}</p>
          <p style="margin: 5px 0;"><strong>剩餘：</strong>${{ (budget.amount - budget.spent).toFixed(2) }}</p>
          <div style="background-color: rgba(0, 0, 0, 0.3); height: 20px; border-radius: 10px; overflow: hidden; margin-top: 10px;">
            <div
              :style="{
                width: Math.min((budget.spent / budget.amount) * 100, 100) + '%',
                backgroundColor: budget.spent > budget.amount ? '#ff6b6b' : budget.spent > budget.amount * 0.8 ? '#ffa726' : '#51cf66',
                height: '100%',
                transition: 'width 0.3s ease',
                boxShadow: budget.spent > budget.amount ? '0 0 10px rgba(255, 107, 107, 0.5)' : budget.spent > budget.amount * 0.8 ? '0 0 10px rgba(255, 167, 38, 0.5)' : '0 0 10px rgba(81, 207, 102, 0.5)'
              }"
            ></div>
          </div>
          
          <!-- 每日預算狀態 -->
          <div v-if="budget.daily_limit" style="margin-top: 15px; border-top: 1px dashed rgba(0, 212, 255, 0.2); padding-top: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
              <p style="margin: 0; font-size: 14px;"><strong>今日預算：</strong>${{ budget.daily_limit.toFixed(2) }}</p>
              <p style="margin: 0; font-size: 14px;">
                已用: <span :style="{ color: getDailySpent(budget) > budget.daily_limit ? '#ff6b6b' : '#51cf66' }">${{ getDailySpent(budget).toFixed(2) }}</span>
              </p>
            </div>
            <div style="background-color: rgba(0, 0, 0, 0.3); height: 10px; border-radius: 5px; overflow: hidden;">
              <div
                :style="{
                  width: Math.min((getDailySpent(budget) / budget.daily_limit) * 100, 100) + '%',
                  backgroundColor: getDailySpent(budget) > budget.daily_limit ? '#ff6b6b' : '#51cf66',
                  height: '100%',
                  transition: 'width 0.3s ease'
                }"
              ></div>
            </div>
          </div>

          <p style="margin-top: 10px; font-size: 14px; color: #a0aec0;">
            <small>{{ formatDateTime(budget.start_date) }} - {{ formatDateTime(budget.end_date) }}</small>
          </p>
        </div>
      </div>
      <p v-else>尚無預算</p>
    </div>

    <div class="card">
      <h2>最近交易</h2>
      <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
        <input type="text" v-model="searchQuery" placeholder="搜尋描述..." style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; flex: 1; min-width: 150px;" />
        <input type="text" v-model="searchCategory" placeholder="搜尋類別..." style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; flex: 1; min-width: 150px;" />
        <input type="date" v-model="searchDate" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; min-width: 150px;" />
        <button @click="clearSearch" class="btn btn-secondary" style="padding: 8px 15px;">清除</button>
      </div>
      <div style="overflow-x: auto;" v-if="filteredTransactions.length > 0">
        <table class="table">
          <thead>
            <tr>
              <th>日期</th>
              <th>描述</th>
              <th>類型</th>
              <th>金額</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in filteredTransactions" :key="transaction.id">
              <td>{{ formatDateTime(transaction.transaction_date) }}</td>
              <td>{{ transaction.description }}</td>
              <td>{{ transaction.transaction_type === 'credit' ? '收入' : '支出' }}</td>
              <td :style="{ color: transaction.transaction_type === 'credit' ? '#51cf66' : '#ff6b6b' }">
                ${{ transaction.amount.toFixed(2) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else>尚無交易記錄</p>
    </div>

    <!-- 快速記帳彈窗 -->
    <div v-if="showQuickTransactionModal" class="modal">
      <div class="modal-content">
        <h2 style="color: #00d4ff;">快速記帳 - {{ selectedAccount?.name }}</h2>
        <form @submit.prevent="handleQuickTransaction">
          <div class="form-group">
            <label for="quick_description">描述</label>
            <input
              type="text"
              id="quick_description"
              v-model="quickTransactionForm.description"
              placeholder="交易描述"
              required
            />
          </div>

          <div class="form-group">
            <label for="quick_amount">金額</label>
            <input
              type="number"
              id="quick_amount"
              v-model.number="quickTransactionForm.amount"
              step="0.01"
              min="0.01"
              required
            />
          </div>

          <div class="form-group">
            <label for="quick_type">交易類型</label>
            <select id="quick_type" v-model="quickTransactionForm.transaction_type" required>
              <option value="credit">收入</option>
              <option value="debit">支出</option>
            </select>
          </div>

          <CategorySelector
            v-model="quickTransactionForm.category"
            :categories="categories"
            @open-management="showCategoryModal = true"
          />

          <div class="form-group">
            <label for="quick_date">日期時間</label>
            <input
              type="datetime-local"
              id="quick_date"
              v-model="quickTransactionForm.transaction_date"
              required
            />
          </div>

          <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button type="submit" class="btn btn-primary" style="flex: 1;">
              新增交易
            </button>
            <button type="button" @click="closeQuickTransactionModal" class="btn btn-secondary" style="flex: 1;">
              取消
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 消息提示彈窗 -->
    <MessageModal
      v-model="showMessageModal"
      :type="messageType"
      :message="message"
    />

    <!-- 類別管理彈窗 -->
    <CategoryManagementModal
      v-model="showCategoryModal"
      :categories="categories"
      @categories-changed="loadData"
      @show-message="handleShowMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { Account, Transaction, Budget, Category } from '@/types'
import CategorySelector from '@/components/CategorySelector.vue'
import CategoryManagementModal from '@/components/CategoryManagementModal.vue'
import MessageModal from '@/components/MessageModal.vue'
import { formatDateTime, formatDateTimeForBackend } from '@/utils/dateFormat'

const accounts = ref<Account[]>([])
const transactions = ref<Transaction[]>([])
const budgets = ref<Budget[]>([])
const categories = ref<Category[]>([])
const searchQuery = ref('')
const searchCategory = ref('')
const searchDate = ref('')
const showQuickTransactionModal = ref(false)
const showMessageModal = ref(false)
const showCategoryModal = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const selectedAccount = ref<Account | null>(null)

const handleShowMessage = (type: 'success' | 'error', msg: string) => {
  messageType.value = type
  message.value = msg
  showMessageModal.value = true
}

// 獲取當前日期時間
const getCurrentDateTime = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

// 快速記帳表單
const quickTransactionForm = ref({
  account_id: 0,
  transaction_type: 'debit',
  amount: 0,
  category: '',
  description: '',
  transaction_date: getCurrentDateTime()
})



const totalByCurrency = computed(() => {
  const totals: Record<string, number> = {}
  accounts.value.forEach(account => {
    if (!totals[account.currency]) {
      totals[account.currency] = 0
    }
    totals[account.currency] += account.balance
  })
  return totals
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



const filteredTransactions = computed(() => {
  let filtered = transactions.value

  if (searchQuery.value) {
    filtered = filtered.filter(transaction =>
      transaction.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  if (searchCategory.value) {
    filtered = filtered.filter(transaction =>
      transaction.category && transaction.category.toLowerCase().includes(searchCategory.value.toLowerCase())
    )
  }

  if (searchDate.value) {
    filtered = filtered.filter(transaction =>
      transaction.transaction_date.startsWith(searchDate.value)
    )
  }

  return filtered.slice(0, 20) // 顯示最多20筆搜尋結果
})

const clearSearch = () => {
  searchQuery.value = ''
  searchCategory.value = ''
  searchDate.value = ''
}

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
  
  return transactions.value
    .filter(t => {
      const isToday = t.transaction_date.startsWith(today)
      const isSameAccount = t.account_id === budget.account_id
      const isSameCategory = t.category === budget.category
      const isExpense = t.transaction_type === 'debit'
      return isToday && isSameAccount && isSameCategory && isExpense
    })
    .reduce((sum, t) => sum + t.amount, 0)
}

const loadData = async () => {
  try {
    const [accountsRes, transactionsRes, budgetsRes, categoriesRes] = await Promise.all([
      api.getAccounts(),
      api.getTransactions(),
      api.getBudgets(),
      api.getCategories()
    ])
    accounts.value = accountsRes.data
    transactions.value = transactionsRes.data
    budgets.value = budgetsRes.data
    categories.value = categoriesRes.data
  } catch (error) {
    console.error('載入資料時發生錯誤:', error)
  }
}

const quickAddTransaction = (account: Account) => {
  selectedAccount.value = account
  quickTransactionForm.value = {
    account_id: account.id,
    transaction_type: 'debit',
    amount: 0,
    category: categories.value.length > 0 ? categories.value[0].name : '',
    description: '',
    transaction_date: getCurrentDateTime()
  }
  showQuickTransactionModal.value = true
}

const handleQuickTransaction = async () => {
  try {
    const formattedDate = formatDateTimeForBackend(quickTransactionForm.value.transaction_date)
    console.log('原始時間:', quickTransactionForm.value.transaction_date)
    console.log('格式化後時間:', formattedDate)

    await api.createTransaction({
      account_id: quickTransactionForm.value.account_id,
      transaction_type: quickTransactionForm.value.transaction_type as 'debit' | 'credit',
      amount: quickTransactionForm.value.amount,
      category: quickTransactionForm.value.category,
      description: quickTransactionForm.value.description,
      transaction_date: formattedDate
    })

    // 顯示成功訊息
    messageType.value = 'success'
    message.value = '交易已成功新增！'
    showMessageModal.value = true

    // 重新載入資料
    await loadData()

    // 關閉表單並重置
    closeQuickTransactionModal()
  } catch (error: any) {
    messageType.value = 'error'
    message.value = error.response?.data?.detail || '新增交易失敗，請稍後再試'
    showMessageModal.value = true
  }
}

const closeQuickTransactionModal = () => {
  showQuickTransactionModal.value = false
  selectedAccount.value = null
  // 重置表單
  quickTransactionForm.value = {
    account_id: 0,
    transaction_type: 'debit',
    amount: 0,
    category: '',
    description: '',
    transaction_date: getCurrentDateTime()
  }
}

onMounted(loadData)
</script>
