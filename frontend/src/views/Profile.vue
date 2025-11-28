<template>
  <div class="container">
    <h1>個人設定</h1>

    <!-- 使用者資訊 -->
    <div class="card">
      <h2>帳號資訊</h2>
      <p><strong>電子郵件：</strong>{{ user?.email }}</p>
      <p v-if="user?.is_google_user"><strong>登入方式：</strong>Google 帳號</p>
      <p v-if="!user?.is_google_user"><strong>2FA 狀態：</strong>{{ user?.two_factor_enabled ? '已啟用' : '未啟用' }}</p>
    </div>

    <!-- 變更密碼 (僅一般帳號) -->
    <div v-if="!user?.is_google_user" class="card">
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

    <!-- 2FA 設定 (僅一般帳號) -->
    <div v-if="!user?.is_google_user" class="card">
      <h2>雙因素認證 (2FA)</h2>
      <p style="margin-bottom: 15px; color: #a0aec0;">
        使用手機驗證器應用程式（如 Google Authenticator、Microsoft Authenticator）來增加帳號安全性
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
        <p style="margin-bottom: 15px; color: #ff6b6b;">警告：停用 2FA 會降低帳號安全性</p>
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
            將所有資料匯出為加密的 JSON 檔案，可用於備份或轉移到其他使用者帳號
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

    <!-- 危險操作區域 -->
    <div class="card" style="border: 2px solid #ff6b6b;">
      <h2 style="color: #ff6b6b;">危險操作</h2>
      <p style="margin-bottom: 20px; color: #ff9999;">
        ⚠️ 以下操作無法復原，請謹慎操作
      </p>

      <div style="display: flex; flex-direction: column; gap: 20px;">
        <!-- 清除所有資料 -->
        <div style="padding: 15px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">
          <h3 style="margin-bottom: 10px; color: #ff6b6b;">清除所有資料</h3>
          <p style="margin-bottom: 15px; font-size: 14px; color: #a0aec0;">
            刪除所有帳戶、交易、預算、類別等資料，但<strong>保留您的帳號</strong>。清除後帳號將恢復到剛註冊時的狀態。
          </p>
          <p style="margin-bottom: 15px; font-size: 13px; color: #ff9999;">
            💡 建議：清除資料前先匯出備份
          </p>
          <button @click="showClearDataConfirm = true" class="btn btn-danger">
            清除所有資料
          </button>
        </div>

        <!-- 刪除帳號 -->
        <div style="padding: 15px; background: rgba(255, 107, 107, 0.15); border-radius: 8px;">
          <h3 style="margin-bottom: 10px; color: #ff6b6b;">刪除帳號</h3>
          <p style="margin-bottom: 15px; font-size: 14px; color: #a0aec0;">
            <strong>永久刪除</strong>您的帳號及所有相關資料（帳戶、交易、預算、類別等）。此操作無法復原！
          </p>
          <p style="margin-bottom: 15px; font-size: 13px; color: #ff9999;">
            ⚠️ 警告：刪除後您將無法登入，且所有資料將永久消失
          </p>
          <button @click="showDeleteAccountConfirm = true" class="btn btn-danger">
            刪除帳號
          </button>
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

    <!-- 清除資料確認彈窗 -->
    <ConfirmModal
      v-model="showClearDataConfirm"
      title="確認清除所有資料"
      :message="`⚠️ 此操作將刪除您的所有資料：\n\n• 所有帳戶及交易記錄\n• 所有預算設定\n• 所有類別設定\n\n但會保留您的帳號，您仍可登入。\n帳號將恢復到初始狀態（含預設帳戶）。\n\n建議：清除前先匯出備份！`"
      confirm-text="我已經瞭解風險"
      cancel-text="取消"
      confirm-type="danger"
      :require-confirm-text="true"
      confirm-text-placeholder="我已經瞭解風險"
      @confirm="confirmClearData"
    />

    <!-- 刪除帳號確認彈窗 -->
    <ConfirmModal
      v-model="showDeleteAccountConfirm"
      title="確認刪除帳號"
      :message="`🚨 此操作無法復原！\n\n刪除帳號將：\n• 永久刪除您的帳號\n• 刪除所有帳戶及交易記錄\n• 刪除所有預算設定\n• 刪除所有類別設定\n• 您將無法再登入此帳號\n\n所有資料將永久消失！`"
      confirm-text="我已經瞭解風險"
      cancel-text="取消"
      confirm-type="danger"
      :require-confirm-text="true"
      confirm-text-placeholder="我已經瞭解風險"
      @confirm="confirmDeleteAccount"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import type { User } from '@/types'
import MessageModal from '@/components/MessageModal.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { useDateTime } from '@/composables/useDateTime'

const { getTodayString } = useDateTime()

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

// Dangerous operations
const showClearDataConfirm = ref(false)
const showDeleteAccountConfirm = ref(false)

// Message modal
const showMessageModal = ref(false)
const messageType = ref<'success' | 'error'>('success')
const message = ref('')

const loadUserProfile = async () => {
  try {
    const response = await api.getCurrentUser()
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
    let filename = `accounting_data_${getTodayString()}.json`
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

const confirmClearData = async () => {
  try {
    await api.clearUserData()

    messageType.value = 'success'
    message.value = '所有資料已清除！您的帳號已恢復到初始狀態。'
    showMessageModal.value = true

    // 重新載入使用者資料
    await loadUserProfile()
  } catch (err: any) {
    messageType.value = 'error'
    message.value = err.response?.data?.detail || '清除資料失敗'
    showMessageModal.value = true
  }
}

const confirmDeleteAccount = async () => {
  try {
    await api.deleteUserAccount()

    // 清除本地 token
    localStorage.removeItem('token')

    // 顯示成功訊息後跳轉到登入頁
    messageType.value = 'success'
    message.value = '帳號已成功刪除。感謝您的使用，再見！'
    showMessageModal.value = true

    // 延遲跳轉，讓使用者看到訊息
    setTimeout(() => {
      window.location.href = '/login'
    }, 2000)
  } catch (err: any) {
    messageType.value = 'error'
    message.value = err.response?.data?.detail || '刪除帳號失敗'
    showMessageModal.value = true
  }
}

onMounted(loadUserProfile)
</script>
