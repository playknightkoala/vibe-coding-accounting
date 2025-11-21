<template>
  <div class="container">
    <h1>儀表板</h1>

    <div class="card">
      <h2>總覽</h2>

      <!-- 頁籤選單 -->
      <div class="tabs-container">
        <button
          :class="['tab-btn', activeTab === 'accounts' ? 'active' : '']"
          @click="activeTab = 'accounts'"
        >
          帳戶狀況及總額統計
        </button>
        <button
          :class="['tab-btn', activeTab === 'trends' ? 'active' : '']"
          @click="activeTab = 'trends'"
        >
          收入與支出趨勢
        </button>
      </div>

      <!-- 帳戶狀況及總額統計頁籤 -->
      <div v-if="activeTab === 'accounts'" class="tab-content">
        <div style="margin-bottom: 30px;">
          <h3 style="margin-bottom: 15px;">帳戶狀況</h3>
          <div v-if="accountsStore.accounts.length > 0" style="display: grid; gap: 15px;">
            <div v-for="account in accountsStore.accounts" :key="account.id"
                 style="border: 1px solid rgba(0, 212, 255, 0.2); padding: 15px; border-radius: 8px; background: rgba(0, 212, 255, 0.03); transition: all 0.3s ease;"
                 @mouseenter="($event.currentTarget as HTMLElement).style.borderColor = 'rgba(0, 212, 255, 0.5)'"
                 @mouseleave="($event.currentTarget as HTMLElement).style.borderColor = 'rgba(0, 212, 255, 0.2)'">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <h4 style="margin: 0 0 5px 0;">{{ account.name }}</h4>
                  <p style="margin: 0; font-size: 14px; color: #a0aec0;">
                    {{ accountsStore.getAccountTypeText(account.account_type) }} - {{ account.currency }}
                  </p>
                </div>
                <div style="text-align: right; display: flex; align-items: center; gap: 15px;">
                  <p style="margin: 0; font-size: 24px; font-weight: bold;"
                     :style="{ color: account.balance >= 0 ? '#51cf66' : '#ff6b6b' }">
                    {{ account.currency }} ${{ account.balance.toFixed(2) }}
                  </p>
                  <button @click="openQuickTransaction(account)" class="btn"
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
            <div v-for="(total, currency) in dashboard.totalByCurrency.value" :key="currency"
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

      <!-- 收入與支出趨勢頁籤 -->
      <div v-else-if="activeTab === 'trends'" class="tab-content">
        <MonthlyChart ref="monthlyChartRef" @day-click="handleDayClick" />
      </div>
    </div>

    <div class="card">
      <h2>預算狀態</h2>
      <div v-if="budgetsStore.budgets.length > 0" style="display: grid; gap: 15px;">
        <div v-for="budget in budgetsStore.budgets" :key="budget.id"
             style="border: 1px solid rgba(0, 212, 255, 0.2); padding: 15px; border-radius: 8px; background: rgba(0, 212, 255, 0.03);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h3 style="margin: 0;">{{ budget.name }}</h3>
            <div style="display: flex; gap: 8px; align-items: center;">
              <span v-if="budget.range_mode === 'recurring'"
                    style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; white-space: nowrap;">
                🔄 {{ budgetsStore.getPeriodText(budget.period || '') }}
              </span>
              <span v-else
                    style="background: rgba(0, 212, 255, 0.2);
                           color: #00d4ff; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid #00d4ff; white-space: nowrap;">
                📅 自訂區間
              </span>
              <span :style="{
                padding: '4px 12px',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: dashboard.getBudgetStatusColor(budget),
                color: 'white',
                whiteSpace: 'nowrap'
              }">
                {{ dashboard.getBudgetStatus(budget) }}
              </span>
            </div>
          </div>
          <p style="margin: 5px 0;"><strong>類別：</strong>{{ budget.category_names.join(', ') || '所有類別' }}</p>
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

          <div v-if="budget.daily_limit" style="margin-top: 15px; border-top: 1px dashed rgba(0, 212, 255, 0.2); padding-top: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
              <p style="margin: 0; font-size: 14px;"><strong>今日預算：</strong>${{ budget.daily_limit.toFixed(2) }}</p>
              <div style="text-align: right;">
                <p style="margin: 0; font-size: 14px;">
                  已用: <span :style="{ color: dashboard.getDailySpent(budget) > budget.daily_limit ? '#ff6b6b' : '#51cf66' }">
                    ${{ dashboard.getDailySpent(budget).toFixed(2) }}
                  </span>
                </p>
                <p style="margin: 0; font-size: 14px;">
                  剩餘: <span :style="{ color: (budget.daily_limit - dashboard.getDailySpent(budget)) < 0 ? '#ff6b6b' : '#51cf66' }">
                    ${{ (budget.daily_limit - dashboard.getDailySpent(budget)).toFixed(2) }}
                  </span>
                </p>
              </div>
            </div>
            <div style="background-color: rgba(0, 0, 0, 0.3); height: 10px; border-radius: 5px; overflow: hidden;">
              <div
                :style="{
                  width: Math.min((dashboard.getDailySpent(budget) / budget.daily_limit) * 100, 100) + '%',
                  backgroundColor: dashboard.getDailySpent(budget) > budget.daily_limit ? '#ff6b6b' : '#51cf66',
                  height: '100%',
                  transition: 'width 0.3s ease'
                }"
              ></div>
            </div>
          </div>

          <p style="margin-top: 10px; font-size: 14px; color: #a0aec0;">
            <small>{{ dateTimeUtils.formatDateTime(budget.start_date) }} - {{ dateTimeUtils.formatDateTime(budget.end_date) }}</small>
          </p>
        </div>
      </div>
      <p v-else>尚無預算</p>
    </div>

    <div class="card">
      <h2>最近交易</h2>
      <div style="display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap;">
        <input type="text" v-model="searchQuery" placeholder="搜尋描述..."
               style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; flex: 1; min-width: 150px;" />
        <input type="text" v-model="searchCategory" placeholder="搜尋類別..."
               style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; flex: 1; min-width: 150px;" />
        <select v-model="searchType" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; min-width: 100px;">
          <option value="">所有類型</option>
          <option value="credit">收入</option>
          <option value="debit">支出</option>
        </select>
        <div style="display: flex; gap: 5px; align-items: center; flex-wrap: wrap;">
          <input type="date" v-model="searchStartDate"
                 style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; min-width: 130px;" />
          <span>~</span>
          <input type="date" v-model="searchEndDate"
                 style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; min-width: 130px;" />
        </div>
        <button @click="clearSearch" class="btn btn-secondary" style="padding: 8px 15px;">清除</button>
      </div>
      <div style="overflow-x: auto;" v-if="filteredTransactions.length > 0">
        <table class="table">
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
              <td>{{ dateTimeUtils.formatDateTime(transaction.transaction_date) }}</td>
              <td>{{ transaction.description }}</td>
              <td>{{ transaction.transaction_type === 'credit' ? '收入' : '支出' }}</td>
              <td>{{ transaction.category || '無' }}</td>
              <td :style="{ color: transaction.transaction_type === 'credit' ? '#51cf66' : '#ff6b6b' }">
                ${{ transaction.amount.toFixed(2) }}
              </td>
              <td>
                <button @click="handleRecordAgain(transaction)" class="btn btn-primary" style="padding: 5px 10px; white-space: nowrap;">
                  再記一筆
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else>尚無交易記錄</p>
    </div>

    <!-- 快速記帳彈窗 -->
    <div v-if="quickModal.isOpen.value" class="modal">
      <div class="modal-content">
        <h2 style="color: #00d4ff;">快速記帳</h2>
        <form @submit.prevent="handleQuickTransaction">
          <div class="form-group">
            <label>帳戶</label>
            <select v-model="quickForm.form.value.account_id" required>
              <option v-for="account in accountsStore.accounts" :key="account.id" :value="account.id">
                {{ account.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="quickForm.form.value.description" placeholder="交易描述" required />
          </div>

          <div class="form-group">
            <label>金額</label>
            <div style="position: relative;">
              <input
                type="text"
                v-model.number="quickForm.form.value.amount"
                @click="showQuickCalculator = true"
                readonly
                required
                style="padding-right: 40px; cursor: pointer;"
                placeholder="點擊使用計算機輸入"
              />
              <button
                type="button"
                @click="showQuickCalculator = true"
                style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: rgba(0, 212, 255, 0.2); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 4px; padding: 4px 8px; cursor: pointer; color: #00d4ff; font-size: 18px;"
                title="打開計算機"
              >
                🧮
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>交易類型</label>
            <select v-model="quickForm.form.value.transaction_type" required>
              <option value="credit">收入</option>
              <option value="debit">支出</option>
            </select>
          </div>

          <CategorySelector
            :model-value="quickForm.form.value.category || ''"
            @update:model-value="quickForm.form.value.category = $event"
            :categories="categoriesStore.categories"
            @open-management="showCategoryModal = true"
          />

          <div class="form-group">
            <label>日期時間</label>
            <DateTimeInput v-model="quickForm.form.value.transaction_date" :required="true" />
          </div>

          <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button type="submit" class="btn btn-primary" style="flex: 1;">新增交易</button>
            <button type="button" @click="closeQuickTransaction" class="btn btn-secondary" style="flex: 1;">取消</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 消息提示彈窗 -->
    <MessageModal
      v-model="messageModal.isOpen.value"
      :type="messageModal.type.value"
      :message="messageModal.message.value"
    />

    <!-- 類別管理彈窗 -->
    <CategoryManagementModal
      v-model="showCategoryModal"
      :categories="categoriesStore.categories"
      @categories-changed="categoriesStore.fetchCategories()"
      @show-message="messageModal.show"
    />

    <!-- 計算機 -->
    <Calculator
      v-model="showQuickCalculator"
      :initial-value="quickForm.form.value.amount"
      @confirm="handleQuickCalculatorConfirm"
    />

    <!-- 當日交易明細彈窗 -->
    <DailyTransactionsModal
      v-model="showDailyModal"
      :date="selectedDate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Account, TransactionCreate } from '@/types'
import CategorySelector from '@/components/CategorySelector.vue'
import CategoryManagementModal from '@/components/CategoryManagementModal.vue'
import MessageModal from '@/components/MessageModal.vue'
import Calculator from '@/components/Calculator.vue'
import DateTimeInput from '@/components/DateTimeInput.vue'
import MonthlyChart from '@/components/MonthlyChart.vue'
import DailyTransactionsModal from '@/components/DailyTransactionsModal.vue'
import { useAccountsStore } from '@/stores/accounts'
import { useTransactionsStore } from '@/stores/transactions'
import { useBudgetsStore } from '@/stores/budgets'
import { useCategoriesStore } from '@/stores/categories'
import { useModal } from '@/composables/useModal'
import { useMessage } from '@/composables/useMessage'
import { useForm } from '@/composables/useForm'
import { useDateTime } from '@/composables/useDateTime'
import { useDashboard } from '@/composables/useDashboard'

const accountsStore = useAccountsStore()
const transactionsStore = useTransactionsStore()
const budgetsStore = useBudgetsStore()
const categoriesStore = useCategoriesStore()
const quickModal = useModal()
const messageModal = useMessage()
const dateTimeUtils = useDateTime()
const dashboard = useDashboard()

const activeTab = ref('accounts')
const searchQuery = ref('')
const searchCategory = ref('')
const searchType = ref('')
const { start: defaultStart, end: defaultEnd } = dateTimeUtils.getCurrentMonthRange()
const searchStartDate = ref(defaultStart)
const searchEndDate = ref(defaultEnd)
const showCategoryModal = ref(false)
const showQuickCalculator = ref(false)
const selectedAccount = ref<Account | null>(null)
const showDailyModal = ref(false)
const selectedDate = ref('')
const monthlyChartRef = ref<InstanceType<typeof MonthlyChart> | null>(null)

const initialQuickFormData: TransactionCreate = {
  account_id: 0,
  transaction_type: 'debit',
  amount: 0,
  category: '',
  description: '',
  transaction_date: dateTimeUtils.getCurrentDateTime()
}

const quickForm = useForm<TransactionCreate>(initialQuickFormData)

const filteredTransactions = computed(() => {
  let filtered = transactionsStore.transactions

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

  if (searchStartDate.value) {
    filtered = filtered.filter(transaction =>
      transaction.transaction_date >= `${searchStartDate.value}T00:00:00`
    )
  }

  if (searchEndDate.value) {
    filtered = filtered.filter(transaction =>
      transaction.transaction_date <= `${searchEndDate.value}T23:59:59`
    )
  }

  if (searchType.value) {
    filtered = filtered.filter(transaction =>
      transaction.transaction_type === searchType.value
    )
  }

  return filtered.slice(0, 20)
})

const clearSearch = () => {
  searchQuery.value = ''
  searchCategory.value = ''
  searchType.value = ''
  const { start, end } = dateTimeUtils.getCurrentMonthRange()
  searchStartDate.value = start
  searchEndDate.value = end
}

const openQuickTransaction = (account: Account) => {
  quickForm.resetForm()
  quickForm.form.value.account_id = account.id
  quickForm.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
  if (categoriesStore.categories.length > 0) {
    quickForm.form.value.category = categoriesStore.categories[0].name
  }
  quickModal.open()
}

const handleQuickTransaction = async () => {
  try {
    const transactionData = {
      ...quickForm.form.value,
      transaction_date: dateTimeUtils.formatDateTimeForBackend(quickForm.form.value.transaction_date)
    }

    await transactionsStore.createTransaction(transactionData)

    // 重新載入所有資料
    await Promise.all([
      accountsStore.fetchAccounts(),
      budgetsStore.fetchBudgets()
    ])

    // 刷新折線圖
    if (monthlyChartRef.value) {
      await monthlyChartRef.value.refresh()
    }

    messageModal.showSuccess('交易已成功新增！')
    closeQuickTransaction()
  } catch (error: any) {
    messageModal.showError(error.response?.data?.detail || '新增交易失敗，請稍後再試')
  }
}

const closeQuickTransaction = () => {
  quickModal.close()
  quickForm.resetForm()
  quickForm.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
}

const handleQuickCalculatorConfirm = (value: number) => {
  quickForm.form.value.amount = value
}

const handleDayClick = (date: string) => {
  selectedDate.value = date
  showDailyModal.value = true
}

const handleRecordAgain = (transaction: any) => {
  quickForm.resetForm()
  quickForm.form.value.account_id = transaction.account_id
  quickForm.form.value.description = transaction.description
  quickForm.form.value.amount = transaction.amount
  quickForm.form.value.transaction_type = transaction.transaction_type
  quickForm.form.value.category = transaction.category || ''
  quickForm.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
  quickModal.open()
}

onMounted(async () => {
  await Promise.all([
    accountsStore.fetchAccounts(),
    transactionsStore.fetchTransactions(),
    budgetsStore.fetchBudgets(),
    categoriesStore.fetchCategories()
  ])
})
</script>

<style scoped>
.tabs-container {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 10px 20px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 15px;
}

.tab-btn:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.4);
  color: #fff;
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 102, 255, 0.3) 0%, rgba(0, 212, 255, 0.3) 100%);
  border-color: #00d4ff;
  color: #00d4ff;
  font-weight: 500;
}

.tab-content {
  margin-top: 20px;
}
</style>
