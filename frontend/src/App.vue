<template>
  <div id="app">
    <nav v-if="isAuthenticated" class="navbar">
      <div class="navbar-content">
        <div>
          <router-link to="/">儀表板</router-link>
          <router-link to="/accounts">帳戶</router-link>
          <router-link to="/transactions">交易</router-link>
          <router-link to="/budgets">預算</router-link>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
          <router-link to="/profile">個人設定</router-link>
          <button @click="handleLogout" class="btn btn-secondary">登出</button>
        </div>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const isAuthenticated = computed(() => authStore.isAuthenticated)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
