import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import ForgotPassword from '@/views/ForgotPassword.vue'
import ResetPassword from '@/views/ResetPassword.vue'
import Privacy from '@/views/Privacy.vue'
import Terms from '@/views/Terms.vue'
import Dashboard from '@/views/Dashboard.vue'
import Accounts from '@/views/Accounts.vue'

import Budgets from '@/views/Budgets.vue'
import Profile from '@/views/Profile.vue'
import Reports from '@/views/Reports.vue'
import TestChart from '@/views/TestChart.vue'
import Admin from '@/views/Admin.vue'
import ExchangeRates from '@/views/ExchangeRates.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Login',
    component: Login,
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { public: true }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPassword,
    meta: { public: true }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPassword,
    meta: { public: true }
  },
  {
    path: '/google-callback',
    name: 'GoogleCallback',
    component: () => import('@/views/GoogleCallback.vue'),
    meta: { public: true }
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: Privacy,
    meta: { public: true }
  },
  {
    path: '/terms',
    name: 'Terms',
    component: Terms,
    meta: { public: true }
  },
  {
    path: '/dashboard',
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
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/exchange-rates',
    name: 'ExchangeRates',
    component: ExchangeRates,
    meta: { requiresAuth: true }
  },
  {
    path: '/test-chart',
    name: 'TestChart',
    component: TestChart
  },
  // Catch-all route for 404 - must be last
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated

  // Public pages that don't require authentication
  const publicPages = ['/', '/register', '/forgot-password', '/reset-password']
  const isPublicPage = publicPages.includes(to.path)

  // Handle public pages
  if (isPublicPage) {
    // Only redirect to dashboard from login/register pages if authenticated
    // Allow forgot-password and reset-password pages even when authenticated
    if ((to.path === '/' || to.path === '/register') && isAuthenticated) {
      next('/dashboard')
    } else {
      next()
    }
    return
  }

  // Handle protected pages
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      // Not authenticated, redirect to login
      next('/')
      return
    }

    // Check admin permission
    if (to.meta.requiresAdmin) {
      // Ensure user data is loaded
      if (!authStore.user) {
        await authStore.fetchUser()
      }

      if (!authStore.user?.is_admin) {
        // Not an admin, redirect to dashboard
        next('/dashboard')
        return
      }
    }

    // Authenticated and authorized, allow access
    next()
    return
  }

  // Default: allow navigation
  next()
})

export default router
