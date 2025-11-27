import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { public: true }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: { public: true }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPassword.vue'),
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
    component: () => import('@/views/Privacy.vue'),
    meta: { public: true }
  },
  {
    path: '/terms',
    name: 'Terms',
    component: () => import('@/views/Terms.vue'),
    meta: { public: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/accounts',
    name: 'Accounts',
    component: () => import('@/views/Accounts.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/budgets',
    name: 'Budgets',
    component: () => import('@/views/Budgets.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/exchange-rates',
    name: 'ExchangeRates',
    component: () => import('@/views/ExchangeRates.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test-chart',
    name: 'TestChart',
    component: () => import('@/views/TestChart.vue')
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
