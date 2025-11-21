<template>
  <div class="container">
    <h1>交易</h1>

    <div class="card">
      <div class="controls-header">
        <button @click="modal.open()" class="btn btn-primary btn-add">新增交易</button>
        <div class="filters-wrapper">
          <input type="text" v-model="searchQuery" placeholder="搜尋描述..." class="search-input" />
          <input type="text" v-model="searchCategory" placeholder="搜尋類別..." class="search-input" />
          <select v-model="searchType" class="search-select">
            <option value="">所有類型</option>
            <option value="credit">收入</option>
            <option value="debit">支出</option>
          </select>
          <div class="date-range-wrapper">
            <input type="date" v-model="searchStartDate" class="date-input" />
            <span class="date-separator">~</span>
            <input type="date" v-model="searchEndDate" class="date-input" />
          </div>
          <button @click="clearSearch" class="btn btn-secondary btn-clear">清除</button>
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
              <td>{{ dateTimeUtils.formatDateTime(transaction.transaction_date) }}</td>
              <td>{{ transaction.description }}</td>
              <td>{{ transaction.transaction_type === 'credit' ? '收入' : '支出' }}</td>
              <td>{{ transaction.category || '無' }}</td>
              <td :style="{ color: transaction.transaction_type === 'credit' ? '#51cf66' : '#ff6b6b' }">
                ${{ transaction.amount.toFixed(2) }}
              </td>
              <td>
                <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                  <button @click="handleRecordAgain(transaction)" class="btn" style="padding: 5px 10px; background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white;">
                    再記一筆
                  </button>
                  <button @click="handleEdit(transaction)" class="btn btn-primary" style="padding: 5px 10px;">
                    編輯
                  </button>
                  <button @click="handleDelete(transaction.id)" class="btn btn-danger" style="padding: 5px 10px;">
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

    <div v-if="modal.isOpen.value" class="modal">
      <div class="modal-content">
        <h2>{{ formController.isEditing() ? '編輯交易' : '新增交易' }}</h2>
        <div v-if="accountsStore.accounts.length === 0" class="error" style="margin-bottom: 15px;">
          請先建立帳戶才能新增交易。
        </div>
        <form @submit.prevent="handleSubmit" v-if="accountsStore.accounts.length > 0">
          <div class="form-group">
            <label>帳戶</label>
            <select v-model="formController.form.value.account_id" required>
              <option v-for="account in accountsStore.accounts" :key="account.id" :value="account.id">
                {{ account.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="formController.form.value.description" required />
          </div>
          <div class="form-group">
            <label>金額</label>
            <div style="position: relative;">
              <input
                type="text"
                v-model.number="formController.form.value.amount"
                @click="showCalculator = true"
                readonly
                required
                style="padding-right: 40px; cursor: pointer;"
                placeholder="點擊使用計算機輸入"
              />
              <button
                type="button"
                @click="showCalculator = true"
                style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: rgba(0, 212, 255, 0.2); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 4px; padding: 4px 8px; cursor: pointer; color: #00d4ff; font-size: 18px;"
                title="打開計算機"
              >
                🧮
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>交易類型</label>
            <select v-model="formController.form.value.transaction_type" required>
              <option value="credit">收入</option>
              <option value="debit">支出</option>
            </select>
          </div>
          <CategorySelector
            v-model="formController.form.value.category"
            :categories="categoriesStore.categories"
            @open-management="showCategoryModal = true"
          />
          <div class="form-group">
            <label>日期時間</label>
            <DateTimeInput v-model="formController.form.value.transaction_date" :required="true" />
          </div>
          <div v-if="modal.error.value" class="error">{{ modal.error.value }}</div>
          <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button type="submit" class="btn btn-primary">{{ formController.isEditing() ? '更新' : '建立' }}</button>
            <button type="button" @click="handleClose" class="btn btn-secondary">取消</button>
          </div>
        </form>
        <div v-else style="margin-top: 20px;">
          <button type="button" @click="handleClose" class="btn btn-secondary">關閉</button>
        </div>
      </div>
    </div>

    <!-- 類別管理彈窗 -->
    <CategoryManagementModal
      v-model="showCategoryModal"
      :categories="categoriesStore.categories"
      @categories-changed="categoriesStore.fetchCategories()"
      @show-message="messageModal.show"
    />

    <!-- 消息提示彈窗 -->
    <MessageModal
      v-model="messageModal.isOpen.value"
      :type="messageModal.type.value"
      :message="messageModal.message.value"
    />

    <!-- 刪除確認對話框 -->
    <ConfirmModal
      v-model="confirmDialog.isOpen.value"
      title="確認刪除"
      message="確定要刪除此交易嗎？刪除後將無法復原。"
      confirm-text="刪除"
      cancel-text="取消"
      confirm-type="danger"
      @confirm="confirmDialog.handleConfirm"
    />

    <!-- 計算機 -->
    <Calculator
      v-model="showCalculator"
      :initial-value="formController.form.value.amount"
      @confirm="handleCalculatorConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Transaction, TransactionCreate } from '@/types'
import CategorySelector from '@/components/CategorySelector.vue'
import CategoryManagementModal from '@/components/CategoryManagementModal.vue'
import MessageModal from '@/components/MessageModal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import Calculator from '@/components/Calculator.vue'
import DateTimeInput from '@/components/DateTimeInput.vue'
import { useAccountsStore } from '@/stores/accounts'
import { useTransactionsStore } from '@/stores/transactions'
import { useBudgetsStore } from '@/stores/budgets'
import { useCategoriesStore } from '@/stores/categories'
import { useModal } from '@/composables/useModal'
import { useConfirm } from '@/composables/useConfirm'
import { useMessage } from '@/composables/useMessage'
import { useForm } from '@/composables/useForm'
import { useDateTime } from '@/composables/useDateTime'

const accountsStore = useAccountsStore()
const transactionsStore = useTransactionsStore()
const budgetsStore = useBudgetsStore()
const categoriesStore = useCategoriesStore()
const modal = useModal()
const confirmDialog = useConfirm()
const messageModal = useMessage()
const dateTimeUtils = useDateTime()

const searchQuery = ref('')
const searchCategory = ref('')
const searchType = ref('')
const { start: defaultStart, end: defaultEnd } = dateTimeUtils.getCurrentMonthRange()
const searchStartDate = ref(defaultStart)
const searchEndDate = ref(defaultEnd)
const showCategoryModal = ref(false)
const showCalculator = ref(false)

const initialFormData: TransactionCreate = {
  account_id: 0,
  description: '',
  amount: 0,
  transaction_type: 'debit',
  category: '',
  transaction_date: dateTimeUtils.getCurrentDateTime()
}

const formController = useForm<TransactionCreate>(initialFormData)

const filteredTransactions = computed(() => {
  return transactionsStore.transactions.filter(transaction => {
    const matchesDescription = searchQuery.value === '' ||
      transaction.description.toLowerCase().includes(searchQuery.value.toLowerCase())

    const matchesCategory = searchCategory.value === '' ||
      (transaction.category && transaction.category.toLowerCase().includes(searchCategory.value.toLowerCase()))

    const matchesDate = (!searchStartDate.value || transaction.transaction_date >= `${searchStartDate.value}T00:00:00`) &&
      (!searchEndDate.value || transaction.transaction_date <= `${searchEndDate.value}T23:59:59`)

    const matchesType = searchType.value === '' ||
      transaction.transaction_type === searchType.value

    return matchesDescription && matchesCategory && matchesDate && matchesType
  })
})

const clearSearch = () => {
  searchQuery.value = ''
  searchCategory.value = ''
  searchType.value = ''
  const { start, end } = dateTimeUtils.getCurrentMonthRange()
  searchStartDate.value = start
  searchEndDate.value = end
}

const handleEdit = (transaction: Transaction) => {
  formController.setForm({
    account_id: transaction.account_id,
    description: transaction.description,
    amount: transaction.amount,
    transaction_type: transaction.transaction_type,
    category: transaction.category || '',
    transaction_date: dateTimeUtils.formatDateTimeForInput(transaction.transaction_date)
  }, transaction.id)
  modal.open()
}

const handleDelete = (id: number) => {
  confirmDialog.confirm(id, async () => {
    try {
      await transactionsStore.deleteTransaction(id)
      // 刪除交易後需要更新帳戶餘額和預算
      await Promise.all([
        accountsStore.fetchAccounts(),
        budgetsStore.fetchBudgets()
      ])
    } catch (err) {
      console.error('刪除交易時發生錯誤:', err)
    }
  })
}

const handleSubmit = async () => {
  try {
    modal.clearError()
    const transactionData = {
      ...formController.form.value,
      transaction_date: dateTimeUtils.formatDateTimeForBackend(formController.form.value.transaction_date)
    }

    if (formController.isEditing()) {
      await transactionsStore.updateTransaction(formController.editingId.value!, {
        description: transactionData.description,
        amount: transactionData.amount,
        category: transactionData.category,
        transaction_date: transactionData.transaction_date
      })
    } else {
      await transactionsStore.createTransaction(transactionData)
    }

    // 交易會影響帳戶餘額和預算，需要重新載入
    await Promise.all([
      accountsStore.fetchAccounts(),
      budgetsStore.fetchBudgets()
    ])
    handleClose()
  } catch (err: any) {
    modal.setError(err.response?.data?.detail || (formController.isEditing() ? '更新交易失敗' : '建立交易失敗'))
  }
}

const handleClose = () => {
  modal.close()
  formController.resetForm()
  formController.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
  // 確保有帳戶時自動選擇第一個
  if (accountsStore.accounts.length > 0) {
    formController.form.value.account_id = accountsStore.accounts[0].id
  }
  // 確保有類別時自動選擇第一個
  if (categoriesStore.categories.length > 0) {
    formController.form.value.category = categoriesStore.categories[0].name
  }
}

const handleCalculatorConfirm = (value: number) => {
  formController.form.value.amount = value
}

const handleRecordAgain = (transaction: Transaction) => {
  formController.resetForm()
  formController.form.value.account_id = transaction.account_id
  formController.form.value.description = transaction.description
  formController.form.value.amount = transaction.amount
  formController.form.value.transaction_type = transaction.transaction_type
  formController.form.value.category = transaction.category || ''
  formController.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
  modal.open()
}

onMounted(async () => {
  await Promise.all([
    transactionsStore.fetchTransactions(),
    accountsStore.fetchAccounts(),
    categoriesStore.fetchCategories()
  ])

  // 自動選擇第一個帳戶
  if (accountsStore.accounts.length > 0 && formController.form.value.account_id === 0) {
    formController.form.value.account_id = accountsStore.accounts[0].id
  }
  // 自動選擇第一個類別
  if (categoriesStore.categories.length > 0 && formController.form.value.category === '') {
    formController.form.value.category = categoriesStore.categories[0].name
  }
})
</script>

<style scoped>
.controls-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.filters-wrapper {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  flex: 1;
  justify-content: flex-end;
  align-items: center;
}

.search-input,
.search-select,
.date-input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.search-input {
  flex: 1;
  min-width: 150px;
}

.search-select {
  min-width: 100px;
}

.date-range-wrapper {
  display: flex;
  gap: 5px;
  align-items: center;
  flex-wrap: wrap;
}

.date-input {
  flex: 1;
  min-width: 130px;
}

.btn-clear {
  padding: 8px 15px;
}

/* Mobile Responsive Styles */
@media (max-width: 768px) {
  .controls-header {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-add {
    width: 100%;
    margin-bottom: 10px;
  }

  .filters-wrapper {
    flex-direction: column;
    align-items: stretch;
    width: 100%;
  }

  .search-input,
  .search-select,
  .date-range-wrapper,
  .btn-clear {
    width: 100%;
    min-width: 0; /* Override min-width to prevent overflow */
  }

  .date-range-wrapper {
    display: flex;
    flex-direction: row; /* Keep dates side-by-side if possible, or stack if very narrow */
    gap: 5px;
  }
  
  .date-input {
    min-width: 0;
    flex: 1;
  }
}
</style>
