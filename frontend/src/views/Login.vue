<template>
  <div class="container">
    <div class="card" style="max-width: 400px; margin: 100px auto;">
      <h2>登入</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">使用者名稱</label>
          <input
            type="text"
            id="username"
            v-model="form.username"
            required
          />
        </div>
        <div class="form-group">
          <label for="password">密碼</label>
          <input
            type="password"
            id="password"
            v-model="form.password"
            required
          />
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 10px;">
          登入
        </button>
      </form>
      <p style="margin-top: 20px; text-align: center; color: #a0aec0;">
        還沒有帳號？ <router-link to="/register" style="color: #00d4ff; text-decoration: none; font-weight: 500; transition: all 0.3s ease;">註冊</router-link>
      </p>
    </div>

    <!-- 2FA 驗證彈窗 -->
    <div v-if="show2FAModal" class="modal">
      <div class="modal-content">
        <h2 style="color: #00d4ff;">雙因素驗證</h2>
        <p style="margin: 15px 0; color: #a0aec0;">請輸入驗證器應用程式中的 6 位數驗證碼</p>
        <div class="form-group">
          <label for="2fa_code">驗證碼</label>
          <input
            type="text"
            id="2fa_code"
            v-model="twoFactorCode"
            placeholder="000000"
            maxlength="6"
            pattern="[0-9]{6}"
            required
            autofocus
          />
        </div>
        <div style="display: flex; gap: 10px; margin-top: 20px;">
          <button @click="verify2FA" class="btn btn-primary" style="flex: 1;">
            驗證
          </button>
          <button @click="cancel2FA" class="btn btn-secondary" style="flex: 1;">
            取消
          </button>
        </div>
      </div>
    </div>

    <!-- 登入失敗彈窗 -->
    <div v-if="showErrorModal" class="modal">
      <div class="modal-content">
        <h2 style="color: #ff6b6b;">登入失敗</h2>
        <p style="margin: 20px 0; color: #a0aec0;">{{ errorMessage }}</p>
        <button @click="showErrorModal = false" class="btn btn-primary" style="width: 100%;">
          確定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  username: '',
  password: ''
})

const show2FAModal = ref(false)
const showErrorModal = ref(false)
const errorMessage = ref('')
const twoFactorCode = ref('')

const handleLogin = async () => {
  try {
    const response = await authStore.login(form.value)

    // 檢查是否需要 2FA
    if (response && response.requires_2fa) {
      show2FAModal.value = true
    } else {
      // 登入成功，導向首頁
      await router.push('/')
    }
  } catch (err: any) {
    // 登入失敗，確保清除任何舊的 token
    authStore.logout()

    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      errorMessage.value = detail
    } else {
      errorMessage.value = '登入失敗，請檢查您的使用者名稱和密碼'
    }
    showErrorModal.value = true
  }
}

const verify2FA = async () => {
  if (twoFactorCode.value.length !== 6) {
    errorMessage.value = '請輸入 6 位數驗證碼'
    showErrorModal.value = true
    return
  }

  try {
    const response = await api.verify2FA(form.value, twoFactorCode.value)
    // 設定 token
    authStore.setToken(response.data.access_token)
    show2FAModal.value = false
    router.push('/')
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      errorMessage.value = detail
    } else {
      errorMessage.value = '驗證碼錯誤，請重試'
    }
    showErrorModal.value = true
    twoFactorCode.value = ''
  }
}

const cancel2FA = () => {
  show2FAModal.value = false
  twoFactorCode.value = ''
  form.value = {
    username: '',
    password: ''
  }
}
</script>
