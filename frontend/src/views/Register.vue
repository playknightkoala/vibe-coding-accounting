<template>
  <div class="container">
    <main>
      <section class="card" style="max-width: 400px; margin: 100px auto;" aria-labelledby="register-heading">
        <div class="logo-container">
          <img src="/FullLOGO.webp" alt="會計與預算系統標誌" class="full-logo" width="250" height="232" fetchpriority="high">
        </div>
        <h1 id="register-heading" style="color: #00d4ff; font-size: 24px; margin-bottom: 20px;">註冊</h1>
        <form @submit.prevent="handleRegister" aria-label="註冊表單">
        <div class="form-group">
          <label for="email">電子郵件</label>
          <input
            type="email"
            id="email"
            v-model="form.email"
            @blur="validateEmail"
            placeholder="example@email.com"
            required
          />
          <p v-if="emailError" style="margin-top: 5px; font-size: 12px; color: #ff6b6b;">
            {{ emailError }}
          </p>
        </div>
        <div class="form-group">
          <label for="password">密碼</label>
          <input
            type="password"
            id="password"
            v-model="form.password"
            @input="validatePassword"
            required
          />
          <div style="margin-top: 8px;">
            <p style="font-size: 12px; margin-bottom: 5px; color: #a0aec0;">密碼要求：</p>
            <p :style="{ fontSize: '12px', color: passwordRules.length ? '#51cf66' : '#ff6b6b', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px' }">
              <span class="material-icons" style="font-size: 16px;">{{ passwordRules.length ? 'check_circle' : 'cancel' }}</span>
              至少 8 個字元
            </p>
            <p :style="{ fontSize: '12px', color: passwordRules.uppercase ? '#51cf66' : '#ff6b6b', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px' }">
              <span class="material-icons" style="font-size: 16px;">{{ passwordRules.uppercase ? 'check_circle' : 'cancel' }}</span>
              至少 1 個大寫字母
            </p>
            <p :style="{ fontSize: '12px', color: passwordRules.lowercase ? '#51cf66' : '#ff6b6b', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px' }">
              <span class="material-icons" style="font-size: 16px;">{{ passwordRules.lowercase ? 'check_circle' : 'cancel' }}</span>
              至少 1 個小寫字母
            </p>
            <p :style="{ fontSize: '12px', color: passwordRules.number ? '#51cf66' : '#ff6b6b', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px' }">
              <span class="material-icons" style="font-size: 16px;">{{ passwordRules.number ? 'check_circle' : 'cancel' }}</span>
              至少 1 個數字
            </p>
            <p :style="{ fontSize: '12px', color: passwordRules.special ? '#51cf66' : '#ff6b6b', marginBottom: '3px', display: 'flex', alignItems: 'center', gap: '4px' }">
              <span class="material-icons" style="font-size: 16px;">{{ passwordRules.special ? 'check_circle' : 'cancel' }}</span>
              至少 1 個特殊字元 (!@#$%^&*(),.?":{}|&lt;&gt;)
            </p>
          </div>
        </div>
        
        <!-- Cloudflare Turnstile -->
        <!-- Cloudflare Turnstile -->
        <div class="turnstile-container">
          <div ref="turnstileContainer"></div>
        </div>

        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 10px;" :disabled="!isFormValid">
          註冊
        </button>
      </form>
      <p style="margin-top: 20px; text-align: center; color: #a0aec0;">
        已經有帳號了？ <router-link to="/login" style="color: #00d4ff; text-decoration: none; font-weight: 500; transition: all 0.3s ease;">登入</router-link>
      </p>
      <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255, 255, 255, 0.1); text-align: center;">
        <p style="font-size: 12px; color: #a0aec0; margin-bottom: 8px;">
          點擊註冊即表示您同意我們的
        </p>
        <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
          <router-link to="/terms" style="color: #00d4ff; text-decoration: none; font-size: 12px; opacity: 0.9; transition: opacity 0.3s ease;">
            服務條款
          </router-link>
          <span style="color: #a0aec0; font-size: 12px;">·</span>
          <router-link to="/privacy" style="color: #00d4ff; text-decoration: none; font-size: 12px; opacity: 0.9; transition: opacity 0.3s ease;">
            隱私權政策
          </router-link>
        </div>
      </div>
      </section>
    </main>

    <div v-if="showSuccessModal" class="modal" role="dialog" aria-labelledby="success-modal-title">
      <div class="modal-content">
        <h2 id="success-modal-title" style="color: #51cf66;">註冊成功！</h2>
        <p style="margin: 20px 0; color: #a0aec0;">您的帳號已經成功建立，點擊下方按鈕前往登入頁面。</p>
        <button @click="goToLogin" class="btn btn-primary" style="width: 100%;">
          前往登入
        </button>
      </div>
    </div>

    <div v-if="showErrorModal" class="modal" role="dialog" aria-labelledby="error-modal-title">
      <div class="modal-content">
        <h2 id="error-modal-title" style="color: #ff6b6b;">註冊失敗</h2>
        <p style="margin: 20px 0; color: #a0aec0;">{{ errorMessage }}</p>
        <button @click="showErrorModal = false" class="btn btn-primary" style="width: 100%;">
          確定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: ''
})

const emailError = ref('')
const showSuccessModal = ref(false)
const showErrorModal = ref(false)
const errorMessage = ref('')

const passwordRules = ref({
  length: false,
  uppercase: false,
  lowercase: false,
  number: false,
  special: false
})

const turnstileToken = ref('')
const siteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY

const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.value.email) {
    emailError.value = '請輸入電子郵件'
    return false
  }
  if (!emailRegex.test(form.value.email)) {
    emailError.value = '請輸入有效的電子郵件格式'
    return false
  }
  emailError.value = ''
  return true
}

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
  return form.value.email.length > 0 &&
    emailError.value === '' &&
    passwordRules.value.length &&
    passwordRules.value.uppercase &&
    passwordRules.value.lowercase &&
    passwordRules.value.number &&
    passwordRules.value.special &&
    turnstileToken.value !== ''
})

const handleRegister = async () => {
  if (!validateEmail()) {
    return
  }

  if (!isFormValid.value) {
    errorMessage.value = '請確保所有密碼要求都已滿足且完成驗證'
    showErrorModal.value = true
    return
  }

  try {
    await authStore.register({
      ...form.value,
      turnstile_token: turnstileToken.value
    })
    showSuccessModal.value = true
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      errorMessage.value = detail
    } else if (Array.isArray(detail)) {
      errorMessage.value = detail.map((e: any) => e.msg).join('\n')
    } else {
      errorMessage.value = '註冊失敗，請稍後再試'
    }
    showErrorModal.value = true
    // 重置 Turnstile
    if (window.turnstile) {
      window.turnstile.reset()
      turnstileToken.value = ''
    }
  }
}

const goToLogin = () => {
  router.push('/login')
}

// Load Turnstile script
// Load Turnstile script
import { onMounted, onBeforeUnmount } from 'vue'

const turnstileContainer = ref<HTMLElement | null>(null)
const widgetId = ref<string | null>(null)

const renderTurnstile = () => {
  if (window.turnstile && turnstileContainer.value) {
    // 如果已經有 widget，先移除
    if (widgetId.value) {
      window.turnstile.remove(widgetId.value)
    }
    
    widgetId.value = window.turnstile.render(turnstileContainer.value, {
      sitekey: siteKey,
      callback: (token: string) => {
        turnstileToken.value = token
      },
      'expired-callback': () => {
        turnstileToken.value = ''
      }
    })
  }
}

onMounted(() => {
  if (window.turnstile) {
    renderTurnstile()
  } else {
    const script = document.createElement('script')
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
    script.async = true
    script.defer = true
    script.onload = renderTurnstile
    document.head.appendChild(script)
  }
})

onBeforeUnmount(() => {
  if (window.turnstile && widgetId.value) {
    window.turnstile.remove(widgetId.value)
  }
})
</script>

<style scoped>
.logo-container {
  text-align: center;
  margin-bottom: 30px;
}

.full-logo {
  max-width: 250px;
  width: 100%;
  height: auto;
}

/* Add styles for Turnstile container if needed */
.turnstile-container {
  margin: 20px 0;
  display: flex;
  justify-content: center;
}
</style>
