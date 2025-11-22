<template>
  <div class="container">
    <h1>儀表板</h1>

    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px;">
        <h2>總覽</h2>
        
        <!-- 總額統計 (移至右上角) -->

        <div style="display: flex; gap: 15px; flex-wrap: wrap; align-items: center;">
          <span style="font-size: 1.1rem; color: #a0aec0; font-weight: 500;">總額統計</span>
          <div v-for="(total, currency) in dashboard.totalByCurrency.value" :key="currency"
               style="padding: 8px 20px; background: linear-gradient(135deg, rgba(0, 102, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%); border-radius: 25px; border: 1px solid rgba(0, 212, 255, 0.2); display: flex; align-items: center; gap: 12px;">
            <span style="color: #a0aec0; font-size: 1rem;">{{ currency }}</span>
            <span style="font-size: 1.3rem; font-weight: bold;"
               :style="{ color: total >= 0 ? '#51cf66' : '#ff6b6b' }">
              ${{ total.toFixed(2) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 頁籤選單 -->
      <div class="tabs-container">
        <button
          :class="['tab-btn', activeTab === 'accounts' ? 'active' : '']"
          @click="activeTab = 'accounts'"
        >
          帳戶狀況
        </button>
        <button
          :class="['tab-btn', activeTab === 'trends' ? 'active' : '']"
          @click="activeTab = 'trends'"
        >
          收入與支出趨勢
        </button>
      </div>

      <!-- 帳戶狀況頁籤 -->
      <div v-if="activeTab === 'accounts'" class="tab-content">
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

      <!-- 收入與支出趨勢頁籤 -->
      <div v-else-if="activeTab === 'trends'" class="tab-content">
        <MonthlyChart ref="monthlyChartRef" @day-click="handleDayClick" />
      </div>
    </div>

    <div class="card">
      <h2>預算狀態</h2>
      <div v-if="budgetsStore.budgets.length > 0" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
        <div v-for="budget in budgetsStore.budgets" :key="budget.id"
             style="border: 1px solid rgba(0, 212, 255, 0.2); padding: 12px; border-radius: 8px; background: rgba(0, 212, 255, 0.03);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="margin: 0; font-size: 1.1rem;">{{ budget.name }}</h3>
            <div style="display: flex; gap: 6px; align-items: center;">
              <span v-if="budget.range_mode === 'recurring'"
                    style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; white-space: nowrap;">
                🔄 {{ budgetsStore.getPeriodText(budget.period || '') }}
              </span>
              <span v-else
                    style="background: rgba(0, 212, 255, 0.2);
                           color: #00d4ff; padding: 2px 8px; border-radius: 10px; font-size: 11px; border: 1px solid #00d4ff; white-space: nowrap;">
                📅 自訂
              </span>
              <span :style="{
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '12px',
                backgroundColor: dashboard.getBudgetStatusColor(budget),
                color: 'white',
                whiteSpace: 'nowrap'
              }">
                {{ dashboard.getBudgetStatus(budget) }}
              </span>
            </div>
          </div>
          
          <p style="margin: 0 0 8px 0; font-size: 13px; color: #a0aec0;">{{ budget.category_names.join(', ') || '所有類別' }}</p>
          
          <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
            <span>預算: ${{ budget.amount.toFixed(0) }}</span>
            <span>已用: ${{ budget.spent.toFixed(0) }}</span>
            <span :style="{ color: (budget.amount - budget.spent) < 0 ? '#ff6b6b' : '#51cf66' }">
              剩餘: ${{ (budget.amount - budget.spent).toFixed(0) }}
            </span>
          </div>
          
          <div style="background-color: rgba(0, 0, 0, 0.3); height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 10px;">
            <div
              :style="{
                width: Math.min((budget.spent / budget.amount) * 100, 100) + '%',
                backgroundColor: budget.spent > budget.amount ? '#ff6b6b' : budget.spent > budget.amount * 0.8 ? '#ffa726' : '#51cf66',
                height: '100%',
                transition: 'width 0.3s ease'
              }"
            ></div>
          </div>

          <div v-if="budget.daily_limit" style="border-top: 1px dashed rgba(0, 212, 255, 0.2); padding-top: 8px; margin-top: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; margin-bottom: 4px;">
              <span>今日: ${{ budget.daily_limit.toFixed(0) }}</span>
              <span>
                已用: <span :style="{ color: dashboard.getDailySpent(budget) > budget.daily_limit ? '#ff6b6b' : '#51cf66' }">${{ dashboard.getDailySpent(budget).toFixed(0) }}</span>
              </span>
              <span>
                剩: <span :style="{ color: (budget.daily_limit - dashboard.getDailySpent(budget)) < 0 ? '#ff6b6b' : '#51cf66' }">${{ (budget.daily_limit - dashboard.getDailySpent(budget)).toFixed(0) }}</span>
              </span>
            </div>
            <div style="background-color: rgba(0, 0, 0, 0.3); height: 6px; border-radius: 3px; overflow: hidden;">
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

          <p style="margin-top: 8px; font-size: 11px; color: #a0aec0; text-align: right;">
            {{ dateTimeUtils.formatDateTime(budget.start_date).split(' ')[0] }} - {{ dateTimeUtils.formatDateTime(budget.end_date).split(' ')[0] }}
          </p>
        </div>
      </div>
      <p v-else>尚無預算</p>
    </div>

    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h2 style="margin: 0;">交易日曆</h2>
        <button @click="showSearchModal = true" class="btn btn-primary" style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 1.2rem;">🔍</span>
          <span>搜尋交易</span>
        </button>
      </div>
      <TransactionCalendar
        :transactions="transactionsStore.transactions"
        :selected-date="selectedDate"
        @date-selected="handleCalendarDateSelected"
        @edit-transaction="handleEditTransaction"
      />
    </div>

    <!-- 快速記帳彈窗 -->
    <div v-if="quickModal.isOpen.value" class="modal">
      <div class="modal-content">
        <h2 style="color: #00d4ff;">{{ quickForm.isEditing() ? '編輯交易' : '快速記帳' }}</h2>
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
            <DescriptionHistory
              :descriptions="historicalDescriptions"
              @select="handleDescriptionSelect"
            />
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

          <div style="display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap;">
            <button type="submit" class="btn btn-primary" style="flex: 1;">{{ quickForm.isEditing() ? '更新' : '新增交易' }}</button>
            <button 
              v-if="quickForm.isEditing()" 
              type="button" 
              @click="handleRecordAgain({ 
                account_id: quickForm.form.value.account_id,
                description: quickForm.form.value.description,
                amount: quickForm.form.value.amount,
                transaction_type: quickForm.form.value.transaction_type,
                category: quickForm.form.value.category
              })" 
              class="btn" 
              style="flex: 1; background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white;"
            >
              再記一筆
            </button>
            <button 
              v-if="quickForm.isEditing()" 
              type="button" 
              @click="handleDeleteTransaction" 
              class="btn btn-danger" 
              style="flex: 1;"
            >
              刪除
            </button>
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
      @edit-transaction="handleEditTransaction"
    />

    <!-- 交易搜尋彈窗 -->
    <TransactionsSearchModal
      v-model="showSearchModal"
      :transactions="transactionsStore.transactions"
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
import DescriptionHistory from '@/components/DescriptionHistory.vue'
import TransactionCalendar from '@/components/TransactionCalendar.vue'
import TransactionsSearchModal from '@/components/TransactionsSearchModal.vue'
import { useAccountsStore } from '@/stores/accounts'
import { useTransactionsStore } from '@/stores/transactions'
import { useBudgetsStore } from '@/stores/budgets'
import { useCategoriesStore } from '@/stores/categories'
import { useModal } from '@/composables/useModal'
import { useMessage } from '@/composables/useMessage'
import { useForm } from '@/composables/useForm'
import { useDateTime } from '@/composables/useDateTime'
import { useDashboard } from '@/composables/useDashboard'
import api from '@/services/api'

const accountsStore = useAccountsStore()
const transactionsStore = useTransactionsStore()
const budgetsStore = useBudgetsStore()
const categoriesStore = useCategoriesStore()
const quickModal = useModal()
const messageModal = useMessage()
const dateTimeUtils = useDateTime()
const dashboard = useDashboard()

const activeTab = ref('accounts')
const showCategoryModal = ref(false)
const showQuickCalculator = ref(false)
const showSearchModal = ref(false)
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

// Historical descriptions from backend
const historicalDescriptions = ref<string[]>([])

const fetchDescriptionHistory = async () => {
  try {
    const response = await api.getDescriptionHistory()
    historicalDescriptions.value = response.data.descriptions
  } catch (error) {
    console.error('載入敘述歷史時發生錯誤:', error)
  }
}

const handleCalendarDateSelected = (date: string) => {
  selectedDate.value = date
  showDailyModal.value = true
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

const handleEditTransaction = (transaction: Transaction) => {
  quickForm.setForm({
    account_id: transaction.account_id,
    description: transaction.description,
    amount: transaction.amount,
    transaction_type: transaction.transaction_type,
    category: transaction.category || '',
    transaction_date: dateTimeUtils.formatDateTimeForInput(transaction.transaction_date)
  }, transaction.id)
  showDailyModal.value = false
  quickModal.open()
}

const handleDeleteTransaction = async () => {
  if (!quickForm.isEditing()) return
  
  if (!confirm('確定要刪除此交易嗎？刪除後將無法復原。')) return

  try {
    await transactionsStore.deleteTransaction(quickForm.editingId.value!)
    await Promise.all([
      accountsStore.fetchAccounts(),
      budgetsStore.fetchBudgets(),
      fetchDescriptionHistory()
    ])
    
    if (monthlyChartRef.value) {
      await monthlyChartRef.value.refresh()
    }
    
    messageModal.showSuccess('交易已刪除')
    closeQuickTransaction()
  } catch (error: any) {
    messageModal.showError(error.response?.data?.detail || '刪除交易失敗')
  }
}

const handleQuickTransaction = async () => {
  try {
    const transactionData = {
      ...quickForm.form.value,
      transaction_date: dateTimeUtils.formatDateTimeForBackend(quickForm.form.value.transaction_date)
    }

    if (quickForm.isEditing()) {
      await transactionsStore.updateTransaction(quickForm.editingId.value!, {
        description: transactionData.description,
        amount: transactionData.amount,
        category: transactionData.category,
        transaction_date: transactionData.transaction_date
      })
      // 更新交易時也更新敘述歷史
      await api.updateDescriptionHistory(transactionData.description)
      messageModal.showSuccess('交易已更新！')
    } else {
      await transactionsStore.createTransaction(transactionData)
      // 新增交易後更新敘述歷史
      await api.updateDescriptionHistory(transactionData.description)
      messageModal.showSuccess('交易已成功新增！')
    }

    // 重新載入所有資料
    await Promise.all([
      accountsStore.fetchAccounts(),
      budgetsStore.fetchBudgets(),
      fetchDescriptionHistory()
    ])

    // 刷新折線圖
    if (monthlyChartRef.value) {
      await monthlyChartRef.value.refresh()
    }

    closeQuickTransaction()
  } catch (error: any) {
    messageModal.showError(error.response?.data?.detail || (quickForm.isEditing() ? '更新交易失敗' : '新增交易失敗'))
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

const handleDescriptionSelect = (description: string) => {
  quickForm.form.value.description = description
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
    categoriesStore.fetchCategories(),
    fetchDescriptionHistory()
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
