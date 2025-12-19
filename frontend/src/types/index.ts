export interface User {
  id: number
  email: string
  is_google_user: boolean
  is_admin: boolean
  is_blocked: boolean
  two_factor_enabled: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string | null
}

export interface UserAdminInfo extends User {
  transaction_count: number
  budget_count: number
  account_count: number
}

export interface AdminUserUpdate {
  email?: string
  password?: string
  is_admin?: boolean
  is_blocked?: boolean
  two_factor_enabled?: boolean
}

export interface UserCreate {
  email: string
  password: string
  turnstile_token?: string
}

export interface UserLogin {
  email: string
  password: string
}

export interface UserUpdate {
  current_password?: string
  new_password?: string
}

export interface Token {
  access_token: string
  token_type: string
  requires_2fa?: boolean
}

export interface TwoFactorSetup {
  secret: string
  qr_code: string
}

export interface TwoFactorVerify {
  token: string
}

export interface Account {
  id: number
  name: string
  account_type: 'cash' | 'bank' | 'credit_card' | 'stored_value' | 'securities' | 'other'
  balance: number
  currency: string
  description: string | null
  user_id: number
  created_at: string
  updated_at: string | null
}

export interface AccountCreate {
  name: string
  account_type: 'cash' | 'bank' | 'credit_card' | 'stored_value' | 'securities' | 'other'
  currency?: string
  description?: string
  initial_balance?: number
}

export interface AccountUpdate {
  name?: string
  description?: string
}

export interface Transaction {
  id: number
  description: string
  amount: number
  transaction_type: 'credit' | 'debit' | 'installment'
  category: string | null
  transaction_date: string
  account_id: number
  created_at: string
  updated_at: string | null
  note?: string
  foreign_amount?: number
  foreign_currency?: string
  // Installment fields
  is_installment: boolean
  installment_group_id?: string
  installment_number?: number
  total_installments?: number
  total_amount?: number
  remaining_amount?: number
  annual_interest_rate?: number
  exclude_from_budget: boolean
  // Recurring expense fields
  recurring_group_id?: string
  is_from_recurring: boolean
}

export interface TransactionCreate {
  description: string
  amount: number
  transaction_type: 'credit' | 'debit' | 'installment'
  category?: string
  transaction_date: string
  account_id: number
  note?: string
  foreign_amount?: number
  foreign_currency?: string
  exclude_from_budget?: boolean
  // Installment specific fields
  is_installment?: boolean
  total_installments?: number
  billing_day?: number
  annual_interest_rate?: number
}

export interface TransactionUpdate {
  description?: string
  amount?: number
  category?: string
  transaction_date?: string
  note?: string
  foreign_currency?: string
  transaction_type?: 'credit' | 'debit' | 'installment'
}

export interface TransferCreate {
  from_account_id: number
  to_account_id: number
  amount: number
  transaction_date: string
  description: string
  note?: string
}

export interface Budget {
  id: number
  name: string
  category_names: string[]  // 改為類別名稱列表
  amount: number
  daily_limit?: number
  daily_limit_mode: 'auto' | 'manual'  // 每日預算計算模式
  spent: number
  range_mode: 'custom' | 'recurring'
  period?: 'monthly' | 'quarterly' | 'yearly'
  start_date: string
  end_date: string
  account_ids: number[]  // 改為帳戶ID列表
  user_id: number
  parent_budget_id?: number
  is_latest_period: boolean
  over_budget_days: number  // 超支天數
  within_budget_days: number  // 預算內天數
  last_stats_update: string | null  // 最後統計更新時間
  created_at: string
  updated_at: string | null
}

export interface BudgetCreate {
  name: string
  category_names: string[]  // 改為類別名稱列表
  amount: number
  daily_limit?: number
  daily_limit_mode: 'auto' | 'manual'  // 每日預算計算模式
  range_mode: 'custom' | 'recurring'
  period?: 'monthly' | 'quarterly' | 'yearly'
  start_date?: string  // recurring模式可為空
  end_date?: string    // recurring模式可為空
  account_ids: number[]  // 改為帳戶ID列表
}

export interface BudgetUpdate {
  name?: string
  category_names?: string[]  // 改為類別名稱列表
  amount?: number
  daily_limit?: number
  daily_limit_mode?: 'auto' | 'manual'  // 每日預算計算模式
  spent?: number
  range_mode?: 'custom' | 'recurring'
  period?: 'monthly' | 'quarterly' | 'yearly'
  start_date?: string
  end_date?: string
  account_ids?: number[]  // 改為帳戶ID列表
}

export interface Category {
  id: number
  name: string
  user_id: number
  order_index: number
  created_at: string
  updated_at: string | null
}

export interface CategoryCreate {
  name: string
}

export interface CategoryUpdate {
  name?: string
  order_index?: number
}

export interface CategoryOrderUpdate {
  category_id: number
  order_index: number
}

export interface DailyStats {
  date: string
  credit: number
  debit: number
}

export interface MonthlyStats {
  daily_stats: DailyStats[]
}

// Report types
export interface CategoryStats {
  category: string
  amount: number
  percentage: number
  credit: number
  debit: number
}

export interface AccountStats {
  account_id: number
  account_name: string
  amount: number
  percentage: number
  credit: number
  debit: number
  balance: number
}

export interface TransactionDetail {
  id: number
  description: string
  amount: number
  transaction_type: string
  category: string | null
  transaction_date: string
  account_id: number
  account_name: string
  note?: string
  foreign_amount?: number
  foreign_currency?: string
}

export interface DailyTransactions {
  date: string
  total_credit: number
  total_debit: number
  transactions: TransactionDetail[]
}

export interface OverviewReport {
  total_credit: number
  total_debit: number
  net_amount: number
  category_stats: CategoryStats[]
  top_five_income: TransactionDetail[]
  top_five_expense: TransactionDetail[]
}

export interface DetailsReport {
  daily_transactions: DailyTransactions[]
  total_credit: number
  total_debit: number
}

export interface CategoryReport {
  category_stats: CategoryStats[]
  total_amount: number
  total_credit: number
  total_debit: number
}

export interface RankingReport {
  expense_ranking: TransactionDetail[]
  income_ranking: TransactionDetail[]
}

export interface AccountReport {
  account_stats: AccountStats[]
  total_amount: number
}

export interface ExchangeRate {
  id: number
  bank: string
  currency_code: string
  currency_name: string
  buying_rate: number | null
  selling_rate: number | null
  updated_at: string
}

// Recurring Expense types
export interface RecurringExpense {
  id: number
  description: string
  amount: number
  category: string | null
  note: string | null
  day_of_month: number
  account_id: number
  recurring_group_id: string
  start_date: string
  end_date: string | null
  is_active: boolean
  last_executed_date: string | null
  created_at: string
  updated_at: string | null
}

export interface RecurringExpenseCreate {
  description: string
  amount: number
  category?: string
  note?: string
  day_of_month: number
  account_id: number
}

export interface RecurringExpenseUpdate {
  description?: string
  amount?: number
  category?: string
  note?: string
  day_of_month?: number
  is_active?: boolean
  end_date?: string
}

// AI財務報告相關類型
export interface AIFinancialSummary {
  // 報告元數據
  report_generated_at: string
  report_period_start: string
  report_period_end: string
  user_id: number

  // 財務概況
  total_income: number
  total_expense: number
  net_income: number
  savings_rate: number

  // 帳戶狀況
  total_assets: number
  accounts_summary: Array<{
    name: string
    type: string
    balance: number
    currency: string
  }>

  // 支出分析
  top_expense_categories: Array<{
    category: string
    amount: number
    percentage: number
  }>
  top_income_categories: Array<{
    category: string
    amount: number
    percentage: number
  }>

  // 預算執行情況
  budgets_summary: Array<{
    name: string
    amount: number
    spent: number
    percentage: number
    status: string
  }>
  total_budget_amount: number
  total_budget_spent: number
  budget_utilization: number

  // 交易統計
  total_transactions: number
  average_transaction_amount: number
  largest_expense: {
    description: string
    amount: number
    date: string
    category: string
  } | null
  largest_income: {
    description: string
    amount: number
    date: string
    category: string
  } | null

  // 趨勢分析
  daily_average_expense: number
  daily_average_income: number
  expense_trend: string

  // 警示與建議
  alerts: string[]
  financial_health_score: number

  // 文本報告
  text_report: string
}
