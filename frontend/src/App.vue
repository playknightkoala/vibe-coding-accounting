<template>
  <div id="app">
    <nav v-if="isAuthenticated" class="navbar">
      <div class="navbar-content">
        <!-- Logo (Desktop Only) -->
        <div class="navbar-logo">
          <img src="/LOGO.webp" alt="Logo" class="logo-image" width="120" height="120" fetchpriority="high">
        </div>

        <!-- Hamburger Menu Button (Mobile Only) -->
        <button class="navbar-toggle" @click="toggleMenu" :class="{ active: isMenuOpen }">
          <span></span>
          <span></span>
          <span></span>
        </button>

        <!-- Navigation Links -->
        <div class="navbar-menu" :class="{ active: isMenuOpen }">
          <div class="navbar-links">
            <router-link to="/dashboard" @click="closeMenu">儀表板</router-link>
            <router-link to="/accounts" @click="closeMenu">帳戶</router-link>
            <router-link to="/budgets" @click="closeMenu">預算</router-link>
            <router-link to="/reports" @click="closeMenu">報表</router-link>
            <router-link to="/exchange-rates" @click="closeMenu">匯率</router-link>
          </div>
          <div class="navbar-actions">
            <router-link v-if="isAdmin" to="/admin" @click="closeMenu">管理員</router-link>
            <router-link to="/profile" @click="closeMenu">個人設定</router-link>
            <button @click="handleLogout" class="btn btn-secondary">登出</button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Route Loading Spinner -->
    <LoadingSpinner :show="isRouteLoading" text="載入中..." />

    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const authStore = useAuthStore()
const router = useRouter()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const isAdmin = computed(() => authStore.user?.is_admin || false)
const isMenuOpen = ref(false)
const isRouteLoading = ref(false)

let loadingTimer: number | null = null

// Track route changes for loading state
router.beforeEach(() => {
  // Show loading after 150ms to avoid flash for fast transitions
  loadingTimer = window.setTimeout(() => {
    isRouteLoading.value = true
  }, 150)
})

router.afterEach(() => {
  // Clear timer and hide loading
  if (loadingTimer) {
    clearTimeout(loadingTimer)
    loadingTimer = null
  }
  isRouteLoading.value = false
})

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}

const handleLogout = () => {
  closeMenu()
  authStore.logout()
  router.push('/')
}

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    try {
      await authStore.fetchUser()
    } catch (error) {
      console.error('Failed to restore user session:', error)
    }
  }
})
</script>

<style scoped>
/* Navbar Logo */
.navbar-logo {
  display: flex;
  align-items: center;
  margin-right: 20px;
}

.logo-image {
  height: 40px;
  width: auto;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.logo-image:hover {
  transform: scale(1.05);
}

/* Hamburger Menu Button */
.navbar-toggle {
  display: none;
  flex-direction: column;
  justify-content: space-around;
  width: 30px;
  height: 24px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  z-index: 1001;
}

.navbar-toggle span {
  width: 100%;
  height: 3px;
  background: #00d4ff;
  border-radius: 3px;
  transition: all 0.3s ease;
}

.navbar-toggle.active span:nth-child(1) {
  transform: rotate(45deg) translate(5px, 5px);
}

.navbar-toggle.active span:nth-child(2) {
  opacity: 0;
}

.navbar-toggle.active span:nth-child(3) {
  transform: rotate(-45deg) translate(7px, -6px);
}

/* Desktop Navigation */
.navbar-menu {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
  gap: 20px;
}

.navbar-links {
  display: flex;
  gap: 10px;
  align-items: center;
}

.navbar-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* Mobile Styles */
@media (max-width: 768px) {
  .navbar-content {
    justify-content: space-between;
  }

  .navbar-logo {
    margin-right: 0;
  }

  .logo-image {
    height: 35px;
  }

  .navbar-toggle {
    display: flex;
  }

  .navbar-menu {
    position: fixed;
    top: 60px;
    left: 0;
    right: 0;
    background: linear-gradient(135deg, rgba(10, 14, 39, 0.98) 0%, rgba(26, 31, 58, 0.98) 100%);
    backdrop-filter: blur(10px);
    flex-direction: column;
    padding: 20px;
    gap: 0;
    max-height: 0;
    overflow: hidden;
    opacity: 0;
    transition: all 0.3s ease;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  }

  .navbar-menu.active {
    max-height: 500px;
    opacity: 1;
  }

  .navbar-links,
  .navbar-actions {
    flex-direction: column;
    width: 100%;
    gap: 0;
  }

  .navbar-links {
    border-bottom: 1px solid rgba(0, 212, 255, 0.1);
    padding-bottom: 15px;
    margin-bottom: 15px;
  }

  .navbar-menu a,
  .navbar-menu button {
    width: 100%;
    text-align: left;
    padding: 12px 15px;
    margin: 0 !important;
    border-radius: 5px;
    transition: background 0.3s ease;
  }

  .navbar-menu a:hover {
    background: rgba(0, 212, 255, 0.1);
  }

  .navbar-menu a::after {
    display: none;
  }

  .navbar-menu button {
    margin-top: 10px !important;
    justify-content: center;
  }
}

/* Prevent body scroll when menu is open */
@media (max-width: 768px) {
  body:has(.navbar-menu.active) {
    overflow: hidden;
  }
}

/* Route transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

