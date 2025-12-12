<template>
  <div class="container">
    <div class="card" style="max-width: 450px; margin: 100px auto;">
      <div style="text-align: center; margin-bottom: 30px;">
        <h2 style="margin: 0 0 10px 0; color: #00d4ff; display: flex; align-items: center; gap: 8px; justify-content: center;">
          <span class="material-icons" style="font-size: 28px;">lock</span>
          忘記密碼
        </h2>
        <p style="color: #a0aec0; margin: 0; font-size: 14px;">
          輸入您的註冊郵箱，我們將發送密碼重設連結給您
        </p>
      </div>

      <form @submit.prevent="handleSubmit" v-if="!emailSent">
        <div class="form-group">
          <label for="email">電子郵件</label>
          <input
            type="email"
            id="email"
            v-model="email"
            placeholder="請輸入註冊時使用的郵箱"
            required
            :disabled="loading"
          />
        </div>

        <!-- Cloudflare Turnstile -->
        <div class="turnstile-container">
          <div ref="turnstileContainer"></div>
        </div>

        <button
          type="submit"
          class="btn btn-primary"
          style="width: 100%; margin-top: 20px;"
          :disabled="loading || !email || !turnstileToken"
        >
          {{ loading ? '發送中...' : '發送重設連結' }}
        </button>
      </form>

      <!-- 成功訊息 -->
      <div v-if="emailSent" style="text-align: center; padding: 20px;">
        <div style="margin-bottom: 20px;">
          <span class="material-icons" style="font-size: 60px; color: #51cf66;">mark_email_read</span>
        </div>
        <h3 style="color: #51cf66; margin: 0 0 15px 0;">郵件已發送！</h3>
        <p style="color: #a0aec0; margin: 0 0 20px 0; line-height: 1.6;">
          如果該郵箱已註冊，您將收到密碼重設郵件。<br>
          請檢查您的收件匣（也請查看垃圾郵件）。
        </p>
        <p style="color: #00d4ff; font-size: 12px; margin: 0 0 20px 0; display: flex; align-items: center; gap: 6px; justify-content: center;">
          <span class="material-icons" style="font-size: 16px;">info</span>
          連結將在 30 分鐘後失效
        </p>
        <button
          @click="resetForm"
          class="btn btn-secondary"
          style="width: 100%;"
        >
          重新發送
        </button>
      </div>

      <div style="margin-top: 25px; text-align: center; padding-top: 25px; border-top: 1px solid rgba(255,255,255,0.1);">
        <router-link
          to="/login"
          style="color: #00d4ff; text-decoration: none; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 5px;"
        >
          <span class="material-icons" style="font-size: 18px;">arrow_back</span>
          <span>返回登入</span>
        </router-link>
      </div>
    </div>

    <!-- 錯誤訊息 Modal -->
    <div v-if="showErrorModal" class="modal">
      <div class="modal-content">
        <h2 style="color: #ff6b6b; display: flex; align-items: center; gap: 8px; justify-content: center;">
          <span class="material-icons" style="font-size: 32px;">error</span>
          發送失敗
        </h2>
        <p style="margin: 20px 0; color: #a0aec0;">{{ errorMessage }}</p>
        <button @click="showErrorModal = false" class="btn btn-primary" style="width: 100%;">
          確定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import api from '@/services/api'

const email = ref('')
const emailSent = ref(false)
const loading = ref(false)
const showErrorModal = ref(false)
const errorMessage = ref('')

// Turnstile
const turnstileToken = ref('')
const siteKey = import.meta.env.VITE_TURNSTILE_SITE_KEY
const turnstileContainer = ref<HTMLElement | null>(null)
const widgetId = ref<string | null>(null)

const renderTurnstile = () => {
  if (window.turnstile && turnstileContainer.value) {
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

const resetForm = () => {
  emailSent.value = false
  email.value = ''
  turnstileToken.value = ''
  // Re-render Turnstile after DOM update
  setTimeout(() => {
    renderTurnstile()
  }, 100)
}

const handleSubmit = async () => {
  if (!turnstileToken.value) return

  loading.value = true
  try {
    await api.requestPasswordReset(email.value, turnstileToken.value)
    emailSent.value = true
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      errorMessage.value = detail
    } else if (Array.isArray(detail)) {
      errorMessage.value = detail.map((e: any) => e.msg).join('\n')
    } else {
      errorMessage.value = '發送失敗，請稍後再試'
    }
    showErrorModal.value = true
    
    // Reset Turnstile on error
    if (window.turnstile) {
      window.turnstile.reset()
      turnstileToken.value = ''
    }
  } finally {
    loading.value = false
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
.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
</style>
