<template>
  <div class="container">
    <h1>個人設定</h1>

    <!-- 使用者資訊 -->
    <div class="card">
      <h2>帳戶資訊</h2>
      <p><strong>使用者名稱：</strong>{{ user?.username }}</p>
      <p><strong>2FA 狀態：</strong>{{ user?.two_factor_enabled ? '已啟用' : '未啟用' }}</p>
    </div>

    <!-- 變更密碼 -->
    <div class="card">
      <h2>變更密碼</h2>
      <form @submit.prevent="handlePasswordChange">
        <div class="form-group">
          <label for="current_password">目前密碼</label>
          <input
            type="password"
            id="current_password"
            v-model="passwordForm.current_password"
            required
          />
        </div>
        <div class="form-group">
          <label for="new_password">新密碼</label>
          <input
            type="password"
            id="new_password"
            v-model="passwordForm.new_password"
            required
          />
          <p style="margin-top: 5px; font-size: 12px; color: #a0aec0;">
            密碼需包含：至少 8 個字元、1 個大寫字母、1 個小寫字母、1 個數字、1 個特殊字元
          </p>
        </div>
        <div v-if="passwordError" class="error">{{ passwordError }}</div>
        <div v-if="passwordSuccess" class="success">{{ passwordSuccess }}</div>
        <button type="submit" class="btn btn-primary">更新密碼</button>
      </form>
    </div>

    <!-- 2FA 設定 -->
    <div class="card">
      <h2>雙因素認證 (2FA)</h2>
      <p style="margin-bottom: 15px; color: #a0aec0;">
        使用手機驗證器應用程式（如 Google Authenticator、Microsoft Authenticator）來增加帳戶安全性
      </p>

      <!-- 尚未啟用 2FA -->
      <div v-if="!user?.two_factor_enabled && !showSetup2FA">
        <button @click="start2FASetup" class="btn btn-primary">啟用 2FA</button>
      </div>

      <!-- 設定 2FA -->
      <div v-if="showSetup2FA && qrCode">
        <h3 style="margin-bottom: 15px;">步驟 1: 掃描 QR Code</h3>
        <img :src="qrCode" alt="QR Code" style="max-width: 250px; margin-bottom: 15px; border-radius: 8px;" />
        <p style="margin-bottom: 10px; color: #a0aec0;">或手動輸入此密鑰：</p>
        <p style="margin-bottom: 20px; font-family: monospace; background: rgba(0, 212, 255, 0.1); padding: 10px; border-radius: 4px; word-break: break-all;">{{ secret }}</p>

        <h3 style="margin-bottom: 15px;">步驟 2: 輸入驗證碼</h3>
        <div class="form-group">
          <label for="verify_token">6 位數驗證碼</label>
          <input
            type="text"
            id="verify_token"
            v-model="verifyToken"
            placeholder="000000"
            maxlength="6"
            pattern="[0-9]{6}"
            required
          />
        </div>
        <div v-if="twoFactorError" class="error">{{ twoFactorError }}</div>
        <div style="display: flex; gap: 10px;">
          <button @click="verify2FASetup" class="btn btn-primary">驗證並啟用</button>
          <button @click="cancel2FASetup" class="btn btn-secondary">取消</button>
        </div>
      </div>

      <!-- 已啟用 2FA -->
      <div v-if="user?.two_factor_enabled && !showDisable2FA">
        <p style="color: #51cf66; margin-bottom: 15px;">✓ 雙因素認證已啟用</p>
        <button @click="showDisable2FA = true" class="btn btn-danger">停用 2FA</button>
      </div>

      <!-- 停用 2FA -->
      <div v-if="showDisable2FA">
        <h3 style="margin-bottom: 15px;">停用雙因素認證</h3>
        <p style="margin-bottom: 15px; color: #ff6b6b;">警告：停用 2FA 會降低帳戶安全性</p>
        <div class="form-group">
          <label for="disable_token">輸入驗證碼以確認</label>
          <input
            type="text"
            id="disable_token"
            v-model="disableToken"
            placeholder="000000"
            maxlength="6"
            pattern="[0-9]{6}"
            required
          />
        </div>
        <div v-if="twoFactorError" class="error">{{ twoFactorError }}</div>
        <div style="display: flex; gap: 10px;">
          <button @click="handleDisable2FA" class="btn btn-danger">確認停用</button>
          <button @click="showDisable2FA = false; disableToken = ''" class="btn btn-secondary">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import type { User } from '@/types'

const user = ref<User | null>(null)
const passwordForm = ref({
  current_password: '',
  new_password: ''
})
const passwordError = ref('')
const passwordSuccess = ref('')

const showSetup2FA = ref(false)
const qrCode = ref('')
const secret = ref('')
const verifyToken = ref('')
const twoFactorError = ref('')

const showDisable2FA = ref(false)
const disableToken = ref('')

const loadUserProfile = async () => {
  try {
    const response = await api.getUserProfile()
    user.value = response.data
  } catch (error) {
    console.error('載入使用者資料失敗:', error)
  }
}

const handlePasswordChange = async () => {
  try {
    passwordError.value = ''
    passwordSuccess.value = ''
    await api.updateUserProfile(passwordForm.value)
    passwordSuccess.value = '密碼更新成功'
    passwordForm.value = {
      current_password: '',
      new_password: ''
    }
  } catch (err: any) {
    passwordError.value = err.response?.data?.detail || '密碼更新失敗'
  }
}

const start2FASetup = async () => {
  try {
    twoFactorError.value = ''
    const response = await api.setup2FA()
    qrCode.value = response.data.qr_code
    secret.value = response.data.secret
    showSetup2FA.value = true
  } catch (err: any) {
    twoFactorError.value = err.response?.data?.detail || '啟用 2FA 失敗'
  }
}

const verify2FASetup = async () => {
  try {
    twoFactorError.value = ''
    await api.verify2FASetup({ token: verifyToken.value })
    showSetup2FA.value = false
    verifyToken.value = ''
    qrCode.value = ''
    secret.value = ''
    await loadUserProfile()
    alert('2FA 已成功啟用！')
  } catch (err: any) {
    twoFactorError.value = err.response?.data?.detail || '驗證失敗'
  }
}

const cancel2FASetup = () => {
  showSetup2FA.value = false
  verifyToken.value = ''
  qrCode.value = ''
  secret.value = ''
  twoFactorError.value = ''
}

const handleDisable2FA = async () => {
  try {
    twoFactorError.value = ''
    await api.disable2FA({ token: disableToken.value })
    showDisable2FA.value = false
    disableToken.value = ''
    await loadUserProfile()
    alert('2FA 已停用')
  } catch (err: any) {
    twoFactorError.value = err.response?.data?.detail || '停用失敗'
  }
}

onMounted(loadUserProfile)
</script>
