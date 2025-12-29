<template>
  <div class="container">
    <!-- Page Loading Spinner -->
    <LoadingSpinner :show="isLoading" text="載入中..." />

    <h1>儀表板</h1>

    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
        <h2>總覽</h2>

        <!-- 總額統計與時間範圍切換 (移至右上角) -->
        <div style="display: flex; gap: 15px; flex-wrap: wrap; align-items: center;">
          <!-- 時間範圍切換按鈕 -->
          <div style="display: flex; gap: 8px; background: rgba(0, 0, 0, 0.2); padding: 4px; border-radius: 20px; border: 1px solid rgba(0, 212, 255, 0.2);">
            <button
              @click="dashboard.setTimeRangeMode('month')"
              :class="['time-range-btn', dashboard.timeRangeMode.value === 'month' ? 'active' : '']"
            >
              本月
            </button>
            <button
              @click="dashboard.setTimeRangeMode('day')"
              :class="['time-range-btn', dashboard.timeRangeMode.value === 'day' ? 'active' : '']"
            >
              今日
            </button>
            <button
              @click="dashboard.setTimeRangeMode('total')"
              :class="['time-range-btn', dashboard.timeRangeMode.value === 'total' ? 'active' : '']"
            >
              總體
            </button>
          </div>

          <span style="font-size: 1.1rem; color: #a0aec0; font-weight: 500;">
            <template v-if="dashboard.timeRangeMode.value === 'total'">帳戶總額</template>
            <template v-else-if="dashboard.timeRangeMode.value === 'month'">本月變化</template>
            <template v-else>今日變化</template>
          </span>

          <div v-for="(total, currency) in dashboard.totalByCurrencyForTimeRange.value" :key="currency"
               style="padding: 8px 20px; background: linear-gradient(135deg, rgba(0, 102, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%); border-radius: 25px; border: 1px solid rgba(0, 212, 255, 0.2); display: flex; align-items: center; gap: 12px;">
            <span style="color: #a0aec0; font-size: 1rem;">{{ currency }}</span>
            <span style="font-size: 1.3rem; font-weight: bold;"
               :style="{ color: total >= 0 ? '#51cf66' : '#ff6b6b' }">
              <template v-if="dashboard.timeRangeMode.value !== 'total'">
                {{ total >= 0 ? '+' : '' }}
              </template>
              ${{ total.toFixed(2) }}
            </span>
          </div>
        </div>
      </div>

      <!-- 收支統計 -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
        <div style="padding: 15px; background: linear-gradient(135deg, rgba(81, 207, 102, 0.1) 0%, rgba(81, 207, 102, 0.05) 100%); border-radius: 8px; border: 1px solid rgba(81, 207, 102, 0.2);">
          <div style="color: #a0aec0; font-size: 0.9rem; margin-bottom: 5px;">收入</div>
          <div style="color: #51cf66; font-size: 1.8rem; font-weight: bold;">
            ${{ dashboard.incomeExpenseStats.value.income.toFixed(2) }}
          </div>
        </div>
        <div style="padding: 15px; background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 107, 107, 0.05) 100%); border-radius: 8px; border: 1px solid rgba(255, 107, 107, 0.2);">
          <div style="color: #a0aec0; font-size: 0.9rem; margin-bottom: 5px;">支出</div>
          <div style="color: #ff6b6b; font-size: 1.8rem; font-weight: bold;">
            ${{ dashboard.incomeExpenseStats.value.expense.toFixed(2) }}
          </div>
        </div>
        <div style="padding: 15px; background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%); border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
          <div style="color: #a0aec0; font-size: 0.9rem; margin-bottom: 5px;">淨收支</div>
          <div :style="{ color: dashboard.incomeExpenseStats.value.net >= 0 ? '#51cf66' : '#ff6b6b', fontSize: '1.8rem', fontWeight: 'bold' }">
            ${{ dashboard.incomeExpenseStats.value.net.toFixed(2) }}
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
        <!-- 排序選擇器 -->
        <div v-if="accountsStore.accounts.length > 0" style="margin-bottom: 15px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
          <span style="color: #a0aec0; font-size: 0.9rem;">排序方式：</span>
          <div style="display: flex; gap: 8px; background: rgba(0, 0, 0, 0.2); padding: 4px; border-radius: 20px; border: 1px solid rgba(0, 212, 255, 0.2);">
            <button
              @click="accountSortMode = 'type'"
              :class="['sort-btn', accountSortMode === 'type' ? 'active' : '']"
            >
              帳戶類型
            </button>
            <button
              @click="accountSortMode = 'currency'"
              :class="['sort-btn', accountSortMode === 'currency' ? 'active' : '']"
            >
              幣別
            </button>
            <button
              @click="accountSortMode = 'balance'"
              :class="['sort-btn', accountSortMode === 'balance' ? 'active' : '']"
            >
              金額
            </button>
          </div>
        </div>

        <div v-if="accountsStore.accounts.length > 0" style="display: grid; gap: 15px;">
          <div v-for="account in sortedAccounts" :key="account.id" class="account-card">
            <div class="account-info">
              <h4>{{ account.name }}</h4>
              <p>{{ accountsStore.getAccountTypeText(account.account_type) }} - {{ account.currency }}</p>
            </div>

            <div class="account-balance">
              <div class="balance-display">
                <span class="currency-label">{{ account.currency }}</span>
                <span class="balance-amount" :style="{ color: dashboard.getAccountBalance(account.id) >= 0 ? '#51cf66' : '#ff6b6b' }">
                  ${{ dashboard.getAccountBalance(account.id).toFixed(2) }}
                </span>
              </div>
            </div>

            <div class="account-actions">
              <button @click="openQuickTransaction(account)" class="btn btn-action btn-accounting">
                記帳
              </button>
              <!-- Transfer Buttons -->
              <button v-if="account.account_type === 'stored_value'" 
                      @click="openTransferModal(account, 'topup')" 
                      class="btn btn-action btn-topup">
                儲值
              </button>
              <button v-if="account.account_type === 'cash'" 
                      @click="openTransferModal(account, 'withdraw')" 
                      class="btn btn-action btn-withdraw">
                提領
              </button>
              <button v-if="account.account_type === 'bank'" 
                      @click="openTransferModal(account, 'transfer')" 
                      class="btn btn-action btn-transfer">
                轉帳
              </button>
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
      <div v-if="activeBudgets.length > 0" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
        <div v-for="budget in activeBudgets" :key="budget.id"
             style="border: 1px solid rgba(0, 212, 255, 0.2); padding: 12px; border-radius: 8px; background: rgba(0, 212, 255, 0.03);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="margin: 0; font-size: 1.1rem;">{{ budget.name }}</h3>
            <div style="display: flex; gap: 6px; align-items: center;">
              <button 
                @click.stop="togglePrimary(budget)"
                :style="{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  color: budget.is_primary ? '#ffd700' : 'rgba(255, 255, 255, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  padding: '4px',
                  transition: 'all 0.3s'
                }"
                :title="budget.is_primary ? '取消主要預算' : '設為主要預算'"
              >
                <span class="material-icons" style="font-size: 20px;">{{ budget.is_primary ? 'star' : 'star_border' }}</span>
              </button>
              <span v-if="budget.range_mode === 'recurring'"
                    style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; white-space: nowrap; display: flex; align-items: center; gap: 4px;">
                <span class="material-icons" style="font-size: 14px;">autorenew</span>
                {{ budgetsStore.getPeriodText(budget.period || '') }}
              </span>
              <span v-else
                    style="background: rgba(0, 212, 255, 0.2);
                           color: #00d4ff; padding: 2px 8px; border-radius: 10px; font-size: 11px; border: 1px solid #00d4ff; white-space: nowrap; display: flex; align-items: center; gap: 4px;">
                <span class="material-icons" style="font-size: 14px;">event</span>
                自訂
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

          <!-- 週期統計 -->
          <div v-if="budget.over_budget_days > 0 || budget.within_budget_days > 0"
               style="border-top: 1px dashed rgba(0, 212, 255, 0.2); padding-top: 8px; margin-top: 8px;">
            <div style="font-size: 11px; color: #a0aec0; margin-bottom: 6px; display: flex; align-items: center; gap: 4px;">
              <span class="material-icons" style="font-size: 14px;">analytics</span>
              本週期執行狀況
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px; font-size: 12px;">
              <div style="display: flex; align-items: center; gap: 6px;">
                <span class="material-icons" style="font-size: 14px; color: #51cf66;">check_circle</span>
                <span style="color: white;">預算內：</span>
                <span style="color: #51cf66; font-weight: bold;">{{ budget.within_budget_days }} 天</span>
                <span style="color: #a0aec0;">({{ ((budget.within_budget_days / (budget.within_budget_days + budget.over_budget_days)) * 100).toFixed(0) }}%)</span>
              </div>
              <div style="display: flex; align-items: center; gap: 6px;">
                <span class="material-icons" style="font-size: 14px; color: #ff6b6b;">error</span>
                <span style="color: white;">超支：</span>
                <span style="color: #ff6b6b; font-weight: bold;">{{ budget.over_budget_days }} 天</span>
                <span style="color: #a0aec0;">({{ ((budget.over_budget_days / (budget.within_budget_days + budget.over_budget_days)) * 100).toFixed(0) }}%)</span>
              </div>
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
          <span class="material-icons" style="font-size: 1.2rem;">search</span>
          <span>搜尋交易</span>
        </button>
      </div>
      <TransactionCalendar
        :transactions="transactionsStore.transactions"
        :recurring-expenses="recurringExpenses"
        :budgets="budgetsStore.budgets"
        :selected-date="selectedDate"
        @date-selected="handleCalendarDateSelected"
        @edit-transaction="handleEditTransaction"
        @add-transaction="handleAddTransactionFromCalendar"
      />
    </div>

    <!-- 快速記帳彈窗 -->
    <div v-if="quickModal.isOpen.value" class="modal">
      <div class="modal-content quick-transaction-modal">
        <div class="modal-header">
          <h2 style="color: #00d4ff; margin: 0;">
            {{ quickForm.isEditing() ? '編輯交易' : 
               quickForm.transferMode.value === 'topup' ? '新增儲值' :
               quickForm.transferMode.value === 'withdraw' ? '新增提領' :
               quickForm.transferMode.value === 'transfer' ? '新增轉帳' :
               '快速記帳' 
            }}
          </h2>
        </div>
        
        <div class="modal-body">
          <form id="quick-transaction-form" @submit.prevent="handleQuickTransaction">
            <div class="form-group">
              <!-- Transfer Mode: From/To Selectors -->
              <div v-if="quickForm.isTransfer()" style="display: flex; gap: 10px; margin-bottom: 15px;">
                <div style="flex: 1;">
                  <label>轉出帳戶</label>
                  <select v-model="quickForm.form.value.account_id" required>
                    <option v-for="account in availableSourceAccounts" :key="account.id" :value="account.id">
                      {{ account.name }}
                    </option>
                  </select>
                </div>
                <div style="flex: 0 0 auto; display: flex; align-items: center; padding-top: 20px;">
                  <span class="material-icons" style="font-size: 1.5rem; color: #00d4ff;">arrow_forward</span>
                </div>
                <div style="flex: 1;">
                  <label>轉入帳戶</label>
                  <select v-model="quickForm.transferTargetId.value" disabled required>
                    <option v-for="account in accountsStore.accounts" :key="account.id" :value="account.id">
                      {{ account.name }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- Regular Mode: Single Account Selector -->
              <div v-else>
                <label>帳戶</label>
                <select v-model="quickForm.form.value.account_id" @change="handleAccountChange" required>
                  <option v-for="account in accountsStore.accounts" :key="account.id" :value="account.id">
                    {{ account.name }}
                  </option>
                </select>
              </div>
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
                  <template v-for="rate in uniqueExchangeRates" :key="rate.currency_code">
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
                      style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: rgba(0, 212, 255, 0.2); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 4px; padding: 4px 8px; cursor: pointer; color: #00d4ff;"
                    ><span class="material-icons" style="font-size: 18px;">calculate</span></button>
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
                      style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: rgba(0, 212, 255, 0.2); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 4px; padding: 4px 8px; cursor: pointer; color: #00d4ff;"
                    ><span class="material-icons" style="font-size: 18px;">calculate</span></button>
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
                  style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: rgba(0, 212, 255, 0.2); border: 1px solid rgba(0, 212, 255, 0.4); border-radius: 4px; padding: 4px 8px; cursor: pointer; color: #00d4ff;"
                  title="打開計算機"
                >
                  <span class="material-icons" style="font-size: 18px;">calculate</span>
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


            <!-- 交易類型 -->
            <div v-if="!quickForm.isTransfer() && !isEditingTransferTransaction" class="form-group">
              <label>交易類型</label>
              <select v-model="quickForm.form.value.transaction_type" required>
                <option value="credit">收入</option>
                <option value="debit">支出</option>
                <option value="installment">分期</option>
              </select>
            </div>
            <!-- 轉帳交易：顯示唯讀類型 -->
            <div v-else-if="isEditingTransferTransaction" class="form-group">
              <label>交易類型</label>
              <div style="padding: 10px 12px; background: rgba(0, 0, 0, 0.2); border-radius: 4px; border: 1px solid rgba(0, 212, 255, 0.3); color: #a0aec0;">
                {{ quickForm.form.value.transaction_type === 'transfer_in' ? '轉入' : '轉出' }}
              </div>
            </div>

            <!-- 固定支出選項 (只在交易類型為支出時顯示，且不在編輯模式，且不是轉帳/提領/儲值) -->
            <div v-if="quickForm.form.value.transaction_type === 'debit' && !quickForm.isEditing() && !quickForm.isTransfer()" class="form-group">
              <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                <input
                  type="checkbox"
                  v-model="quickForm.isRecurring.value"
                  style="width: auto; margin: 0; cursor: pointer;"
                />
                設為固定支出
              </label>
            </div>

            <!-- 固定支出欄位 (只在勾選固定支出時顯示) -->
            <div v-if="quickForm.isRecurring.value && quickForm.form.value.transaction_type === 'debit' && !quickForm.isEditing() && !quickForm.isTransfer()"
                 style="background: rgba(147, 51, 234, 0.1); padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid rgba(147, 51, 234, 0.3);">
              <div class="form-group">
                <label>每月執行日期 (必填)</label>
                <select v-model.number="quickForm.recurringDayOfMonth.value" required>
                  <option v-for="day in 31" :key="day" :value="day">每月 {{ day }} 號</option>
                </select>
                <small style="color: #a0aec0; display: block; margin-top: 5px;">
                  系統將在每月此日期自動建立交易記錄
                </small>
              </div>
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

              <div class="form-group">
                <label>年利率 (%)</label>
                <input
                  type="number"
                  v-model.number="quickForm.annualInterestRate.value"
                  min="0"
                  max="100"
                  step="0.01"
                  placeholder="輸入年利率 (例如: 2.68)"
                />
                <small style="color: #a0aec0; display: block; margin-top: 5px;">
                  填入 1% 以上將使用貸款公式計算，0 或留空為零利率分期
                </small>
              </div>

              <!-- 試算結果 -->
              <div v-if="installmentCalculation" style="background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 5px; margin-top: 10px;">
                <p v-if="installmentCalculation.hasInterest" style="margin: 5px 0; font-size: 0.9rem; color: #ffd43b;">
                  <strong>含利息分期</strong>
                </p>
                <p v-if="installmentCalculation.hasInterest && installmentCalculation.lastAmount !== installmentCalculation.otherAmount" style="margin: 5px 0; font-size: 0.9rem;">
                  <strong>第 1 ~ {{ installmentCalculation.totalPeriods - 1 }} 期 ≈</strong> {{ installmentCalculation.otherAmount }} 元
                </p>
                <p v-if="installmentCalculation.hasInterest && installmentCalculation.lastAmount !== installmentCalculation.otherAmount" style="margin: 5px 0; font-size: 0.9rem;">
                  <strong>第 {{ installmentCalculation.totalPeriods }} 期 ≈</strong> {{ installmentCalculation.lastAmount }} 元
                </p>
                <p v-if="installmentCalculation.hasInterest" style="margin: 5px 0; font-size: 0.9rem; color: #51cf66;">
                  <strong>本金：</strong>{{ installmentCalculation.principal }} 元
                </p>
                <p v-if="installmentCalculation.hasInterest" style="margin: 5px 0; font-size: 0.9rem; color: #ff6b6b;">
                  <strong>利息：</strong>{{ installmentCalculation.totalInterest }} 元
                </p>
                <p v-if="installmentCalculation.hasInterest" style="margin: 5px 0; font-size: 0.9rem; color: #ffd43b;">
                  <strong>利息+本金 ≈</strong> {{ installmentCalculation.totalWithInterest }} 元
                </p>
                <p v-if="!installmentCalculation.hasInterest && installmentCalculation.firstAmount !== installmentCalculation.otherAmount" style="margin: 5px 0; font-size: 0.9rem;">
                  <strong>第一期 ≈</strong> {{ installmentCalculation.firstAmount }} 元
                </p>
                <p v-if="!installmentCalculation.hasInterest && installmentCalculation.firstAmount !== installmentCalculation.otherAmount" style="margin: 5px 0; font-size: 0.9rem;">
                  <strong>其餘各期 ≈</strong> {{ installmentCalculation.otherAmount }} 元
                </p>
                <p v-if="installmentCalculation.firstAmount === installmentCalculation.otherAmount" style="margin: 5px 0; font-size: 0.9rem;">
                  <strong>每期 ≈</strong> {{ installmentCalculation.otherAmount }} 元
                </p>
              </div>

              <div class="form-group">
                <label style="display: flex; align-items: center; gap: 8px;">
                  <input type="checkbox" v-model="quickForm.excludeFromBudget.value" style="width: auto; margin: 0;" />
                  不計入預算
                </label>
              </div>
            </div>

            <!-- 類別選擇器：新建轉帳和編輯轉帳時都隱藏 -->
            <div v-if="!quickForm.isTransfer() && !isEditingTransferTransaction">
              <CategorySelector
                :model-value="quickForm.form.value.category || ''"
                @update:model-value="quickForm.form.value.category = $event"
                :categories="categoriesStore.categories"
                @open-management="showCategoryModal = true"
              />
            </div>
            <!-- 轉帳交易：顯示「不適用」 -->
            <div v-else-if="isEditingTransferTransaction" class="form-group">
              <label>類別</label>
              <div style="padding: 10px 12px; background: rgba(0, 0, 0, 0.2); border-radius: 4px; border: 1px solid rgba(0, 212, 255, 0.3); color: #a0aec0;">
                (不適用)
              </div>
            </div>

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
            <button type="submit" form="quick-transaction-form" class="btn btn-primary" style="flex: 1;">
              {{ quickForm.isEditing() ? '更新' : quickForm.isTransfer() ? '確認轉帳' : '新增交易' }}
            </button>
            <button 
              v-if="quickForm.isEditing() && !isEditingTransferTransaction" 
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

        <!-- 固定支出刪除選項 -->
        <div v-if="deleteConfirmType === 'recurring'" style="margin-bottom: 20px;">
          <p style="color: #ffd43b; margin-bottom: 15px;">請選擇刪除方式：</p>
          <div style="display: flex; gap: 10px; flex-direction: column;">
            <button
              @click="confirmDelete('all')"
              class="btn"
              style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); color: white; width: 100%;"
            >
              刪除固定支出及所有交易
            </button>
            <button
              @click="confirmDelete('future')"
              class="btn"
              style="background: linear-gradient(135deg, #ffa94d 0%, #ff922b 100%); color: white; width: 100%;"
            >
              刪除此筆及之後的交易
            </button>
            <button
              @click="confirmDelete('single')"
              class="btn"
              style="background: linear-gradient(135deg, #4dabf5 0%, #339af0 100%); color: white; width: 100%;"
            >
              僅刪除此筆交易
            </button>
          </div>

          <button
            @click="showDeleteConfirm = false"
            class="btn btn-secondary"
            style="margin-top: 10px; width: 100%;"
          >
            取消
          </button>
        </div>

        <!-- 固定支出刪除選項 (未生效/預測交易) -->
        <div v-else-if="deleteConfirmType === 'recurring-projected'" style="margin-bottom: 20px;">
          <p style="color: #ffd43b; margin-bottom: 15px;">此為尚未生效的固定支出，請選擇刪除方式：</p>
          <div style="display: flex; gap: 10px; flex-direction: column;">
            <button
              @click="confirmDelete('all')"
              class="btn"
              style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); color: white; width: 100%;"
            >
              刪除該筆支出所有交易明細
            </button>
            <button
              @click="confirmDelete('future')"
              class="btn"
              style="background: linear-gradient(135deg, #ffa94d 0%, #ff922b 100%); color: white; width: 100%;"
            >
              刪除此筆及之後的交易 (設定結束日期)
            </button>
          </div>

          <button
            @click="showDeleteConfirm = false"
            class="btn btn-secondary"
            style="margin-top: 10px; width: 100%;"
          >
            取消
          </button>
        </div>

        <!-- 分期刪除選項 -->
        <div v-else-if="deleteConfirmType === 'group'" style="margin-bottom: 20px;">
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
        <!-- 轉帳刪除選項 -->
        <div v-else-if="deleteConfirmType === 'transfer'" style="display: flex; gap: 10px;">
          <button
            @click="confirmDelete('single')"
            class="btn btn-danger"
            style="flex: 1;"
          >
            確定刪除（連同配對交易）
          </button>
          <button
            @click="showDeleteConfirm = false"
            class="btn btn-secondary"
            style="flex: 1;"
          >
            取消
          </button>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import type { Account, TransactionCreate, RecurringExpense, Budget } from '@/types'
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
const recurringExpenses = ref<RecurringExpense[]>([])
const accountSortMode = ref<'type' | 'currency' | 'balance'>('type')

const activeBudgets = computed(() => {
  const today = dateTimeUtils.getTodayString()
  return budgetsStore.budgets.filter(b => b.end_date >= today)
})

const togglePrimary = async (budget: Budget) => {
  try {
    // Optimistic update
    const wasPrimary = budget.is_primary
    budget.is_primary = !wasPrimary
    
    // If setting to true, we need to visually uncheck others
    if (!wasPrimary) {
      activeBudgets.value.forEach(b => {
        if (b.id !== budget.id) b.is_primary = false
      })
    }
    
    await budgetsStore.updateBudget(budget.id, { is_primary: !wasPrimary })
    await budgetsStore.fetchBudgets() // Refresh to ensure consistency
  } catch (err) {
    console.error('更新主要預算失敗:', err)
    messageModal.show('error', '更新主要預算失敗')
    budget.is_primary = !budget.is_primary // Revert
  }
}

// 帳戶排序邏輯
const sortedAccounts = computed(() => {
  const accounts = [...accountsStore.accounts]

  switch (accountSortMode.value) {
    case 'type':
      // 依照帳戶類型排序
      const typeOrder = ['cash', 'bank', 'credit_card', 'stored_value', 'securities', 'other']
      return accounts.sort((a, b) => {
        const aIndex = typeOrder.indexOf(a.account_type)
        const bIndex = typeOrder.indexOf(b.account_type)
        if (aIndex !== bIndex) {
          return aIndex - bIndex
        }
        // 同類型則依照名稱排序
        return a.name.localeCompare(b.name)
      })

    case 'currency':
      // 依照幣別排序
      return accounts.sort((a, b) => {
        if (a.currency !== b.currency) {
          return a.currency.localeCompare(b.currency)
        }
        // 同幣別則依照名稱排序
        return a.name.localeCompare(b.name)
      })

    case 'balance':
      // 依照金額排序（由高到低）
      return accounts.sort((a, b) => {
        const aBalance = dashboard.getAccountBalance(a.id)
        const bBalance = dashboard.getAccountBalance(b.id)
        return bBalance - aBalance
      })

    default:
      return accounts
  }
})

// Delete confirmation modal state
const showDeleteConfirm = ref(false)
const deleteConfirmMessage = ref('')
const deleteConfirmType = ref<'single' | 'group' | 'recurring' | 'recurring-projected' | 'installment-single' | 'transfer'>('single')
const currentDeletingTransaction = ref<any>(null)
const currentEditingTransaction = ref<any>(null)
const currentRecurringExpenseId = ref<number | null>(null)

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
  annualInterestRate: ref<number>(0),
  excludeFromBudget: ref<boolean>(false),
  // Recurring expense fields
  isRecurring: ref<boolean>(false),
  recurringDayOfMonth: ref<number>(1),
  
  // Transfer specific state
  transferTargetId: ref<number | null>(null),
  transferMode: ref<'transfer' | 'topup' | 'withdraw' | null>(null),

  reset: () => {
    quickForm.mode.value = 'create'
    quickForm.editId.value = null
    quickForm.transferTargetId.value = null
    quickForm.transferMode.value = null
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
    quickForm.annualInterestRate.value = 0
    quickForm.excludeFromBudget.value = false
    quickForm.isRecurring.value = false
    quickForm.recurringDayOfMonth.value = 1
    quickForm.activeCalculatorInput.value = 'amount'
    quickForm.isExpanded.value = false
  },
  
  isEditing: () => quickForm.mode.value === 'edit',
  isTransfer: () => !!quickForm.transferMode.value,
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

const availableSourceAccounts = computed(() => {
  if (!quickForm.isTransfer() || !quickForm.transferTargetId.value) {
    return accountsStore.accounts
  }

  const targetAccount = accountsStore.accounts.find(a => a.id === quickForm.transferTargetId.value)
  if (!targetAccount) return accountsStore.accounts

  // Rule: Cash's source can only be Bank
  if (targetAccount.account_type === 'cash') {
    return accountsStore.accounts.filter(a => a.account_type === 'bank')
  }

  // Rule: Bank's source can be Cash or Bank
  if (targetAccount.account_type === 'bank') {
    return accountsStore.accounts.filter(a => ['cash', 'bank'].includes(a.account_type))
  }

  // Rule: Stored Value's source can be Cash or Bank
  if (targetAccount.account_type === 'stored_value') {
    return accountsStore.accounts.filter(a => ['cash', 'bank'].includes(a.account_type))
  }

  return accountsStore.accounts
})

const currentAccount = computed(() => {
  // Use == to handle potential string/number mismatch from select input
  return accountsStore.accounts.find(a => a.id == quickForm.form.value.account_id)
})

const currentAccountCurrency = computed(() => {
  return currentAccount.value?.currency || 'TWD'
})

// 檢測是否正在編輯轉帳交易（包括 transfer_in 和 transfer_out）
const isEditingTransferTransaction = computed(() => {
  const transactionType = quickForm.form.value.transaction_type
  return transactionType === 'transfer_in' || transactionType === 'transfer_out'
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
  const annualRate = quickForm.annualInterestRate.value || 0

  if (annualRate >= 1) {
    // Use loan payment formula: P * r * (1+r)^n / ((1+r)^n - 1)
    // where P = principal, r = monthly rate, n = total periods
    const monthlyRate = annualRate / 12 / 100  // Convert annual % to monthly decimal
    const monthlyPayment = totalAmount * monthlyRate * Math.pow(1 + monthlyRate, periods) / (Math.pow(1 + monthlyRate, periods) - 1)
    const baseAmount = Math.floor(monthlyPayment)  // Round down to integer

    // Calculate last installment separately to account for rounding
    const totalPaidBeforeLast = baseAmount * (periods - 1)
    const totalWithInterest = Math.floor(monthlyPayment * periods)
    const lastAmount = totalWithInterest - totalPaidBeforeLast
    const totalInterest = totalWithInterest - totalAmount

    return {
      firstAmount: baseAmount,
      otherAmount: baseAmount,
      lastAmount: lastAmount,
      totalPeriods: periods,
      hasInterest: true,
      totalWithInterest: totalWithInterest,
      totalInterest: totalInterest,
      principal: totalAmount
    }
  } else {
    // Zero-interest: integer division
    const baseAmount = Math.floor(totalAmount / periods)
    const remainder = totalAmount - (baseAmount * periods)
    const firstAmount = baseAmount + remainder

    return {
      firstAmount: firstAmount,
      otherAmount: baseAmount,
      lastAmount: baseAmount,
      totalPeriods: periods,
      hasInterest: false
    }
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

const handleAccountChange = () => {
  // When account changes, update selected currency to match new account's currency
  const newAccount = accountsStore.accounts.find(a => a.id == quickForm.form.value.account_id)
  if (newAccount && quickForm.isEditing()) {
    // In edit mode, reset to account's currency to avoid confusion
    quickForm.selectedCurrency.value = newAccount.currency
    quickForm.foreignAmount.value = null
  }
}

// Unique Exchange Rates (deduplicated by currency_code, prioritize 'bot')
const uniqueExchangeRates = computed(() => {
  const uniqueRates = new Map<string, typeof exchangeRatesStore.rates[0]>()
  
  exchangeRatesStore.rates.forEach(rate => {
    const existing = uniqueRates.get(rate.currency_code)
    if (!existing) {
      uniqueRates.set(rate.currency_code, rate)
    } else if (rate.bank === 'bot' && existing.bank !== 'bot') {
      // Prioritize Bank of Taiwan (bot)
      uniqueRates.set(rate.currency_code, rate)
    }
  })
  
  return Array.from(uniqueRates.values()).sort((a, b) => 
    a.currency_code.localeCompare(b.currency_code)
  )
})

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

const openQuickTransaction = (account?: Account) => {
  quickForm.resetForm()
  if (account) {
    quickForm.form.value.account_id = account.id
    // Set default currency to account currency
    quickForm.selectedCurrency.value = account.currency
  } else {
    // Default to last used account or first available
    const lastAccountId = localStorage.getItem('last_account_id')
    if (lastAccountId) {
      const accountExists = accountsStore.accounts.find(a => a.id === Number(lastAccountId))
      if (accountExists) {
        quickForm.form.value.account_id = Number(lastAccountId)
        quickForm.selectedCurrency.value = accountExists.currency
      }
    } else if (accountsStore.accounts.length > 0) {
      quickForm.form.value.account_id = accountsStore.accounts[0].id
      quickForm.selectedCurrency.value = accountsStore.accounts[0].currency
    }
  }
  
  quickForm.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
  if (categoriesStore.categories.length > 0) {
    quickForm.form.value.category = categoriesStore.categories[0].name
  }
  
  fetchDescriptionHistory()
  quickModal.open()
}

const openTransferModal = (account: Account, mode: 'transfer' | 'topup' | 'withdraw') => {
  quickForm.reset()
  quickForm.transferMode.value = mode
  
  // Always set the selected account as the Target (To)
  quickForm.transferTargetId.value = account.id
  
  if (mode === 'topup') {
    quickForm.form.value.description = '儲值'
  } else if (mode === 'withdraw') {
    quickForm.form.value.description = '提領'
  } else {
    quickForm.form.value.description = '轉帳'
  }
  
  quickForm.form.value.transaction_date = dateTimeUtils.getCurrentDateTime()
  
  // Auto-select first available source account
  nextTick(() => {
    if (availableSourceAccounts.value.length > 0) {
      quickForm.form.value.account_id = availableSourceAccounts.value[0].id
    }
  })

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
  currentEditingTransaction.value = transaction
  showDailyModal.value = false
  fetchDescriptionHistory()
  quickModal.open()
  
  // Scroll to quick form
  const quickFormElement = document.getElementById('quick-transaction-form')
  if (quickFormElement) {
    quickFormElement.scrollIntoView({ behavior: 'smooth' })
  }
}

const handleAddTransactionFromCalendar = (dateStr: string) => {
  // 1. Open Quick Form (Reset first)
  quickForm.reset()
  quickModal.open()
  
  // 2. Set Date and Time
  // dateStr is YYYY-MM-DD
  // Get current time HH:mm
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  
  // Combine date and time
  quickForm.form.value.transaction_date = `${dateStr}T${hours}:${minutes}`
  
  // 3. Set Account
  // Use last used account from localStorage or default to first account
  const lastAccountId = localStorage.getItem('last_account_id')
  if (lastAccountId) {
    const account = accountsStore.accounts.find(a => a.id === Number(lastAccountId))
    if (account) {
      quickForm.form.value.account_id = account.id
    } else if (accountsStore.accounts.length > 0) {
      quickForm.form.value.account_id = accountsStore.accounts[0].id
    }
  } else if (accountsStore.accounts.length > 0) {
    quickForm.form.value.account_id = accountsStore.accounts[0].id
  }
  
  // Scroll to quick form
  const quickFormElement = document.getElementById('quick-transaction-form')
  if (quickFormElement) {
    quickFormElement.scrollIntoView({ behavior: 'smooth' })
  }
}

const handleDeleteTransaction = async () => {
  if (!quickForm.isEditing()) return

  // Find the transaction being edited
  let transaction = transactionsStore.transactions.find(t => t.id === quickForm.editingId.value)
  
  // If not found in store, check if it's a projected recurring expense (negative ID)
  if (!transaction && quickForm.editingId.value && quickForm.editingId.value < 0) {
    transaction = currentEditingTransaction.value
  }
  
  currentDeletingTransaction.value = transaction

  // Check if it's a recurring expense transaction
  if (transaction?.is_from_recurring && transaction.recurring_group_id) {
    // Fetch recurring expenses to find the ID
    try {
      // If we already have recurringExpenses loaded, use them
      let recurringExpense = recurringExpenses.value.find(re => re.recurring_group_id === transaction.recurring_group_id)
      
      if (!recurringExpense) {
         const response = await api.getRecurringExpenses()
         recurringExpense = response.data.find((re: any) => re.recurring_group_id === transaction.recurring_group_id)
      }

      if (recurringExpense) {
        currentRecurringExpenseId.value = recurringExpense.id
        
        // If it's a projected transaction (negative ID), we can't delete "single" because it doesn't exist yet.
        // We should probably only offer "future" (stop from now) or "all".
        // Or "single" could mean "skip this occurrence" if the backend supports it (by creating a skipped record).
        // For now, let's assume standard options but maybe warn or adjust text.
        
        if (transaction.id < 0) {
             deleteConfirmMessage.value = `此為尚未生效的固定支出 (每月 ${recurringExpense.day_of_month} 號)`
             deleteConfirmType.value = 'recurring-projected'
        } else {
             deleteConfirmMessage.value = `此交易為固定支出自動產生的交易 (每月 ${recurringExpense.day_of_month} 號)`
             deleteConfirmType.value = 'recurring'
        }
        
        showDeleteConfirm.value = true
      } else {
        // Fallback to regular single delete
        deleteConfirmMessage.value = '確定要刪除此交易嗎？刪除後將無法復原。'
        deleteConfirmType.value = 'single'
        showDeleteConfirm.value = true
      }
    } catch (error) {
      console.error('Failed to fetch recurring expenses:', error)
      deleteConfirmMessage.value = '確定要刪除此交易嗎？刪除後將無法復原。'
      deleteConfirmType.value = 'single'
      showDeleteConfirm.value = true
    }
  }
  // Check if it's an installment transaction
  else if (transaction?.is_installment && transaction.installment_group_id) {
    deleteConfirmMessage.value = `此交易為分期交易 (第 ${transaction.installment_number} 期，共 ${transaction.total_installments} 期)`
    deleteConfirmType.value = 'group'
    showDeleteConfirm.value = true
  }
  // Check if it's a transfer transaction
  else if (transaction?.transaction_type === 'transfer_in' || transaction?.transaction_type === 'transfer_out') {
    const typeLabel = transaction.transaction_type === 'transfer_in' ? '轉入' : '轉出'
    deleteConfirmMessage.value = `此為${typeLabel}交易，刪除時將同時移除對應的轉出/轉入記錄。確定要刪除嗎？`
    deleteConfirmType.value = 'transfer'
    showDeleteConfirm.value = true
  }
  else {
    deleteConfirmMessage.value = '確定要刪除此交易嗎？刪除後將無法復原。'
    deleteConfirmType.value = 'single'
    showDeleteConfirm.value = true
  }
}

const confirmDelete = async (deleteType: 'single' | 'group' | 'future' | 'all') => {
  showDeleteConfirm.value = false

  const transaction = currentDeletingTransaction.value
  if (!transaction) return

  try {
    // Handle recurring expense deletions
    if ((deleteConfirmType.value === 'recurring' || deleteConfirmType.value === 'recurring-projected') && currentRecurringExpenseId.value) {
      const mode = deleteType === 'single' ? 'single' : deleteType === 'future' ? 'future' : 'all'
      
      // Special handling for projected transactions (negative ID)
      if (transaction.id < 0) {
        if (mode === 'all') {
          // For 'all', we just delete the recurring expense, no transaction ID needed
          await api.deleteRecurringExpense(
            currentRecurringExpenseId.value,
            'all'
          )
          messageModal.showSuccess('已刪除固定支出及所有相關交易')
        } else if (mode === 'future') {
          // For 'future', we update the end_date to the day before this transaction
          // BUT, if this transaction is the FIRST one (or before start_date), we should delete the whole thing
          
          let shouldDeleteAll = false
          let recurringExpense = recurringExpenses.value.find(re => re.id === currentRecurringExpenseId.value)
          
          // If not found in local state, fetch fresh data
          if (!recurringExpense) {
            try {
              const res = await api.getRecurringExpenses()
              recurringExpense = res.data.find(re => re.id === currentRecurringExpenseId.value)
            } catch (e) {
              console.error('Failed to fetch recurring expenses for check', e)
            }
          }
          
          if (recurringExpense) {
            const txDate = new Date(transaction.transaction_date)
            const startDate = new Date(recurringExpense.start_date)
            
            // Robust check: Since recurring expenses are monthly, if the transaction date is 
            // within 15 days of the start date, it MUST be the first occurrence.
            // This handles any timezone discrepancies (e.g. start_date being in UTC vs local txDate).
            const bufferTime = 15 * 24 * 60 * 60 * 1000 // 15 days in ms
            
            if (txDate.getTime() <= startDate.getTime() + bufferTime) {
              shouldDeleteAll = true
            }
          }
          
          if (shouldDeleteAll) {
             await api.deleteRecurringExpense(
                currentRecurringExpenseId.value,
                'all'
              )
              messageModal.showSuccess('已刪除固定支出及所有相關交易')
          } else {
              const txDate = new Date(transaction.transaction_date)
              txDate.setDate(txDate.getDate() - 1)
              const endDate = txDate.toISOString()
              
              await api.updateRecurringExpense(currentRecurringExpenseId.value, {
                end_date: endDate
              })
              messageModal.showSuccess('已設定結束日期，此筆及之後的交易將不再產生')
          }
        }
      } else {
        // Existing logic for real transactions
        await api.deleteRecurringExpense(
          currentRecurringExpenseId.value,
          mode as 'single' | 'future' | 'all',
          transaction.id
        )

        if (mode === 'single') {
          messageModal.showSuccess('已刪除此筆交易')
        } else if (mode === 'future') {
          messageModal.showSuccess('已刪除此筆及之後的所有交易')
        } else {
          messageModal.showSuccess('已刪除固定支出及所有相關交易')
        }
      }
    }
    // Handle installment group deletions
    else if (deleteType === 'group' && transaction.installment_group_id) {
      await api.deleteInstallmentGroup(transaction.installment_group_id)
      messageModal.showSuccess(`已刪除整組分期交易 (${transaction.total_installments} 期)`)
    }
    // Handle single transaction deletion
    else {
      await transactionsStore.deleteTransaction(quickForm.editingId.value!)
      messageModal.showSuccess('交易已刪除')
    }

    await Promise.all([
      accountsStore.fetchAccounts(),
      budgetsStore.fetchBudgets(),
      transactionsStore.fetchTransactions(),
      fetchDescriptionHistory(),
      api.getRecurringExpenses().then(res => recurringExpenses.value = res.data)
    ])

    if (monthlyChartRef.value) {
      await monthlyChartRef.value.refresh()
    }

    closeQuickTransaction()
  } catch (error: any) {
    messageModal.showError(error.response?.data?.detail || '刪除交易失敗')
  } finally {
    currentDeletingTransaction.value = null
    currentRecurringExpenseId.value = null
  }
}

const handleQuickTransaction = async () => {
  // Handle Transfer
  if (quickForm.isTransfer()) {
    if (!quickForm.transferTargetId.value) {
      messageModal.show('error', '請選擇轉入帳戶')
      return
    }
    if (quickForm.form.value.account_id === quickForm.transferTargetId.value) {
      messageModal.show('error', '轉出與轉入帳戶不能相同')
      return
    }

    // Check for sufficient funds - REMOVED per user request
    // const sourceAccount = accountsStore.accounts.find(a => a.id === quickForm.form.value.account_id)
    // if (sourceAccount && sourceAccount.balance < quickForm.form.value.amount) {
    //   messageModal.show('error', '轉出帳戶餘額不足')
    //   return
    // }

    try {
      await transactionsStore.transfer({
        from_account_id: quickForm.form.value.account_id,
        to_account_id: quickForm.transferTargetId.value,
        amount: quickForm.form.value.amount,
        transaction_date: quickForm.form.value.transaction_date,
        description: quickForm.form.value.description,
        note: quickForm.form.value.note
      })
      
      messageModal.show('success', '轉帳成功')
      quickModal.close()
      
      // Refresh data
      await Promise.all([
        accountsStore.fetchAccounts(),
        transactionsStore.fetchTransactions(),
        budgetsStore.fetchBudgets(), // Budgets might be affected if we didn't exclude transfers (but we did)
        dashboard.fetchData()
      ])
    } catch (error) {
      // Error handled by store
    }
    return
  }

  try {
    // Check if this is a recurring expense
    if (quickForm.isRecurring.value && quickForm.form.value.transaction_type === 'debit' && !quickForm.isEditing()) {
      // Create recurring expense instead of transaction
      const recurringData = {
        description: quickForm.form.value.description,
        amount: quickForm.form.value.amount,
        category: quickForm.form.value.category || undefined,
        note: quickForm.form.value.note || undefined,
        day_of_month: quickForm.recurringDayOfMonth.value,
        account_id: quickForm.form.value.account_id
      }

      await api.createRecurringExpense(recurringData)
      messageModal.showSuccess(`已成功建立固定支出！系統將在每月 ${quickForm.recurringDayOfMonth.value} 號自動建立交易。`)

      // Refresh data
      await Promise.all([
        accountsStore.fetchAccounts(),
        budgetsStore.fetchBudgets(),
        transactionsStore.fetchTransactions(),
        transactionsStore.fetchTransactions(),
        fetchDescriptionHistory(),
        api.getRecurringExpenses().then(res => recurringExpenses.value = res.data)
      ])

      if (monthlyChartRef.value) {
        await monthlyChartRef.value.refresh()
      }

      closeQuickTransaction()
      return
    }

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
      transactionData.annual_interest_rate = quickForm.annualInterestRate.value > 0 ? quickForm.annualInterestRate.value : null
      transactionData.exclude_from_budget = quickForm.excludeFromBudget.value
    }

    if (quickForm.isEditing()) {
      await transactionsStore.updateTransaction(quickForm.editingId.value!, {
        account_id: transactionData.account_id,
        description: transactionData.description,
        note: transactionData.note,
        amount: transactionData.amount,
        category: transactionData.category,
        transaction_date: transactionData.transaction_date,
        foreign_amount: transactionData.foreign_amount,
        foreign_currency: transactionData.foreign_currency,
        transaction_type: transactionData.transaction_type
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
      
      // Save last used account
      localStorage.setItem('last_account_id', String(transactionData.account_id))
      
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
        fetchDescriptionHistory(),
        api.getRecurringExpenses().then(res => recurringExpenses.value = res.data)
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

/* 時間範圍切換按鈕樣式 */
.time-range-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 16px;
  background: transparent;
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  font-weight: 500;
}

.time-range-btn.active {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 212, 255, 0.3);
}

.time-range-btn:hover:not(.active) {
  background: rgba(0, 212, 255, 0.1);
  color: #00d4ff;
}

/* 排序按鈕樣式（複用時間範圍按鈕樣式） */
.sort-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 16px;
  background: transparent;
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  font-weight: 500;
}

.sort-btn.active {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 212, 255, 0.3);
}

.sort-btn:hover:not(.active) {
  background: rgba(0, 212, 255, 0.1);
  color: #00d4ff;
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

/* Account Card Responsive Styles */
.account-card {
  border: 1px solid rgba(0, 212, 255, 0.2);
  padding: 15px;
  border-radius: 8px;
  background: rgba(0, 212, 255, 0.03);
  transition: all 0.3s ease;
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 15px;
  align-items: center;
}

.account-card:hover {
  border-color: rgba(0, 212, 255, 0.5);
}

.account-info h4 {
  margin: 0 0 5px 0;
}

.account-info p {
  margin: 0;
  font-size: 14px;
  color: #a0aec0;
}

.account-balance {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 200px;
}

.balance-display {
  display: flex;
  align-items: baseline;
  gap: 10px;
  width: 100%;
  justify-content: flex-end;
}

.currency-label {
  color: #a0aec0;
  font-size: 16px;
  font-weight: 500;
  flex-shrink: 0;
}

.balance-amount {
  font-size: 24px;
  font-weight: bold;
  white-space: nowrap;
}

.account-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-width: 190px;
}

.btn-action {
  padding: 8px 15px;
  color: white;
  white-space: nowrap;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  width: 90px;
  text-align: center;
}

.btn-accounting {
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
}

.btn-topup {
  background: linear-gradient(135deg, #36D1DC 0%, #5B86E5 100%);
}

.btn-withdraw {
  background: linear-gradient(135deg, #FF512F 0%, #DD2476 100%);
}

.btn-transfer {
  background: linear-gradient(135deg, #1FA2FF 0%, #12D8FA 100%);
}

/* Mobile Layout */
@media (max-width: 768px) {
  .account-card {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    gap: 12px;
  }

  .account-balance {
    width: 100%;
    text-align: left;
  }

  .account-actions {
    width: 100%;
    min-width: auto;
    justify-content: flex-end;
    overflow-x: auto;
    padding-bottom: 2px;
  }

  .btn-action {
    flex: 1;
    width: auto;
    text-align: center;
    padding: 10px;
  }
}
</style>
