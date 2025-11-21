import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import type { User, UserCreate, UserLogin } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  const isAuthenticated = computed(() => {
    return !!token.value && token.value !== 'null' && token.value !== 'undefined'
  })

  async function register(userData: UserCreate) {
    const response = await api.register(userData)
    return response.data
  }

  async function login(credentials: UserLogin) {
    const response = await api.login(credentials)
    // 只有在不需要 2FA 時才設定 token
    if (!response.data.requires_2fa) {
      token.value = response.data.access_token
      localStorage.setItem('token', token.value)
    }
    return response.data
  }

  function setToken(accessToken: string) {
    token.value = accessToken
    localStorage.setItem('token', accessToken)
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  return {
    user,
    token,
    isAuthenticated,
    register,
    login,
    setToken,
    logout
  }
})
