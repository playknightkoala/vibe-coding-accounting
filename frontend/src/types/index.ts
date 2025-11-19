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
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
  balance: number
  currency: string
  description: string | null
  user_id: number
  created_at: string
  updated_at: string | null
}

export interface AccountCreate {
  name: string
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense'
  currency?: string
  description?: string
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
}

export interface TransactionCreate {
  description: string
  amount: number
  transaction_type: 'credit' | 'debit'
  category?: string
  transaction_date: string
  account_id: number
}

export interface TransactionUpdate {
  description?: string
  amount?: number
  category?: string
  transaction_date?: string
}

export interface Budget {
  id: number
  name: string
  category: string
  amount: number
  daily_limit?: number
  spent: number
  period: 'monthly' | 'quarterly' | 'yearly'
  start_date: string
  end_date: string
  account_id: number
  user_id: number
  created_at: string
  updated_at: string | null
}

export interface BudgetCreate {
  name: string
  category: string
  amount: number
  daily_limit?: number
  period: 'monthly' | 'quarterly' | 'yearly'
  start_date: string
  end_date: string
  account_id: number
}

export interface BudgetUpdate {
  name?: string
  category?: string
  amount?: number
  daily_limit?: number
  spent?: number
  period?: 'monthly' | 'quarterly' | 'yearly'
  start_date?: string
  end_date?: string
  account_id?: number | null
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
