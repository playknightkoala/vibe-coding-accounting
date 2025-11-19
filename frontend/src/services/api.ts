import axios from 'axios'
import type { AxiosInstance } from 'axios'
import type {
  UserCreate,
  UserLogin,
  UserUpdate,
  User,
  Token,
  TwoFactorSetup,
  TwoFactorVerify,
  Account,
  AccountCreate,
  AccountUpdate,
  Transaction,
  TransactionCreate,
  TransactionUpdate,
  Budget,
  BudgetCreate,
  BudgetUpdate,
  Category,
  CategoryCreate,
  CategoryUpdate,
  CategoryOrderUpdate
} from '@/types'

const API_URL = 'http://localhost:8000/api'

const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // 只有在不是登入或註冊請求時才跳轉
      const isAuthRequest = error.config.url?.includes('/auth/login') ||
                           error.config.url?.includes('/auth/register')

      if (!isAuthRequest) {
        // Token 失效，清除登入狀態並跳轉到登入頁面
        localStorage.removeItem('token')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default {
  // 認證
  register(userData: UserCreate) {
    return api.post<User>('/auth/register', userData)
  },

  login(credentials: UserLogin) {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    return api.post<Token>('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  verify2FA(credentials: UserLogin, token: string) {
    return api.post<Token>('/auth/login/2fa/verify', {
      username: credentials.username,
      password: credentials.password,
      token: token
    })
  },

  // 使用者設定
  getUserProfile() {
    return api.get<User>('/users/me')
  },

  updateUserProfile(userData: UserUpdate) {
    return api.put<User>('/users/me', userData)
  },

  setup2FA() {
    return api.post<TwoFactorSetup>('/users/me/2fa/setup')
  },

  verify2FASetup(data: TwoFactorVerify) {
    return api.post('/users/me/2fa/verify', data)
  },

  disable2FA(data: TwoFactorVerify) {
    return api.post('/users/me/2fa/disable', data)
  },

  // 帳戶
  getAccounts() {
    return api.get<Account[]>('/accounts/')
  },

  createAccount(accountData: AccountCreate) {
    return api.post<Account>('/accounts/', accountData)
  },

  updateAccount(id: number, accountData: AccountUpdate) {
    return api.put<Account>(`/accounts/${id}`, accountData)
  },

  deleteAccount(id: number) {
    return api.delete(`/accounts/${id}`)
  },

  // 交易
  getTransactions(accountId: number | null = null) {
    const params = accountId ? { account_id: accountId } : {}
    return api.get<Transaction[]>('/transactions/', { params })
  },

  createTransaction(transactionData: TransactionCreate) {
    return api.post<Transaction>('/transactions/', transactionData)
  },

  updateTransaction(id: number, transactionData: TransactionUpdate) {
    return api.put<Transaction>(`/transactions/${id}`, transactionData)
  },

  deleteTransaction(id: number) {
    return api.delete(`/transactions/${id}`)
  },

  // 預算
  getBudgets() {
    return api.get<Budget[]>('/budgets/')
  },

  createBudget(budgetData: BudgetCreate) {
    return api.post<Budget>('/budgets/', budgetData)
  },

  updateBudget(id: number, budgetData: BudgetUpdate) {
    return api.put<Budget>(`/budgets/${id}`, budgetData)
  },

  deleteBudget(id: number) {
    return api.delete(`/budgets/${id}`)
  },

  // 類別
  getCategories() {
    return api.get<Category[]>('/categories/')
  },

  createCategory(categoryData: CategoryCreate) {
    return api.post<Category>('/categories/', categoryData)
  },

  updateCategory(id: number, categoryData: CategoryUpdate) {
    return api.put<Category>(`/categories/${id}`, categoryData)
  },

  reorderCategories(orders: CategoryOrderUpdate[]) {
    return api.post('/categories/reorder', orders)
  },

  deleteCategory(id: number) {
    return api.delete(`/categories/${id}`)
  }
}
