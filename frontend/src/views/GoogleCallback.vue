<template>
  <div class="callback-container">
    <div class="loading-spinner"></div>
    <p>正在登入中...</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

onMounted(async () => {
  const token = route.query.token as string
  
  if (token) {
    try {
      // Store token
      authStore.setToken(token)
      
      // Redirect to dashboard
      await router.push('/dashboard')
    } catch (error) {
      console.error('Login failed:', error)
      await router.push('/login?error=google_login_failed')
    }
  } else {
    await router.push('/login?error=no_token')
  }
})
</script>

<style scoped>
.callback-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: #1a1a2e;
  color: #fff;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #00d4ff;
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
