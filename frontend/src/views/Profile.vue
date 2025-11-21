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

    <!-- 資料匯出匯入 -->
    <div class="card">
      <h2>資料匯出匯入</h2>
      <p style="margin-bottom: 15px; color: #a0aec0;">
        匯出您的所有記帳資料（帳戶、交易、預算），或從備份檔案中還原資料
      </p>
      <div style="padding: 10px; background: rgba(0, 212, 255, 0.1); border-left: 3px solid #00d4ff; border-radius: 4px; margin-bottom: 15px;">
        <p style="margin: 0; font-size: 14px; color: #00d4ff;">
          🔒 您的資料已使用應用程式專屬密鑰加密，只能在本應用程式中匯入
        </p>
      </div>

      <div style="display: flex; flex-direction: column; gap: 15px;">
        <!-- 匯出功能 -->
        <div>
          <h3 style="margin-bottom: 10px;">匯出資料</h3>
          <p style="margin-bottom: 10px; font-size: 14px; color: #a0aec0;">
            將所有資料匯出為加密的 JSON 檔案，可用於備份或轉移到其他帳號
          </p>
          <button @click="handleExportData" class="btn btn-primary" :disabled="exportLoading">
            {{ exportLoading ? '匯出中...' : '匯出資料' }}
          </button>
        </div>

        <!-- 匯入功能 -->
        <div>
          <h3 style="margin-bottom: 10px;">匯入資料</h3>
          <p style="margin-bottom: 10px; font-size: 14px; color: #a0aec0;">
            從加密的 JSON 檔案還原資料。注意：這會在現有資料基礎上新增，不會覆蓋現有資料
          </p>
          <div style="display: flex; align-items: center; gap: 10px;">
            <input
              type="file"
              ref="fileInput"
              accept=".json"
              @change="handleFileSelect"
              style="display: none;"
            />
            <button @click="triggerFileInput" class="btn btn-secondary">
              選擇檔案
            </button>
            <span v-if="selectedFile" style="color: #00d4ff;">{{ selectedFile.name }}</span>
          </div>
          <button
            v-if="selectedFile"
            @click="handleImportData"
            class="btn btn-primary"
            :disabled="importLoading"
            style="margin-top: 10px;"
          >
            {{ importLoading ? '匯入中...' : '開始匯入' }}
          </button>
        </div>
      </div>

      <div v-if="importExportError" class="error" style="margin-top: 15px;">{{ importExportError }}</div>
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

    <!-- 消息提示彈窗 -->
    <MessageModal
      v-model="showMessageModal"
      :type="messageType"
      :message="message"
    />

    <!-- 匯入確認彈窗 -->
    <ConfirmModal
      v-model="showImportConfirm"
      title="確認匯入資料"
      :message="`匯入資料將會覆蓋現有的相同資料：\n\n• 帳戶：相同名稱、類型、幣別的帳戶將被覆蓋\n• 交易：相同日期和描述的交易將被覆蓋\n• 預算：相同名稱的預算將被覆蓋\n\n確定要繼續匯入嗎？`"
      confirm-text="確定匯入"
      cancel-text="取消"
      confirm-type="danger"
      @confirm="confirmImport"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import type { User } from '@/types'
import MessageModal from '@/components/MessageModal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'

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

// Import/Export
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const exportLoading = ref(false)
const importLoading = ref(false)
const importExportError = ref('')
const showImportConfirm = ref(false)

// Message modal
const showMessageModal = ref(false)
const messageType = ref<'success' | 'error'>('success')
const message = ref('')

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
    messageType.value = 'success'
    message.value = '2FA 已成功啟用！'
    showMessageModal.value = true
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
    messageType.value = 'success'
    message.value = '2FA 已停用'
    showMessageModal.value = true
  } catch (err: any) {
    twoFactorError.value = err.response?.data?.detail || '停用失敗'
  }
}

const handleExportData = async () => {
  try {
    exportLoading.value = true
    importExportError.value = ''

    const response = await api.exportUserData()

    // 從 blob 讀取 JSON 內容
    const text = await response.data.text()
    const blob = new Blob([text], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // 從響應頭取得檔案名稱，或使用預設名稱
    const contentDisposition = response.headers['content-disposition']
    let filename = `accounting_data_${new Date().toISOString().split('T')[0]}.json`
    if (contentDisposition) {
      // 修正檔名解析，處理可能的引號和額外字符
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1].replace(/['"]/g, '').trim()
      }
    }

    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    messageType.value = 'success'
    message.value = '資料匯出成功！'
    showMessageModal.value = true
  } catch (err: any) {
    importExportError.value = err.response?.data?.detail || '匯出資料失敗'
  } finally {
    exportLoading.value = false
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    importExportError.value = ''
  }
}

const handleImportData = () => {
  if (!selectedFile.value) return

  // 顯示確認彈窗
  importExportError.value = ''
  showImportConfirm.value = true
}

const confirmImport = async () => {
  if (!selectedFile.value) return

  try {
    importLoading.value = true
    importExportError.value = ''

    const response = await api.importUserData(selectedFile.value)

    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }

    const stats = response.data.stats
    const statsMessage = `資料匯入成功！\n\n` +
      `帳戶：新增 ${stats.accounts_created} 個，覆蓋 ${stats.accounts_updated} 個\n` +
      `交易：新增 ${stats.transactions_created} 筆，覆蓋 ${stats.transactions_updated} 筆\n` +
      `預算：新增 ${stats.budgets_created} 個，覆蓋 ${stats.budgets_updated} 個`

    messageType.value = 'success'
    message.value = statsMessage
    showMessageModal.value = true

    // 重新載入使用者資料
    await loadUserProfile()
  } catch (err: any) {
    importExportError.value = err.response?.data?.detail || '匯入資料失敗'
  } finally {
    importLoading.value = false
  }
}

onMounted(loadUserProfile)
</script>
