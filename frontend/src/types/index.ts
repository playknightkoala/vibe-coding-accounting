export interface User {
  id: number
  username: string
  two_factor_enabled: boolean
  created_at: string
  updated_at: string | null
}

export interface UserCreate {
  username: string
  password: string
}

export interface UserLogin {
  username: string
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
  transaction_type: 'credit' | 'debit'
  category: string | null
  transaction_date: string
  account_id: number
  created_at: string
  updated_at: string | null
  note?: string
}

export interface TransactionCreate {
  description: string
  amount: number
  transaction_type: 'credit' | 'debit'
  category?: string
  transaction_date: string
  account_id: number
  note?: string
}

export interface TransactionUpdate {
  description?: string
  amount?: number
  category?: string
  transaction_date?: string
  note?: string
}

export interface Budget {
  id: number
  name: string
  category_names: string[]  // 改為類別名稱列表
  amount: number
  daily_limit?: number
  spent: number
  range_mode: 'custom' | 'recurring'
  period?: 'monthly' | 'quarterly' | 'yearly'
  start_date: string
  end_date: string
  account_ids: number[]  // 改為帳戶ID列表
  user_id: number
  parent_budget_id?: number
  is_latest_period: boolean
  created_at: string
  updated_at: string | null
}

export interface BudgetCreate {
  name: string
  category_names: string[]  // 改為類別名稱列表
  amount: number
  daily_limit?: number
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
}

export interface RankingReport {
  expense_ranking: TransactionDetail[]
  income_ranking: TransactionDetail[]
}

export interface AccountReport {
  account_stats: AccountStats[]
  total_amount: number
}
