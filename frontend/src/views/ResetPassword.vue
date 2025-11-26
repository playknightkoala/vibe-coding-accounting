<template>
  <div class="container">
    <div class="card" style="max-width: 500px; margin: 100px auto;">
      <!-- 驗證中 -->
      <div v-if="verifying" style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 50px; margin-bottom: 20px;">⏳</div>
        <p style="color: #a0aec0;">驗證連結有效性...</p>
      </div>

      <!-- 連結無效 -->
      <div v-else-if="!isValidToken" style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 60px; margin-bottom: 20px;">❌</div>
        <h2 style="color: #ff6b6b; margin: 0 0 15px 0;">連結無效或已過期</h2>
        <p style="color: #a0aec0; margin: 0 0 30px 0; line-height: 1.6;">
          {{ tokenMessage }}
        </p>
        <router-link to="/forgot-password">
          <button class="btn btn-primary" style="width: 100%;">
            重新申請重設連結
          </button>
        </router-link>
      </div>

      <!-- 重設密碼表單 -->
      <div v-else-if="!resetSuccess">
        <div style="text-align: center; margin-bottom: 30px;">
          <h2 style="margin: 0 0 10px 0; color: #00d4ff;">🔑 重設密碼</h2>
          <p style="color: #a0aec0; margin: 0; font-size: 14px;">
            請設定您的新密碼
          </p>
        </div>

        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="password">新密碼</label>
            <input
              type="password"
              id="password"
              v-model="form.password"
              @input="validatePassword"
              required
              :disabled="loading"
            />
            <div style="margin-top: 12px;">
              <p style="font-size: 12px; margin-bottom: 6px; color: #a0aec0;">密碼要求：</p>
              <p :style="{ fontSize: '12px', color: passwordRules.length ? '#51cf66' : '#ff6b6b', marginBottom: '4px' }">
                {{ passwordRules.length ? '✓' : '✗' }} 至少 8 個字元
              </p>
              <p :style="{ fontSize: '12px', color: passwordRules.uppercase ? '#51cf66' : '#ff6b6b', marginBottom: '4px' }">
                {{ passwordRules.uppercase ? '✓' : '✗' }} 至少 1 個大寫字母
              </p>
              <p :style="{ fontSize: '12px', color: passwordRules.lowercase ? '#51cf66' : '#ff6b6b', marginBottom: '4px' }">
                {{ passwordRules.lowercase ? '✓' : '✗' }} 至少 1 個小寫字母
              </p>
              <p :style="{ fontSize: '12px', color: passwordRules.number ? '#51cf66' : '#ff6b6b', marginBottom: '4px' }">
                {{ passwordRules.number ? '✓' : '✗' }} 至少 1 個數字
              </p>
              <p :style="{ fontSize: '12px', color: passwordRules.special ? '#51cf66' : '#ff6b6b', marginBottom: '4px' }">
                {{ passwordRules.special ? '✓' : '✗' }} 至少 1 個特殊字元 (!@#$%^&*(),.?":{}|&lt;&gt;)
              </p>
            </div>
          </div>

          <div class="form-group">
            <label for="confirmPassword">確認新密碼</label>
            <input
              type="password"
              id="confirmPassword"
              v-model="form.confirmPassword"
              required
              :disabled="loading"
            />
            <p v-if="form.confirmPassword && form.password !== form.confirmPassword"
               style="margin-top: 5px; font-size: 12px; color: #ff6b6b;">
              密碼不一致
            </p>
          </div>

          <button
            type="submit"
            class="btn btn-primary"
            style="width: 100%; margin-top: 25px;"
            :disabled="!isFormValid || loading"
          >
            {{ loading ? '處理中...' : '確認重設密碼' }}
          </button>
        </form>
      </div>

      <!-- 重設成功 -->
      <div v-else style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 70px; margin-bottom: 25px;">✅</div>
        <h2 style="color: #51cf66; margin: 0 0 15px 0;">密碼重設成功！</h2>
        <p style="color: #a0aec0; margin: 0 0 30px 0; line-height: 1.6;">
          您的密碼已成功更新，現在可以使用新密碼登入了。
        </p>
        <router-link to="/login">
          <button class="btn btn-primary" style="width: 100%;">
            前往登入
          </button>
        </router-link>
      </div>
    </div>

    <!-- 錯誤訊息 Modal -->
    <div v-if="showErrorModal" class="modal">
      <div class="modal-content">
        <h2 style="color: #ff6b6b;">❌ 重設失敗</h2>
        <p style="margin: 20px 0; color: #a0aec0; white-space: pre-line;">{{ errorMessage }}</p>
        <button @click="showErrorModal = false" class="btn btn-primary" style="width: 100%;">
          確定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()

const token = ref('')
const verifying = ref(true)
const isValidToken = ref(false)
const tokenMessage = ref('')
const resetSuccess = ref(false)
const loading = ref(false)
const showErrorModal = ref(false)
const errorMessage = ref('')

const form = ref({
  password: '',
  confirmPassword: ''
})

const passwordRules = ref({
  length: false,
  uppercase: false,
  lowercase: false,
  number: false,
  special: false
})

const validatePassword = () => {
  const password = form.value.password
  passwordRules.value = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
  }
}

const isFormValid = computed(() => {
  return (
    passwordRules.value.length &&
    passwordRules.value.uppercase &&
    passwordRules.value.lowercase &&
    passwordRules.value.number &&
    passwordRules.value.special &&
    form.value.password === form.value.confirmPassword
  )
})

const verifyToken = async () => {
  try {
    const response = await api.verifyResetToken(token.value)
    isValidToken.value = response.data.valid
    tokenMessage.value = response.data.message
  } catch (err) {
    isValidToken.value = false
    tokenMessage.value = '無法驗證連結，請重新申請'
  } finally {
    verifying.value = false
  }
}

const handleSubmit = async () => {
  if (!isFormValid.value) return

  loading.value = true
  try {
    await api.confirmPasswordReset(token.value, form.value.password)
    resetSuccess.value = true
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      errorMessage.value = detail
    } else if (Array.isArray(detail)) {
      errorMessage.value = detail.map((e: any) => e.msg).join('\n')
    } else {
      errorMessage.value = '重設失敗，請稍後再試'
    }
    showErrorModal.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 從 URL query 取得 token
  token.value = route.query.token as string

  if (!token.value) {
    isValidToken.value = false
    tokenMessage.value = '缺少重設連結 token'
    verifying.value = false
    return
  }

  verifyToken()
})
</script>
