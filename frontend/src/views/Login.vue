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
        還沒有帳號？ <router-link to="/register" style="color: #00d4ff; text-decoration: none; font-weight: 500;">註冊</router-link>
      </p>
      <p style="margin-top: 10px; text-align: center; color: #a0aec0;">
        <router-link to="/about" style="color: #4ecdc4; text-decoration: none; font-weight: 500;">關於本系統</router-link>
      </p>
    </div>

    <!-- FortiGuard / Project Info Section -->
    <div class="project-info">
      <div class="info-card">
        <h3>關於本專案</h3>
        <p>
          本網站為 <strong>個人作品集 (Portfolio Project)</strong>，旨在展示全端開發技術。
        </p>
        <div class="disclaimer">
          <span class="icon">⚠️</span>
          <span>
            <strong>非真實金融服務</strong>：本系統僅供展示用途，請勿輸入真實的銀行帳號、密碼或任何敏感個人資訊。
          </span>
        </div>
        <div class="developer-info">
          <p>開發者: YS Hong</p>
          <router-link to="/about" class="more-link">了解更多專案細節 &rarr;</router-link>
        </div>
      </div>
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

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.card {
  background: rgba(255, 255, 255, 0.05);
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
}

h2 {
  color: #00d4ff;
  text-align: center;
  margin-bottom: 30px;
  font-size: 2rem;
  font-weight: 600;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #a0aec0;
  font-size: 0.9rem;
}

input {
  width: 100%;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s ease;
}

input:focus {
  outline: none;
  border-color: #00d4ff;
  box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
}

.btn {
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #00d4ff 0%, #00b4d8 100%);
  color: #1a1a2e;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: #1a1a2e;
  padding: 30px;
  border-radius: 16px;
  width: 90%;
  max-width: 400px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
}

/* Project Info Section Styles */
.project-info {
  width: 100%;
  max-width: 600px; /* Wider than the login card for better readability */
  margin-top: 40px;
  animation: fadeIn 0.8s ease-out;
}

.info-card {
  background: rgba(0, 212, 255, 0.03);
  border: 1px solid rgba(0, 212, 255, 0.1);
  border-radius: 12px;
  padding: 25px;
  text-align: center;
}

.info-card h3 {
  color: #4ecdc4;
  font-size: 1.2rem;
  margin-bottom: 15px;
  font-weight: 600;
}

.info-card p {
  color: #a0aec0;
  line-height: 1.6;
  margin-bottom: 15px;
  font-size: 0.95rem;
}

.disclaimer {
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin: 20px 0;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  text-align: left;
}

.disclaimer .icon {
  font-size: 1.2rem;
}

.disclaimer span {
  color: #ffcccc;
  font-size: 0.9rem;
  line-height: 1.5;
}

.disclaimer strong {
  color: #ff6b6b;
}

.developer-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 15px;
}

.more-link {
  color: #00d4ff;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.more-link:hover {
  color: #4ecdc4;
  text-decoration: underline;
  transform: translateX(5px);
  display: inline-block;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsive Design */
@media (min-width: 1024px) {
  .container {
    flex-direction: row;
    gap: 60px;
    align-items: center;
  }

  .card {
    margin: 0 !important; /* Override inline style */
    flex: 0 0 400px;
  }

  .project-info {
    margin-top: 0;
    flex: 0 0 500px;
    text-align: left;
  }

  .info-card {
    text-align: left;
    padding: 40px;
  }
  
  .developer-info {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
