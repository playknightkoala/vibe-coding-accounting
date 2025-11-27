<template>
  <div class="container">
    <!-- Page Loading Spinner -->
    <LoadingSpinner :show="isLoading" text="載入中..." />

    <h1>儀表板</h1>

    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
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
              <span v-if="(budget.daily_limit - dashboard.getDailySpent(budget)) < 0">
                <span style="color: #ff6b6b">已超支: ${{ (dashboard.getDailySpent(budget) - budget.daily_limit).toFixed(0) }}</span>
              </span>
              <span v-else>
                剩: <span style="color: #51cf66">${{ (budget.daily_limit - dashboard.getDailySpent(budget)).toFixed(0) }}</span>
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
        :budgets="budgetsStore.budgets"
        :selected-date="selectedDate"
        @date-selected="handleCalendarDateSelected"
        @edit-transaction="handleEditTransaction"
      />
    </div>

    <!-- 快速記帳彈窗 -->
    <div v-if="quickModal.isOpen.value" class="modal">
      <div class="modal-content quick-transaction-modal">
        <div class="modal-header">
          <h2 style="color: #00d4ff; margin: 0;">{{ quickForm.isEditing() ? '編輯交易' : '快速記帳' }}</h2>
        </div>
        
        <div class="modal-body">
          <form id="quick-transaction-form" @submit.prevent="handleQuickTransaction">
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
                :current-input="quickForm.form.value.description"
                @select="handleDescriptionSelect"
              />
            </div>
            <div class="form-group">
              <label>
                金額
                <span v-if="isCreditCardAccount" style="font-size: 0.8rem; color: #a0aec0; font-weight: normal; margin-left: 5px;">
                  (每小時同步臺銀匯率，實際金額以銀行為準)
                </span>
              </label>
              
              <!-- Currency Selector (Only for Credit Card) -->
              <div v-if="isCreditCardAccount" style="margin-bottom: 10px;">
                <select 
                  v-model="quickForm.selectedCurrency.value" 
                  @change="handleCurrencyChange"
                  style="width: 100%; text-overflow: ellipsis;"
                >
                  <option value="TWD">TWD (台幣)</option>
                  <template v-for="rate in exchangeRatesStore.rates" :key="rate.currency_code">
                    <option 
                      v-if="rate.buying_rate > 0 && rate.selling_rate > 0"
                      :value="rate.currency_code"
                    >
                      {{ rate.currency_code }} ({{ rate.currency_name }})
                    </option>
                  </template>
                </select>
              </div>

              <!-- Dual Inputs for Foreign Currency -->
              <div v-if="quickForm.selectedCurrency.value !== currentAccountCurrency" style="display: flex; gap: 10px; margin-bottom: 5px;">
                <!-- Account Currency ({{ currentAccountCurrency }}) -->
                <div style="flex: 1;">
                  <label style="font-size: 0.8rem; color: #a0aec0;">帳戶金額 ({{ currentAccountCurrency }})</label>
                  <div style="position: relative;">
                    <input
                      type="text"
                      :value="quickForm.form.value.amount"
                      @click="() => { quickForm.activeCalculatorInput.value = 'amount'; showQuickCalculator = true; }"
                      readonly
                      required
                      style="padding-right: 40px; cursor: pointer; width: 100%;"
                      :placeholder="currentAccountCurrency"
                    />
                    <button
                      type="button"
                      @click="() => { quickForm.activeCalculatorInput.value = 'amount'; showQuickCalculator = true; }"
                      style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: rgba(0, 212, 255, 0.2); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 4px; padding: 4px 8px; cursor: pointer; color: #00d4ff; font-size: 18px;"
                    >🧮</button>
                  </div>
                </div>

                <!-- Foreign Currency -->
                <div style="flex: 1;">
                  <label style="font-size: 0.8rem; color: #a0aec0;">外幣金額 ({{ quickForm.selectedCurrency.value }})</label>
                  <div style="position: relative;">
                    <input
                      type="number"
                      v-model.number="quickForm.foreignAmount.value"
                      @click="() => { quickForm.activeCalculatorInput.value = 'foreignAmount'; showQuickCalculator = true; }"
                      readonly
                      required
                      style="padding-right: 40px; cursor: pointer; width: 100%;"
                      placeholder="外幣"
                    />
                    <button
                      type="button"
                      @click="() => { quickForm.activeCalculatorInput.value = 'foreignAmount'; showQuickCalculator = true; }"
                      style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: rgba(0, 212, 255, 0.2); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 4px; padding: 4px 8px; cursor: pointer; color: #00d4ff; font-size: 18px;"
                    >🧮</button>
                  </div>
                </div>
              </div>

              <!-- Single Input for Same Currency or TWD -->
              <div v-else style="position: relative;">
                <input
                  type="text"
                  :value="quickForm.form.value.amount"
                  @click="() => { quickForm.activeCalculatorInput.value = 'amount'; showQuickCalculator = true; }"
                  readonly
                  required
                  style="padding-right: 40px; cursor: pointer; width: 100%;"
                  :placeholder="currentAccountCurrency"
                />
                <button
                  type="button"
                  @click="() => { quickForm.activeCalculatorInput.value = 'amount'; showQuickCalculator = true; }"
                  style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: rgba(0, 212, 255, 0.2); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 4px; padding: 4px 8px; cursor: pointer; color: #00d4ff; font-size: 18px;"
                  title="打開計算機"
                >
                  🧮
                </button>
              </div>

              <div v-if="quickForm.selectedCurrency.value !== currentAccountCurrency" style="margin-top: 5px; font-size: 0.9rem; color: #a0aec0;">
                <template v-if="currentAccountCurrency === 'TWD'">
                  匯率: 1 TWD ≈ {{ (1 / getExchangeRate(quickForm.selectedCurrency.value)).toFixed(4) }} {{ quickForm.selectedCurrency.value }}
                </template>
                <template v-else-if="quickForm.selectedCurrency.value === 'TWD'">
                  匯率: 1 {{ currentAccountCurrency }} ≈ {{ getBuyingRate(currentAccountCurrency) }} TWD
                </template>
                <template v-else>
                  匯率: 1 {{ currentAccountCurrency }} ≈ {{ (getBuyingRate(currentAccountCurrency) / getExchangeRate(quickForm.selectedCurrency.value)).toFixed(4) }} {{ quickForm.selectedCurrency.value }}
                </template>
              </div>
            </div>

            <div class="form-group">
              <label>交易類型</label>
              <select v-model="quickForm.form.value.transaction_type" required>
                <option value="credit">收入</option>
                <option value="debit">支出</option>
                <option value="installment">分期</option>
              </select>
            </div>

            <!-- 分期相關欄位 (只在新建時顯示) -->
            <div v-if="quickForm.form.value.transaction_type === 'installment' && !quickForm.isEditing()" style="background: rgba(0, 212, 255, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px;">
              <div class="form-group">
                <label>分期期數 (必填)</label>
                <input
                  type="number"
                  v-model.number="quickForm.installmentPeriods.value"
                  min="2"
                  max="60"
                  required
                  placeholder="輸入期數 (例如: 12)"
                />
              </div>

              <div class="form-group">
                <label>結帳日 (必填)</label>
                <select v-model.number="quickForm.billingDay.value" required>
                  <option v-for="day in 31" :key="day" :value="day">每月 {{ day }} 號</option>
                </select>
              </div>

              <!-- 試算結果 -->
              <div v-if="installmentCalculation" style="background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 5px; margin-top: 10px;">
                <p style="margin: 5px 0; font-size: 0.9rem;">
                  <strong>第一期:</strong> {{ installmentCalculation.firstAmount }} 元
                </p>
                <p v-if="installmentCalculation.otherAmount !== installmentCalculation.firstAmount" style="margin: 5px 0; font-size: 0.9rem;">
                  <strong>其餘各期:</strong> {{ installmentCalculation.otherAmount }} 元
                </p>
                <p v-else style="margin: 5px 0; font-size: 0.9rem;">
                  <strong>每期:</strong> {{ installmentCalculation.otherAmount }} 元
                </p>
              </div>

              <div class="form-group">
                <label style="display: flex; align-items: center; gap: 8px;">
                  <input type="checkbox" v-model="quickForm.excludeFromBudget.value" style="width: auto; margin: 0;" />
                  不計入預算
                </label>
              </div>
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
            
            <div class="form-group">
              <label>備註</label>
              <textarea 
                v-model="quickForm.form.value.note" 
                placeholder="備註 (選填)" 
                rows="3"
                style="width: 100%; resize: vertical; min-height: 80px;"
              ></textarea>
            </div>
          </form>
        </div>

        <div class="modal-footer">
          <div style="display: flex; gap: 10px; width: 100%;">
            <button type="submit" form="quick-transaction-form" class="btn btn-primary" style="flex: 1;">{{ quickForm.isEditing() ? '更新' : '新增交易' }}</button>
            <button 
              v-if="quickForm.isEditing()" 
              type="button" 
              @click="handleRecordAgain({ 
                account_id: quickForm.form.value.account_id,
                description: quickForm.form.value.description,
                note: quickForm.form.value.note,
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
        </div>
      </div>
    </div>

    <!-- 消息提示彈窗 -->
    <MessageModal
      v-model="messageModal.isOpen.value"
      :type="messageModal.type.value"
      :message="messageModal.message.value"
    />

    <!-- 刪除確認彈窗 -->
    <div v-if="showDeleteConfirm" class="modal">
      <div class="modal-content" style="max-width: 500px;">
        <h2 style="color: #ff6b6b; margin-bottom: 20px;">刪除交易</h2>
        <p style="margin-bottom: 20px;">{{ deleteConfirmMessage }}</p>

        <div v-if="deleteConfirmType === 'group'" style="margin-bottom: 20px;">
          <p style="color: #ffd43b; margin-bottom: 15px;">請選擇刪除方式：</p>
          <div style="display: flex; gap: 10px; flex-direction: column;">
            <button
              @click="confirmDelete('group')"
              class="btn"
              style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); color: white; width: 100%;"
            >
              刪除整組分期 (所有 {{ currentDeletingTransaction?.total_installments }} 期)
            </button>
            <button
              @click="confirmDelete('single')"
              class="btn"
              style="background: linear-gradient(135deg, #ffa94d 0%, #ff922b 100%); color: white; width: 100%;"
            >
              僅刪除此筆交易 (第 {{ currentDeletingTransaction?.installment_number }} 期)
            </button>
          </div>
        </div>
        <div v-else style="display: flex; gap: 10px;">
          <button
            @click="confirmDelete('single')"
            class="btn btn-danger"
            style="flex: 1;"
          >
            確定刪除
          </button>
          <button
            @click="showDeleteConfirm = false"
            class="btn btn-secondary"
            style="flex: 1;"
          >
            取消
          </button>
        </div>

        <button
          v-if="deleteConfirmType === 'group'"
          @click="showDeleteConfirm = false"
          class="btn btn-secondary"
          style="margin-top: 10px; width: 100%;"
        >
          取消
        </button>
      </div>
    </div>

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
      :initial-value="quickForm.activeCalculatorInput.value === 'amount' ? quickForm.form.value.amount : (quickForm.foreignAmount.value || 0)"
      @confirm="handleQuickCalculatorConfirm"
    />

    <!-- 當日交易明細彈窗 -->
    <DailyTransactionsModal
      v-model="showDailyModal"
      :date="modalDate"
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
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { useAccountsStore } from '@/stores/accounts'
import { useTransactionsStore } from '@/stores/transactions'
import { useBudgetsStore } from '@/stores/budgets'
import { useCategoriesStore } from '@/stores/categories'
import { useExchangeRatesStore } from '@/stores/exchangeRates'
import { useAuthStore } from '@/stores/auth'
import { useModal } from '@/composables/useModal'
import { useMessage } from '@/composables/useMessage'
import { useForm } from '@/composables/useForm'
import { useDateTime } from '@/composables/useDateTime'
import { useDashboard } from '@/composables/useDashboard'
import { useLoading } from '@/composables/useLoading'
import api from '@/services/api'

const accountsStore = useAccountsStore()
const transactionsStore = useTransactionsStore()
const budgetsStore = useBudgetsStore()
const categoriesStore = useCategoriesStore()
const exchangeRatesStore = useExchangeRatesStore()
const authStore = useAuthStore()
const quickModal = useModal()
const messageModal = useMessage()
const dateTimeUtils = useDateTime()
const dashboard = useDashboard()
const { isLoading, withLoading } = useLoading()

const activeTab = ref('accounts')
const showCategoryModal = ref(false)
const showQuickCalculator = ref(false)
const showSearchModal = ref(false)
const showDailyModal = ref(false)
const selectedDate = ref(dateTimeUtils.getTodayString())
const modalDate = ref(dateTimeUtils.getTodayString())
const monthlyChartRef = ref<InstanceType<typeof MonthlyChart> | null>(null)

// Delete confirmation modal state
const showDeleteConfirm = ref(false)
const deleteConfirmMessage = ref('')
const deleteConfirmType = ref<'single' | 'group' | 'installment-single'>('single')
const currentDeletingTransaction = ref<any>(null)

const initialQuickFormData: TransactionCreate = {
  account_id: 0,
  transaction_type: 'debit',
  amount: 0,
  category: '',
  description: '',
  note: '',
  transaction_date: dateTimeUtils.getCurrentDateTime()
}

// Quick Transaction Form
const quickForm = {
  isOpen: ref(false),
  isExpanded: ref(false),
  mode: ref<'create' | 'edit'>('create'),
  editId: ref<number | null>(null),
  form: ref<TransactionCreate>({
    account_id: 0,
    description: '',
    amount: 0,
    transaction_type: 'debit',
    category: '',
    transaction_date: new Date().toISOString(),
    note: ''
  }),
  foreignAmount: ref<number | null>(null),
  selectedCurrency: ref<string>('TWD'),
  installmentPeriods: ref<number>(12),
  billingDay: ref<number>(5),
  excludeFromBudget: ref<boolean>(false),

  reset: () => {
    quickForm.mode.value = 'create'
    quickForm.editId.value = null
    quickForm.form.value = {
      account_id: accountsStore.accounts.length > 0 ? accountsStore.accounts[0].id : 0,
      description: '',
      amount: 0,
      transaction_type: 'debit',
      category: '',
      transaction_date: new Date().toISOString(),
      note: ''
    }
    quickForm.foreignAmount.value = null
    quickForm.selectedCurrency.value = 'TWD'
    quickForm.installmentPeriods.value = 12
    quickForm.billingDay.value = 5
    quickForm.excludeFromBudget.value = false
    quickForm.activeCalculatorInput.value = 'amount'
    quickForm.isExpanded.value = false
  },
  
  isEditing: () => quickForm.mode.value === 'edit',
  resetForm: () => quickForm.reset(),
  setForm: (data: any, id: number) => {
    quickForm.mode.value = 'edit'
    quickForm.editId.value = id
    quickForm.form.value = { ...data }
    quickForm.foreignAmount.value = data.foreign_amount || null
    quickForm.selectedCurrency.value = data.foreign_currency || 'TWD'
    quickForm.isExpanded.value = true
  },
  editingId: computed(() => quickForm.editId.value),
  activeCalculatorInput: ref<'amount' | 'foreignAmount'>('amount')
}

const currentAccount = computed(() => {
  // Use == to handle potential string/number mismatch from select input
  return accountsStore.accounts.find(a => a.id == quickForm.form.value.account_id)
})

const currentAccountCurrency = computed(() => {
  return currentAccount.value?.currency || 'TWD'
})

const isCreditCardAccount = computed(() => {
  return currentAccount.value?.account_type === 'credit_card'
})

// Installment Calculation
const installmentCalculation = computed(() => {
  if (quickForm.form.value.transaction_type !== 'installment' || !quickForm.installmentPeriods.value || quickForm.form.value.amount <= 0) {
    return null
  }

  const totalAmount = quickForm.form.value.amount
  const periods = quickForm.installmentPeriods.value

  // Calculate base amount per period (integer division, no decimals)
  const baseAmount = Math.floor(totalAmount / periods)

  // Calculate remainder
  const remainder = totalAmount - (baseAmount * periods)

  // First installment gets the remainder
  const firstAmount = baseAmount + remainder

  return {
    firstAmount: firstAmount,
    otherAmount: baseAmount,
    totalPeriods: periods
  }
})

// Currency Conversion Logic
const getExchangeRate = (currencyCode: string) => {
  const rate = exchangeRatesStore.rates.find(r => r.currency_code === currencyCode)
  return rate?.selling_rate || rate?.buying_rate || 1
}

const getBuyingRate = (currencyCode: string) => {
  const rate = exchangeRatesStore.rates.find(r => r.currency_code === currencyCode)
  return rate?.buying_rate || 1
}

const handleCurrencyChange = () => {
  // Reset amount when currency changes to avoid confusion
  quickForm.form.value.amount = 0
  quickForm.foreignAmount.value = null
}

const handleForeignAmountChange = () => {
  const accountCurrency = currentAccountCurrency.value
  const targetCurrency = quickForm.selectedCurrency.value
  
  // If same currency or no foreign amount, reset
  if (targetCurrency === accountCurrency || !quickForm.foreignAmount.value) {
    if (targetCurrency !== accountCurrency) {
        quickForm.form.value.amount = 0
    }
    return
  }
  
  // Case 1: Account Currency == Target Currency (No conversion needed)
  if (accountCurrency === targetCurrency) {
    quickForm.form.value.amount = quickForm.foreignAmount.value
    return
  }

  // Case 2: Account is TWD, Target is Foreign (Use Selling Rate)
  if (accountCurrency === 'TWD') {
    const rate = getExchangeRate(targetCurrency)
    quickForm.form.value.amount = Math.round(quickForm.foreignAmount.value * rate)
    return
  }

  // Case 3: Account is Foreign, Target is TWD
  if (targetCurrency === 'TWD') {
    const rate = getBuyingRate(accountCurrency)
    quickForm.form.value.amount = Number((quickForm.foreignAmount.value * rate).toFixed(2))
    return
  }

  // Case 4: Account is Foreign, Target is Foreign (Different) -> Cross Rate via TWD
  const targetToTwdRate = getExchangeRate(targetCurrency)
  const twdAmount = quickForm.foreignAmount.value * targetToTwdRate
  
  const accountToTwdRate = getBuyingRate(accountCurrency)
  
  quickForm.form.value.amount = Number((twdAmount / accountToTwdRate).toFixed(2))
}

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
  // showDailyModal.value = true // User requested to disable this
}

const handleDayClick = (date: string) => {
  modalDate.value = date // Update modal date instead of calendar date
  showDailyModal.value = true
}

const openQuickTransaction = (account: Account) => {
  quickForm.resetForm()
  quickForm.form.value.account_id = account.id
  quickForm.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
  if (categoriesStore.categories.length > 0) {
    quickForm.form.value.category = categoriesStore.categories[0].name
  }
  // Set default currency to account currency
  quickForm.selectedCurrency.value = account.currency
  fetchDescriptionHistory()
  quickModal.open()
}

const handleEditTransaction = (transaction: Transaction) => {
  quickForm.setForm({
    account_id: transaction.account_id,
    description: transaction.description,
    note: transaction.note || '',
    amount: transaction.amount,
    transaction_type: transaction.transaction_type,
    category: transaction.category || '',
    transaction_date: dateTimeUtils.formatDateTimeForInput(transaction.transaction_date),
    foreign_amount: transaction.foreign_amount,
    foreign_currency: transaction.foreign_currency
  }, transaction.id)
  showDailyModal.value = false
  fetchDescriptionHistory()
  quickModal.open()
}

const handleDeleteTransaction = () => {
  if (!quickForm.isEditing()) return

  // Find the transaction being edited
  const transaction = transactionsStore.transactions.find(t => t.id === quickForm.editingId.value)
  currentDeletingTransaction.value = transaction

  // Check if it's an installment transaction
  if (transaction?.is_installment && transaction.installment_group_id) {
    deleteConfirmMessage.value = `此交易為分期交易 (第 ${transaction.installment_number} 期，共 ${transaction.total_installments} 期)`
    deleteConfirmType.value = 'group'
    showDeleteConfirm.value = true
  } else {
    deleteConfirmMessage.value = '確定要刪除此交易嗎？刪除後將無法復原。'
    deleteConfirmType.value = 'single'
    showDeleteConfirm.value = true
  }
}

const confirmDelete = async (deleteType: 'single' | 'group') => {
  showDeleteConfirm.value = false

  const transaction = currentDeletingTransaction.value
  if (!transaction) return

  try {
    if (deleteType === 'group' && transaction.installment_group_id) {
      // Delete entire installment group
      await api.deleteInstallmentGroup(transaction.installment_group_id)
      messageModal.showSuccess(`已刪除整組分期交易 (${transaction.total_installments} 期)`)
    } else {
      // Delete single transaction
      await transactionsStore.deleteTransaction(quickForm.editingId.value!)
      messageModal.showSuccess('交易已刪除')
    }

    await Promise.all([
      accountsStore.fetchAccounts(),
      budgetsStore.fetchBudgets(),
      fetchDescriptionHistory()
    ])

    if (monthlyChartRef.value) {
      await monthlyChartRef.value.refresh()
    }

    closeQuickTransaction()
  } catch (error: any) {
    messageModal.showError(error.response?.data?.detail || '刪除交易失敗')
  } finally {
    currentDeletingTransaction.value = null
  }
}

const handleQuickTransaction = async () => {
  try {
    const transactionData: any = {
      ...quickForm.form.value,
      transaction_date: dateTimeUtils.formatDateTimeForBackend(quickForm.form.value.transaction_date),
      foreign_amount: quickForm.selectedCurrency.value !== 'TWD' ? quickForm.foreignAmount.value : null,
      foreign_currency: quickForm.selectedCurrency.value !== 'TWD' ? quickForm.selectedCurrency.value : null
    }

    // Add installment fields if transaction type is installment
    if (quickForm.form.value.transaction_type === 'installment') {
      transactionData.is_installment = true
      transactionData.total_installments = quickForm.installmentPeriods.value
      transactionData.billing_day = quickForm.billingDay.value
      transactionData.exclude_from_budget = quickForm.excludeFromBudget.value
    }

    if (quickForm.isEditing()) {
      await transactionsStore.updateTransaction(quickForm.editingId.value!, {
        description: transactionData.description,
        note: transactionData.note,
        amount: transactionData.amount,
        category: transactionData.category,
        transaction_date: transactionData.transaction_date,
        foreign_amount: transactionData.foreign_amount,
        foreign_currency: transactionData.foreign_currency
      })
      // 更新交易時也更新敘述歷史
      // await api.updateDescriptionHistory(transactionData.description)
      messageModal.showSuccess('交易已更新！')
    } else {
      // Append currency info to note if foreign currency used
      // Append currency info to note if foreign currency used
      // Note is already updated in handleQuickCalculatorConfirm, but we ensure it's there?
      // Actually, handleQuickCalculatorConfirm handles the note update now.
      // We just need to ensure we don't double append if user edits the note manually.
      // Let's trust handleQuickCalculatorConfirm for the note part.


      await transactionsStore.createTransaction(transactionData)
      // 新增交易後更新敘述歷史
      // await api.updateDescriptionHistory(transactionData.description)
      messageModal.showSuccess(transactionData.is_installment ?
        `已成功建立 ${quickForm.installmentPeriods.value} 期分期交易！` :
        '交易已成功新增！')
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
  const accountCurrency = currentAccountCurrency.value
  const targetCurrency = quickForm.selectedCurrency.value
  
  const targetRate = getExchangeRate(targetCurrency)
  const accountRate = getBuyingRate(accountCurrency)

  if (quickForm.activeCalculatorInput.value === 'foreignAmount') {
    // User edited foreign amount -> calculate account amount
    quickForm.foreignAmount.value = value
    
    if (accountCurrency === targetCurrency) {
       // Same currency, no conversion
       quickForm.form.value.amount = value
    } else if (accountCurrency === 'TWD') {
       // Account is TWD, target is foreign
       quickForm.form.value.amount = Math.round(value * targetRate)
    } else if (targetCurrency === 'TWD') {
       // Account is foreign, target is TWD
       quickForm.form.value.amount = Number((value / accountRate).toFixed(2))
    } else {
       // Cross currency: Target -> TWD -> Account
       const twdAmount = value * targetRate
       quickForm.form.value.amount = Number((twdAmount / accountRate).toFixed(2))
    }
  } else {
    // User edited account amount -> calculate foreign amount
    quickForm.form.value.amount = value
    
    if (accountCurrency === targetCurrency) {
       // Same currency, no foreign amount needed
       quickForm.foreignAmount.value = value
    } else if (accountCurrency === 'TWD') {
       // Account is TWD, calculate foreign amount
       if (targetRate > 0) {
         quickForm.foreignAmount.value = Number((value / targetRate).toFixed(2))
       }
    } else if (targetCurrency === 'TWD') {
       // Account is foreign, target is TWD
       quickForm.foreignAmount.value = Number((value * accountRate).toFixed(2))
    } else {
       // Cross currency: Account -> TWD -> Target
       // Account Amount * Account Rate = TWD Amount
       // TWD Amount / Target Rate = Target Amount
       const twdAmount = value * accountRate
       if (targetRate > 0) {
         quickForm.foreignAmount.value = Number((twdAmount / targetRate).toFixed(2))
       }
    }
  }

  // Update note if foreign currency is used (i.e., different from account currency)
  if (targetCurrency !== accountCurrency && quickForm.foreignAmount.value) {
    const currencyNote = `[外幣: ${quickForm.foreignAmount.value} ${targetCurrency} ≈ ${quickForm.form.value.amount} ${accountCurrency}]`
    // Remove existing currency note if any (simple check)
    const noteWithoutCurrency = quickForm.form.value.note.replace(/\[外幣:.*?\]/, '').trim()
    quickForm.form.value.note = noteWithoutCurrency ? `${noteWithoutCurrency} ${currencyNote}` : currencyNote
  }
}

const handleDescriptionSelect = (description: string) => {
  quickForm.form.value.description = description
}

const handleRecordAgain = (transaction: any) => {
  quickForm.resetForm()
  quickForm.form.value.account_id = transaction.account_id
  quickForm.form.value.description = transaction.description
  quickForm.form.value.note = '' // 重記一筆時不保留備註
  quickForm.form.value.amount = transaction.amount
  quickForm.form.value.transaction_type = transaction.transaction_type
  quickForm.form.value.category = transaction.category || ''
  quickForm.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
  quickModal.open()
}

onMounted(async () => {
  await withLoading(async () => {
    try {
      await Promise.all([
        accountsStore.fetchAccounts(),
        transactionsStore.fetchTransactions(),
        budgetsStore.fetchBudgets(),
        categoriesStore.fetchCategories(),
        exchangeRatesStore.fetchRates(),
        fetchDescriptionHistory()
      ])

      // Set initial account if available
      if (accountsStore.accounts.length > 0) {
        quickForm.form.value.account_id = accountsStore.accounts[0].id
      }
    } catch (error) {
      console.error('Failed to initialize dashboard:', error)
    }
  })
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
  border: 1px solid transparent;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 15px;
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



.quick-transaction-modal {
  display: flex;
  flex-direction: column;
  max-height: 85vh; /* Limit height to viewport height */
  padding: 0; /* Reset padding for flex layout */
  overflow: hidden; /* Hide overflow on container */
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  flex-shrink: 0;
}

.modal-body {
  padding: 20px;
  overflow-y: auto; /* Scrollable content */
  flex: 1; /* Take remaining space */
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid rgba(0, 212, 255, 0.2);
  background: rgba(0, 0, 0, 0.2); /* Slight background for separation */
  flex-shrink: 0;
}

/* Ensure textarea matches other inputs */
textarea {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  color: white;
  padding: 8px 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

textarea:focus {
  outline: none;
  border-color: #00d4ff;
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
}
</style>
