<template>
  <div class="container">
    <h1>預算</h1>

    <div class="card">
      <button @click="handleCreate" class="btn btn-primary">新增預算</button>

      <div style="margin-top: 20px;">
        <!-- Active Budgets Section -->
        <div class="section-header" @click="showActive = !showActive" style="display: flex; align-items: center; cursor: pointer; margin-bottom: 15px; user-select: none;">
          <span style="font-size: 1.2rem; margin-right: 10px; transition: transform 0.3s;" :style="{ transform: showActive ? 'rotate(90deg)' : 'rotate(0deg)' }">▶</span>
          <h2 style="margin: 0;">進行中預算 ({{ activeBudgets.length }})</h2>
        </div>
        
        <div v-show="showActive">
          <div v-if="activeBudgets.length > 0">
            <div v-for="budget in activeBudgets" :key="budget.id" class="card" style="margin-bottom: 15px;">
              <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                <h3 style="margin: 0;">{{ budget.name }}</h3>
                <span v-if="budget.range_mode === 'recurring'"
                      style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                             color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                  🔄 {{ budgetsStore.getPeriodText(budget.period || '') }}
                </span>
                <span v-else
                      style="background: rgba(0, 212, 255, 0.2);
                             color: #00d4ff; padding: 4px 12px; border-radius: 12px; font-size: 12px; border: 1px solid #00d4ff;">
                  📅 自訂區間
                </span>
              </div>

              <p><strong>類別：</strong>{{ budget.category_names.length > 0 ? budget.category_names.join('、') : '全部類別' }}</p>
              <p><strong>綁定帳戶：</strong>{{ budgetsStore.getAccountNames(budget.account_ids) }}</p>
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

              <p><small>{{ dateTimeUtils.formatDateTime(budget.start_date) }} - {{ dateTimeUtils.formatDateTime(budget.end_date) }}</small></p>

              <p v-if="budget.range_mode === 'recurring' && budget.is_latest_period"
                 style="margin: 10px 0 0 0; padding: 8px; background: rgba(102, 126, 234, 0.1); border-left: 3px solid #667eea; font-size: 12px;">
                ℹ️ 本週期結束後將自動建立下一個週期
              </p>

              <div style="display: flex; gap: 5px; flex-wrap: wrap; margin-top: 10px;">
                <button @click="handleEdit(budget)" class="btn btn-primary" style="padding: 5px 10px;">
                  編輯
                </button>
                <button @click="handleDelete(budget.id)" class="btn btn-danger" style="padding: 5px 10px;">
                  {{ budget.range_mode === 'recurring' && budget.is_latest_period ? '取消週期' : '刪除' }}
                </button>
              </div>
            </div>
          </div>
          <p v-else style="margin-left: 20px; color: #a0aec0;">尚無進行中預算</p>
        </div>

        <!-- Expired Budgets Section -->
        <div class="section-header" @click="showExpired = !showExpired" style="display: flex; align-items: center; cursor: pointer; margin: 20px 0 15px 0; user-select: none;">
          <span style="font-size: 1.2rem; margin-right: 10px; transition: transform 0.3s;" :style="{ transform: showExpired ? 'rotate(90deg)' : 'rotate(0deg)' }">▶</span>
          <h2 style="margin: 0; color: #a0aec0;">已過期預算 ({{ expiredBudgets.length }})</h2>
        </div>
        
        <div v-show="showExpired">
          <div v-if="expiredBudgets.length > 0">
            <div v-for="budget in expiredBudgets" :key="budget.id" class="card" style="margin-bottom: 15px; opacity: 0.8;">
              <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #a0aec0;">{{ budget.name }}</h3>
                <span v-if="budget.range_mode === 'recurring'"
                      style="background: #4a5568; color: #cbd5e0; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                  🔄 {{ budgetsStore.getPeriodText(budget.period || '') }}
                </span>
                <span v-else
                      style="background: #4a5568; color: #cbd5e0; padding: 4px 12px; border-radius: 12px; font-size: 12px;">
                  📅 自訂區間
                </span>
              </div>

              <p><strong>類別：</strong>{{ budget.category_names.length > 0 ? budget.category_names.join('、') : '全部類別' }}</p>
              <p><strong>綁定帳戶：</strong>{{ budgetsStore.getAccountNames(budget.account_ids) }}</p>
              <p><strong>預算：</strong>${{ budget.amount.toFixed(2) }}</p>
              <p v-if="budget.daily_limit"><strong>每日預算：</strong>${{ budget.daily_limit.toFixed(2) }}</p>
              <p><strong>已使用：</strong>${{ budget.spent.toFixed(2) }}</p>
              <p><strong>剩餘：</strong>${{ (budget.amount - budget.spent).toFixed(2) }}</p>

              <div style="background-color: rgba(0, 0, 0, 0.3); height: 20px; border-radius: 10px; overflow: hidden; margin: 10px 0;">
                <div
                  :style="{
                    width: Math.min((budget.spent / budget.amount) * 100, 100) + '%',
                    backgroundColor: '#a0aec0',
                    height: '100%'
                  }"
                ></div>
              </div>

              <p><small>{{ dateTimeUtils.formatDateTime(budget.start_date) }} - {{ dateTimeUtils.formatDateTime(budget.end_date) }}</small></p>

              <div style="display: flex; gap: 5px; flex-wrap: wrap; margin-top: 10px;">
                <button @click="handleDelete(budget.id)" class="btn btn-danger" style="padding: 5px 10px;">
                  刪除
                </button>
              </div>
            </div>
          </div>
          <p v-else style="margin-left: 20px; color: #a0aec0;">尚無已過期預算</p>
        </div>
      </div>
    </div>

    <div v-if="modal.isOpen.value" class="modal">
      <div class="modal-content">
        <h2>{{ formController.isEditing() ? '編輯預算' : '新增預算' }}</h2>
        <div v-if="accountsStore.accounts.length === 0 && !formController.isEditing()" class="error" style="margin-bottom: 15px;">
          請先建立帳戶才能新增預算。
        </div>
        <form @submit.prevent="handleSubmit" v-if="accountsStore.accounts.length > 0 || formController.isEditing()">
          <div class="form-group">
            <label>預算名稱</label>
            <input v-model="formController.form.value.name" required />
          </div>

          <div class="form-group">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <label>綁定類別（非必選，可多選）</label>
              <button
                type="button"
                @click="showCategoryModal = true"
                class="btn btn-primary"
                style="padding: 4px 12px; font-size: 12px;"
              >
                管理類別
              </button>
            </div>
            <div style="background: rgba(26, 31, 58, 0.6); border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 6px; padding: 12px; max-height: 200px; overflow-y: auto;">
              <div v-if="categoriesStore.categories.length === 0" style="color: #a0aec0; text-align: center;">
                尚無類別
              </div>
              <div v-else style="display: flex; flex-direction: column; gap: 8px;">
                <label
                  v-for="category in categoriesStore.categories"
                  :key="category.id"
                  style="display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 8px; border-radius: 4px; transition: background 0.2s;"
                  :style="{ background: formController.form.value.category_names.includes(category.name) ? 'rgba(0, 212, 255, 0.1)' : 'transparent' }"
                >
                  <input
                    type="checkbox"
                    :value="category.name"
                    v-model="formController.form.value.category_names"
                    style="cursor: pointer; width: 16px; height: 16px; flex-shrink: 0;"
                  />
                  <span style="color: #e0e6ed; flex: 1;">{{ category.name }}</span>
                </label>
              </div>
            </div>
            <p style="margin: 8px 0 0 0; font-size: 12px; color: #a0aec0;">
              不選擇類別表示此預算適用於所有類別的消費
            </p>
          </div>

          <div class="form-group">
            <label>金額</label>
            <input type="number" step="0.01" v-model.number="formController.form.value.amount" required />
          </div>

          <div class="form-group">
            <label>每日預算 (選填)</label>
            <input type="number" step="0.01" v-model.number="formController.form.value.daily_limit" />
          </div>

          <!-- 範圍模式選擇 -->
          <div class="form-group">
            <label>週期設定</label>
            <div style="display: flex; gap: 10px; margin-top: 8px;">
              <button
                type="button"
                @click="selectRangeMode('custom')"
                :style="getRangeModeButtonStyle('custom')"
              >
                📅 自訂區間
              </button>
              <button
                type="button"
                @click="selectRangeMode('recurring')"
                :style="getRangeModeButtonStyle('recurring')"
              >
                🔄 週期
              </button>
            </div>
          </div>

          <!-- 週期模式: 選擇週期類型 -->
          <div v-if="formController.form.value.range_mode === 'recurring'" class="form-group">
            <label>週期類型</label>
            <select v-model="formController.form.value.period" required>
              <option value="monthly">每月</option>
              <option value="quarterly">每季</option>
              <option value="yearly">每年</option>
            </select>
            <p style="margin: 8px 0 0 0; font-size: 12px; color: #a0aec0;">
              系統將自動計算本週期的開始和結束時間，並在週期結束後自動建立下一個週期
            </p>
          </div>

          <!-- 自訂區間模式: 手動選擇日期 -->
          <div v-if="formController.form.value.range_mode === 'custom'" class="date-range-row">
            <div class="form-group date-input-group">
              <label>開始日期</label>
              <input type="date" v-model="budgetForm.startDateOnly.value" @change="() => budgetForm.updateStartDate(formController.form.value)" required />
            </div>
            <div class="form-group date-input-group">
              <label>結束日期</label>
              <input type="date" v-model="budgetForm.endDateOnly.value" @change="() => budgetForm.updateEndDate(formController.form.value)" required />
            </div>
          </div>

          <div class="form-group">
            <label>綁定帳戶（非必選，可多選）</label>
            <div style="background: rgba(26, 31, 58, 0.6); border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 6px; padding: 12px; max-height: 200px; overflow-y: auto;">
              <div v-if="accountsStore.accounts.length === 0" style="color: #a0aec0; text-align: center;">
                尚無帳戶
              </div>
              <div v-else style="display: flex; flex-direction: column; gap: 8px;">
                <label
                  v-for="account in accountsStore.accounts"
                  :key="account.id"
                  style="display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 8px; border-radius: 4px; transition: background 0.2s;"
                  :style="{ background: formController.form.value.account_ids.includes(account.id) ? 'rgba(0, 212, 255, 0.1)' : 'transparent' }"
                >
                  <input
                    type="checkbox"
                    :value="account.id"
                    v-model="formController.form.value.account_ids"
                    style="cursor: pointer; width: 16px; height: 16px; flex-shrink: 0;"
                  />
                  <span style="color: #e0e6ed; flex: 1;">{{ account.name }}</span>
                </label>
              </div>
            </div>
            <p style="margin: 8px 0 0 0; font-size: 12px; color: #a0aec0;">
              不選擇帳戶表示此預算適用於所有帳戶的消費
            </p>
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
      message="確定要刪除此預算嗎？刪除後將無法復原。"
      confirm-text="刪除"
      cancel-text="取消"
      confirm-type="danger"
      @confirm="confirmDialog.handleConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { Budget } from '@/types'
import CategoryManagementModal from '@/components/CategoryManagementModal.vue'
import MessageModal from '@/components/MessageModal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { useAccountsStore } from '@/stores/accounts'
import { useBudgetsStore } from '@/stores/budgets'
import { useCategoriesStore } from '@/stores/categories'
import { useModal } from '@/composables/useModal'
import { useConfirm } from '@/composables/useConfirm'
import { useMessage } from '@/composables/useMessage'
import { useForm } from '@/composables/useForm'
import { useDateTime } from '@/composables/useDateTime'
import { useBudgetForm } from '@/composables/useBudgetForm'

const accountsStore = useAccountsStore()
const budgetsStore = useBudgetsStore()
const categoriesStore = useCategoriesStore()
const modal = useModal()
const confirmDialog = useConfirm()
const messageModal = useMessage()
const dateTimeUtils = useDateTime()
const budgetForm = useBudgetForm()

const showCategoryModal = ref(false)
const showActive = ref(true)
const showExpired = ref(false)

const activeBudgets = computed(() => {
  const today = dateTimeUtils.getTodayString()
  return budgetsStore.budgets.filter(b => b.end_date >= today)
})

const expiredBudgets = computed(() => {
  const today = dateTimeUtils.getTodayString()
  return budgetsStore.budgets.filter(b => b.end_date < today)
})

const formController = useForm(budgetForm.initialFormData)

const getRangeModeButtonStyle = (mode: 'custom' | 'recurring') => {
  const isSelected = formController.form.value.range_mode === mode
  const baseColor = mode === 'custom' ? '#00d4ff' : '#667eea'

  return {
    flex: 1,
    padding: '12px 20px',
    border: isSelected ? `2px solid ${baseColor}` : `1px solid rgba(${mode === 'custom' ? '0, 212, 255' : '102, 126, 234'}, 0.3)`,
    borderRadius: '8px',
    background: isSelected ? `rgba(${mode === 'custom' ? '0, 212, 255' : '102, 126, 234'}, 0.2)` : 'rgba(0, 0, 0, 0.3)',
    color: isSelected ? baseColor : 'white',
    cursor: 'pointer',
    fontWeight: isSelected ? 'bold' : 'normal',
    transition: 'all 0.3s ease'
  }
}

const selectRangeMode = (mode: 'custom' | 'recurring') => {
  formController.form.value.range_mode = mode
  budgetForm.onRangeModeChange(formController.form.value)
}

const handleCreate = () => {
  if (accountsStore.accounts.length === 0) {
    modal.open()
  } else {
    modal.open()
  }
}

const handleEdit = (budget: Budget) => {
  if (budget.range_mode === 'custom') {
    const startDateTime = dateTimeUtils.formatDateTimeForInput(budget.start_date)
    const endDateTime = dateTimeUtils.formatDateTimeForInput(budget.end_date)

    budgetForm.startDateOnly.value = startDateTime.split('T')[0]
    budgetForm.endDateOnly.value = endDateTime.split('T')[0]
  }

  formController.setForm({
    name: budget.name,
    category_names: budget.category_names || [],
    amount: budget.amount,
    daily_limit: budget.daily_limit,
    range_mode: budget.range_mode,
    period: budget.period,
    start_date: budget.range_mode === 'custom' ? `${budgetForm.startDateOnly.value}T00:00` : undefined,
    end_date: budget.range_mode === 'custom' ? `${budgetForm.endDateOnly.value}T23:59` : undefined,
    account_ids: budget.account_ids || []
  }, budget.id)

  modal.open()
}

const handleDelete = (id: number) => {
  confirmDialog.confirm(id, async () => {
    try {
      await budgetsStore.deleteBudget(id)
    } catch (err) {
      console.error('刪除預算時發生錯誤:', err)
    }
  })
}

const handleSubmit = async () => {
  try {
    modal.clearError()
    const budgetData: any = {
      ...formController.form.value
    }

    // 只在自訂區間模式下格式化日期
    if (formController.form.value.range_mode === 'custom' && formController.form.value.start_date && formController.form.value.end_date) {
      budgetData.start_date = dateTimeUtils.formatDateTimeForBackend(formController.form.value.start_date)
      budgetData.end_date = dateTimeUtils.formatDateTimeForBackend(formController.form.value.end_date)
    }

    if (formController.isEditing()) {
      await budgetsStore.updateBudget(formController.editingId.value!, budgetData)
    } else {
      await budgetsStore.createBudget(budgetData)
    }

    handleClose()
  } catch (err: any) {
    modal.setError(err.response?.data?.detail || (formController.isEditing() ? '更新預算失敗' : '建立預算失敗'))
  }
}

const handleClose = () => {
  modal.close()
  budgetForm.resetDates()
  formController.resetForm()
  // 重置為預設值
  formController.form.value = { ...budgetForm.initialFormData }
}

onMounted(async () => {
  await Promise.all([
    budgetsStore.fetchBudgets(),
    accountsStore.fetchAccounts(),
    categoriesStore.fetchCategories()
  ])
})
</script>

<style scoped>
.date-range-row {
  display: flex;
  gap: 15px;
}

.date-input-group {
  flex: 1;
}

@media (max-width: 768px) {
  .date-range-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
