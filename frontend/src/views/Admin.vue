<template>
  <div class="admin-container">
    <h1>管理員面板</h1>

    <div class="users-table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>電子郵件</th>
            <th>登入方式</th>
            <th>狀態</th>
            <th>2FA</th>
            <th>統計 (交/預/帳)</th>
            <th>上次登入</th>
            <th>創建時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id" :class="{ 'blocked-user': user.is_blocked }">
            <td>{{ user.id }}</td>
            <td>
              {{ user.email }}
              <span v-if="user.is_admin" class="admin-badge">管理員</span>
            </td>
            <td>{{ user.is_google_user ? 'Google' : '一般' }}</td>
            <td>
              <span :class="user.is_blocked ? 'status-blocked' : 'status-active'">
                {{ user.is_blocked ? '已封鎖' : '正常' }}
              </span>
            </td>
            <td>
              <span class="material-icons" :style="{ color: user.two_factor_enabled ? '#51cf66' : '#ff6b6b', fontSize: '18px' }">
                {{ user.two_factor_enabled ? 'check' : 'close' }}
              </span>
            </td>
            <td>{{ user.transaction_count }} / {{ user.budget_count }} / {{ user.account_count }}</td>
            <td>{{ formatDate(user.last_login_at) }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>
              <div class="action-buttons">
                <button @click="editUser(user)" class="btn-edit" title="編輯">
                  <span class="material-icons">edit</span>
                </button>

                <!-- Self-action restrictions -->
                <template v-if="user.id !== authStore.user?.id">
                  <button
                    v-if="!user.is_blocked"
                    @click="blockUser(user)"
                    class="btn-block"
                    title="封鎖"
                  ><span class="material-icons">block</span></button>
                  <button
                    v-else
                    @click="unblockUser(user)"
                    class="btn-unblock"
                    title="解除封鎖"
                  ><span class="material-icons">check</span></button>
                  <button @click="resetUserData(user)" class="btn-reset" title="重置資料">
                    <span class="material-icons">refresh</span>
                  </button>
                  <button @click="deleteUser(user)" class="btn-delete" title="刪除">
                    <span class="material-icons">delete</span>
                  </button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 編輯使用者 Modal -->
    <div v-if="showEditModal" class="modal" @click.self="showEditModal = false">
      <div class="modal-content">
        <h2>編輯使用者</h2>
        <form @submit.prevent="updateUser">
          <div class="form-group">
            <label>電子郵件:</label>
            <input
              v-if="!editingUser.is_google_user"
              v-model="editForm.email"
              type="email"
              placeholder="輸入新電子郵件 (留空表示不更改)"
            />
            <input v-else type="text" :value="editingUser.email" disabled />
            <small v-if="editingUser.is_google_user">Google 登入的使用者無法更改電子郵件</small>
          </div>

          <div class="form-group">
            <label>密碼:</label>
            <input
              v-if="!editingUser.is_google_user"
              v-model="editForm.password"
              type="password"
              placeholder="輸入新密碼 (留空表示不更改)"
            />
            <input v-else type="password" value="********" disabled />
            <small v-if="editingUser.is_google_user">Google 登入的使用者無法設定密碼</small>
          </div>

          <!-- Removed Admin Permission Checkbox -->

          <div class="form-group checkbox-group">
            <label>
              <input v-model="editForm.two_factor_enabled" type="checkbox" />
              啟用 2FA
              <small v-if="!editForm.two_factor_enabled">(取消勾選將清除 2FA 設定)</small>
            </label>
          </div>

          <div class="modal-actions">
            <button type="submit" class="btn-primary">儲存</button>
            <button type="button" @click="showEditModal = false" class="btn-secondary">取消</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 確認 Modal -->
    <div v-if="showConfirmModal" class="modal" @click.self="showConfirmModal = false">
      <div class="modal-content">
        <h2>{{ confirmTitle }}</h2>
        <p>{{ confirmMessage }}</p>
        <div class="modal-actions">
          <button @click="confirmAction" class="btn-danger">確認</button>
          <button @click="showConfirmModal = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 訊息 Modal -->
    <div v-if="showMessageModal" class="modal" @click.self="showMessageModal = false">
      <div class="modal-content">
        <h2>{{ messageType === 'success' ? '成功' : '錯誤' }}</h2>
        <p>{{ message }}</p>
        <div class="modal-actions">
          <button @click="showMessageModal = false" class="btn-primary">確定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { UserAdminInfo, AdminUserUpdate } from '@/types'
import { formatDateTime } from '@/utils/dateFormat'

const authStore = useAuthStore()
const users = ref<UserAdminInfo[]>([])
const showEditModal = ref(false)
const showConfirmModal = ref(false)
const showMessageModal = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const confirmTitle = ref('')
const confirmMessage = ref('')
const confirmCallback = ref<(() => void) | null>(null)

const editingUser = ref<UserAdminInfo | null>(null)
const editForm = ref<AdminUserUpdate>({})

onMounted(async () => {
  await loadUsers()
})

async function loadUsers() {
  try {
    const response = await api.admin.listUsers()
    users.value = response.data
  } catch (error: any) {
    showMessage('載入使用者列表失敗: ' + (error.response?.data?.detail || error.message), 'error')
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '未登入'
  // Use shorter date format YYYY/MM/DD
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function editUser(user: UserAdminInfo) {
  editingUser.value = user
  editForm.value = {
    // is_admin: user.is_admin, // Removed from edit form
    two_factor_enabled: user.two_factor_enabled
  }
  showEditModal.value = true
}

async function updateUser() {
  if (!editingUser.value) return

  try {
    // 只傳送有更改的欄位
    const updateData: AdminUserUpdate = {}

    if (editForm.value.email && editForm.value.email !== editingUser.value.email) {
      updateData.email = editForm.value.email
    }

    if (editForm.value.password) {
      updateData.password = editForm.value.password
    }

    // Removed is_admin update logic
    // if (editForm.value.is_admin !== editingUser.value.is_admin) {
    //   updateData.is_admin = editForm.value.is_admin
    // }

    if (editForm.value.two_factor_enabled !== editingUser.value.two_factor_enabled) {
      updateData.two_factor_enabled = editForm.value.two_factor_enabled
    }

    if (Object.keys(updateData).length === 0) {
      showMessage('沒有需要更新的欄位', 'error')
      return
    }

    await api.admin.updateUser(editingUser.value.id, updateData)
    showMessage('更新成功', 'success')
    showEditModal.value = false
    await loadUsers()
  } catch (error: any) {
    showMessage('更新失敗: ' + (error.response?.data?.detail || error.message), 'error')
  }
}

function blockUser(user: UserAdminInfo) {
  showConfirm(
    '確認封鎖',
    `確定要封鎖使用者 ${user.email} 嗎？封鎖後該使用者將無法登入。`,
    async () => {
      try {
        await api.admin.blockUser(user.id)
        showMessage('封鎖成功', 'success')
        await loadUsers()
      } catch (error: any) {
        showMessage('封鎖失敗: ' + (error.response?.data?.detail || error.message), 'error')
      }
    }
  )
}

function unblockUser(user: UserAdminInfo) {
  showConfirm(
    '確認解除封鎖',
    `確定要解除封鎖使用者 ${user.email} 嗎？`,
    async () => {
      try {
        await api.admin.unblockUser(user.id)
        showMessage('解除封鎖成功', 'success')
        await loadUsers()
      } catch (error: any) {
        showMessage('解除封鎖失敗: ' + (error.response?.data?.detail || error.message), 'error')
      }
    }
  )
}

function resetUserData(user: UserAdminInfo) {
  showConfirm(
    '確認重置資料',
    `確定要重置使用者 ${user.email} 的所有資料嗎？這將刪除所有交易、預算和帳戶資料,恢復到剛建立帳號的狀態。此操作無法復原!`,
    async () => {
      try {
        await api.admin.resetUserData(user.id)
        showMessage('重置資料成功', 'success')
        await loadUsers()
      } catch (error: any) {
        showMessage('重置資料失敗: ' + (error.response?.data?.detail || error.message), 'error')
      }
    }
  )
}

function deleteUser(user: UserAdminInfo) {
  showConfirm(
    '確認刪除',
    `確定要完全刪除使用者 ${user.email} 嗎？這將永久刪除該使用者及其所有資料。此操作無法復原!`,
    async () => {
      try {
        await api.admin.deleteUser(user.id)
        showMessage('刪除成功', 'success')
        await loadUsers()
      } catch (error: any) {
        showMessage('刪除失敗: ' + (error.response?.data?.detail || error.message), 'error')
      }
    }
  )
}

function showConfirm(title: string, msg: string, callback: () => void) {
  confirmTitle.value = title
  confirmMessage.value = msg
  confirmCallback.value = callback
  showConfirmModal.value = true
}

function confirmAction() {
  if (confirmCallback.value) {
    confirmCallback.value()
  }
  showConfirmModal.value = false
}

function showMessage(msg: string, type: 'success' | 'error') {
  message.value = msg
  messageType.value = type
  showMessageModal.value = true
}
</script>

<style scoped>
.admin-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

h1 {
  color: #00d4ff;
  margin-bottom: 30px;
}

.users-table-container {
  overflow-x: auto;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1000px; /* Reduced min-width */
}

.users-table th,
.users-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #2c3e50;
}

.users-table th {
  background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
  color: #00d4ff;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 10;
  white-space: nowrap; /* Prevent header wrapping */
}

.users-table tbody tr {
  transition: background-color 0.2s;
}

.users-table tbody tr:hover {
  background-color: rgba(0, 212, 255, 0.1);
}

.blocked-user {
  opacity: 0.6;
}

.admin-badge {
  background: #00d4ff;
  color: #1a1a2e;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8em;
  margin-left: 8px;
  font-weight: 600;
}

.status-active {
  color: #4caf50;
}

.status-blocked {
  color: #f44336;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-buttons button {
  padding: 6px 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1em;
  transition: transform 0.2s, opacity 0.2s;
}

.action-buttons button:hover {
  transform: scale(1.1);
  opacity: 0.8;
}

.btn-edit {
  background: #2196f3;
}

.btn-block {
  background: #ff9800;
}

.btn-unblock {
  background: #4caf50;
}

.btn-reset {
  background: #9c27b0;
}

.btn-delete {
  background: #f44336;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #00d4ff;
  font-weight: 500;
}

.form-group input[type="email"],
.form-group input[type="password"],
.form-group input[type="text"] {
  width: 100%;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid #2c3e50;
  border-radius: 5px;
  color: white;
  font-size: 14px;
}

.form-group input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: #999;
  font-size: 0.85em;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 10px;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-primary,
.btn-secondary,
.btn-danger {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: opacity 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-primary:hover,
.btn-secondary:hover,
.btn-danger:hover {
  opacity: 0.9;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 30px;
  border-radius: 10px;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.modal-content h2 {
  color: #00d4ff;
  margin-bottom: 20px;
}

.modal-content p {
  margin-bottom: 20px;
  line-height: 1.6;
}
</style>
