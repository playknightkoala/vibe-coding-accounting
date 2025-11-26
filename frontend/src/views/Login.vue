<template>
  <div class="container">
    <div class="content-wrapper">
      <!-- Login Form Section -->
      <div class="card login-card">
        <h2>登入</h2>
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="email">電子郵件</label>
            <input
              type="email"
              id="email"
              v-model="form.email"
              placeholder="example@email.com"
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
          
          <div style="margin-top: 20px; display: flex; align-items: center; gap: 10px;">
            <div style="flex: 1; height: 1px; background: rgba(255,255,255,0.1);"></div>
            <span style="color: #a0aec0; font-size: 14px;">或</span>
            <div style="flex: 1; height: 1px; background: rgba(255,255,255,0.1);"></div>
          </div>

          <a href="/api/login/google" class="btn btn-google" style="width: 100%; margin-top: 20px; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 10px;">
            <img src="https://www.svgrepo.com/show/475656/google-color.svg" alt="Google" style="width: 20px; height: 20px;">
            <span>使用 Google 帳號登入</span>
          </a>
        </form>
        <div style="margin-top: 15px; text-align: center;">
          <router-link
            to="/forgot-password"
            style="color: #00d4ff; text-decoration: none; font-size: 14px; opacity: 0.9; transition: opacity 0.3s ease;"
            @mouseover="(e) => e.target.style.opacity = '1'"
            @mouseleave="(e) => e.target.style.opacity = '0.9'"
          >
            忘記密碼？
          </router-link>
        </div>
        <p style="margin-top: 15px; text-align: center; color: #a0aec0;">
          還沒有帳號？ <router-link to="/register" style="color: #00d4ff; text-decoration: none; font-weight: 500;">註冊</router-link>
        </p>
      </div>

      <!-- About / Project Info Section -->
      <div class="about-section">
        <div class="about-content">
          <h1>關於本專案</h1>
          
          <section class="section">
            <h2>📊 專案簡介</h2>
            <p>
              這是一個功能完整的<strong>個人記帳與預算管理系統</strong>，旨在幫助使用者有效管理個人財務、追蹤支出、設定預算目標，並透過視覺化報表深入了解財務狀況。
            </p>
            <p>
              本專案是個人全端開發作品，展示了現代 Web 應用程式開發的完整流程，從前端介面設計到後端 API 開發，再到資料庫設計與部署。
            </p>
          </section>

          <section class="section">
            <h2>✨ 主要功能</h2>
            <ul>
              <li><strong>多幣別支援</strong>：支援 TWD、USD、JPY 等多種貨幣，並提供即時匯率轉換</li>
              <li><strong>交易管理</strong>：快速記帳、交易分類、描述自動完成（支援拼音搜尋）</li>
              <li><strong>預算追蹤</strong>：設定月度/日度預算，即時追蹤預算使用狀況</li>
              <li><strong>報表分析</strong>：多維度財務報表，包含類別分析、帳戶分析、排名統計等</li>
              <li><strong>帳戶管理</strong>：支援現金、銀行、信用卡、儲值卡等多種帳戶類型</li>
              <li><strong>安全性</strong>：使用者認證、JWT Token、2FA 雙因素驗證</li>
            </ul>
          </section>

          <section class="section">
            <h2>🛠️ 技術堆疊</h2>
            <div class="tech-stack">
              <div class="tech-category">
                <h3>前端</h3>
                <ul>
                  <li>Vue 3 (Composition API)</li>
                  <li>TypeScript</li>
                  <li>Pinia (狀態管理)</li>
                  <li>Vue Router</li>
                  <li>Axios</li>
                </ul>
              </div>
              <div class="tech-category">
                <h3>後端</h3>
                <ul>
                  <li>Python FastAPI</li>
                  <li>SQLAlchemy (ORM)</li>
                  <li>PostgreSQL</li>
                  <li>JWT Authentication</li>
                  <li>APScheduler (排程任務)</li>
                </ul>
              </div>
              <div class="tech-category">
                <h3>部署</h3>
                <ul>
                  <li>Docker & Docker Compose</li>
                  <li>Nginx (反向代理)</li>
                  <li>SSL/TLS (HTTPS)</li>
                </ul>
              </div>
            </div>
          </section>

          <section class="section">
            <h2>👨‍💻 開發者</h2>
            <p>
              <strong>YS Hong</strong> - 全端工程師
            </p>
            <p>
              這個專案是我的個人作品集之一，展示了我在全端開發、系統架構設計、以及現代 Web 技術應用方面的能力。
            </p>
          </section>

          <div class="footer-note">
            <p>© 2025 YS Hong. 本專案為個人作品，僅供展示與學習用途。</p>
          </div>
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
  email: '',
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
      await router.push('/dashboard')
    }
  } catch (err: any) {
    // 登入失敗，確保清除任何舊的 token
    authStore.logout()

    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      errorMessage.value = detail
    } else {
      errorMessage.value = '登入失敗，請檢查您的電子郵件和密碼'
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
    router.push('/dashboard')
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
    email: '',
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

.content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 40px;
  width: 100%;
  max-width: 900px; /* Adjusted to match original About page width for better readability */
  align-items: center;
}

/* Login Card Styles */
.card {
  background: rgba(255, 255, 255, 0.05);
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  /* Removed max-width: 400px to let it expand */
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
}

.login-card h2 {
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

.btn-google {
  background: #fff;
  color: #333;
  border: 1px solid #ddd;
  transition: all 0.3s ease;
}

.btn-google:hover {
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* About Section Styles */
.about-section {
  width: 100%;
  animation: fadeIn 0.8s ease-out;
}

.about-content {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.about-content h1 {
  color: #00d4ff;
  font-size: 2rem;
  margin-bottom: 30px;
  text-align: center;
}

.section {
  margin-bottom: 30px;
}

.section h2 {
  color: #00d4ff;
  font-size: 1.5rem;
  margin-bottom: 15px;
  border-bottom: 2px solid rgba(0, 212, 255, 0.3);
  padding-bottom: 10px;
}

.section h3 {
  color: #4ecdc4;
  font-size: 1.2rem;
  margin-bottom: 10px;
}

.section p {
  color: #e0e0e0;
  line-height: 1.6;
  margin-bottom: 15px;
}

.section ul {
  color: #e0e0e0;
  line-height: 1.6;
  padding-left: 20px;
}

.section li {
  margin-bottom: 8px;
}

.section strong {
  color: #00d4ff;
}

.tech-stack {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.tech-category {
  background: rgba(0, 212, 255, 0.05);
  padding: 20px;
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.tech-category ul {
  padding-left: 20px;
  margin: 0;
}

.footer-note {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  color: #a0a0a0;
  font-size: 0.9rem;
}

/* Modal Styles */
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

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsive Design */
@media (max-width: 768px) {
  .content-wrapper {
    padding: 20px;
  }
  
  .card, .about-content {
    padding: 20px;
  }
}
</style>
