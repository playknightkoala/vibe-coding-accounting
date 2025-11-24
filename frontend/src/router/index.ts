import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Dashboard from '@/views/Dashboard.vue'
import Accounts from '@/views/Accounts.vue'

import Budgets from '@/views/Budgets.vue'
import Profile from '@/views/Profile.vue'
import Reports from '@/views/Reports.vue'
import TestChart from '@/views/TestChart.vue'
import About from '@/views/About.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
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
    path: '/about',
    name: 'About',
    component: About,
    meta: { public: true }
  },
  {
    path: '/',
    redirect: '/dashboard'
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
    path: '/test-chart',
    name: 'TestChart',
    component: TestChart
  },
  // Catch-all route for 404 - must be last
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: (to) => {
      // This will be handled by beforeEach guard
      return { path: to.path }
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated

  // Public pages that don't require authentication
  const publicPages = ['/login', '/register', '/about']
  const isPublicPage = publicPages.includes(to.path)

  // Check if route exists (not a 404)
  const routeExists = router.hasRoute(to.name || '')

  // Handle 404 / invalid routes
  if (to.name === 'NotFound' || !routeExists) {
    if (isAuthenticated) {
      // Has valid token but invalid route -> redirect to dashboard
      next('/dashboard')
    } else {
      // No valid token and invalid route -> redirect to login
      next('/login')
    }
    return
  }

  // Handle public pages
  if (isPublicPage) {
    if (to.path === '/login' || to.path === '/register') {
      // If already authenticated, redirect to dashboard
      if (isAuthenticated) {
        next('/dashboard')
      } else {
        next()
      }
    } else {
      // About page - always allow
      next()
    }
    return
  }

  // Handle protected pages
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      // Not authenticated, redirect to login
      next('/login')
    } else {
      // Authenticated, allow access
      next()
    }
    return
  }

  // Default: allow navigation
  next()
})

export default router
