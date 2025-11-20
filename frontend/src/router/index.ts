import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Dashboard from '@/views/Dashboard.vue'
import Accounts from '@/views/Accounts.vue'
import Transactions from '@/views/Transactions.vue'
import Budgets from '@/views/Budgets.vue'
import Profile from '@/views/Profile.vue'
import Reports from '@/views/Reports.vue'
import TestChart from '@/views/TestChart.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/accounts',
    name: 'Accounts',
    component: Accounts,
    meta: { requiresAuth: true }
  },
  {
    path: '/transactions',
    name: 'Transactions',
    component: Transactions,
    meta: { requiresAuth: true }
  },
  {
    path: '/budgets',
    name: 'Budgets',
    component: Budgets,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: Reports,
    meta: { requiresAuth: true }
  },
  {
    path: '/test-chart',
    name: 'TestChart',
    component: TestChart
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 需要認證的頁面
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // 未登入，導向登入頁
      next('/login')
    } else {
      // 已登入，允許訪問
      next()
    }
  }
  // 登入或註冊頁面
  else if (to.name === 'Login' || to.name === 'Register') {
    if (authStore.isAuthenticated) {
      // 已登入，導向首頁
      next('/')
    } else {
      // 未登入，允許訪問
      next()
    }
  }
  // 其他頁面
  else {
    next()
  }
})

export default router
