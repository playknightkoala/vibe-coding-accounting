import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Dashboard from '@/views/Dashboard.vue'
import Accounts from '@/views/Accounts.vue'
import Transactions from '@/views/Transactions.vue'
import Budgets from '@/views/Budgets.vue'
import Profile from '@/views/Profile.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 防止無限重定向
  if (to.path === from.path) {
    next()
    return
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    if (to.path !== '/login') {
      next('/login')
    } else {
      next()
    }
  } else if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    if (to.path !== '/') {
      next('/')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
