<template>
  <div class="container">
    <h1>帳戶</h1>

    <div class="card">
      <button @click="modal.open()" class="btn btn-primary">新增帳戶</button>

      <div style="overflow-x: auto;" v-if="accountsStore.accounts.length > 0">
        <table class="table" style="margin-top: 20px;">
          <thead>
            <tr>
              <th>名稱</th>
              <th>類型</th>
              <th>餘額</th>
              <th>幣別</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="account in accountsStore.accounts" :key="account.id">
              <td>{{ account.name }}</td>
              <td>{{ accountsStore.getAccountTypeText(account.account_type) }}</td>
              <td>${{ account.balance.toFixed(2) }}</td>
              <td>{{ account.currency }}</td>
              <td>
                <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                  <button @click="handleEdit(account)" class="btn btn-primary" style="padding: 5px 10px;">
                    編輯
                  </button>
                  <button @click="handleDelete(account.id)" class="btn btn-danger" style="padding: 5px 10px;">
                    刪除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else style="margin-top: 20px;">尚無帳戶</p>
    </div>

    <div v-if="modal.isOpen.value" class="modal">
      <div class="modal-content">
        <h2>{{ formController.isEditing() ? '編輯帳戶' : '新增帳戶' }}</h2>
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label>帳戶名稱</label>
            <input v-model="formController.form.value.name" required />
          </div>
          <div class="form-group">
            <label>帳戶類型</label>
            <select v-model="formController.form.value.account_type" required>
              <option value="cash">現金</option>
              <option value="bank">銀行</option>
              <option value="credit_card">信用卡</option>
              <option value="stored_value">儲值卡</option>
              <option value="securities">證券戶</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div class="form-group">
            <label>幣別</label>
            <select v-model="formController.form.value.currency" required>
              <option value="TWD">TWD</option>
              <option value="USD">USD</option>
              <option value="JPY">JPY</option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="formController.form.value.description"></textarea>
          </div>
          <div class="form-group" v-if="!formController.isEditing()">
            <label>初始金額（選填）</label>
            <input
              type="number"
              step="0.01"
              v-model.number="formController.form.value.initial_balance"
              placeholder="0.00"
            />
            <p style="margin-top: 5px; font-size: 12px; color: #a0aec0;">
              可輸入此帳戶目前已有的金額，預設為 0
            </p>
          </div>
          <div v-if="modal.error.value" class="error">{{ modal.error.value }}</div>
          <div style="display: flex; gap: 10px; margin-top: 20px;">
            <button type="submit" class="btn btn-primary">{{ formController.isEditing() ? '更新' : '建立' }}</button>
            <button type="button" @click="handleClose" class="btn btn-secondary">取消</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 刪除確認對話框 -->
    <ConfirmModal
      v-model="confirmDialog.isOpen.value"
      title="確認刪除"
      message="確定要刪除此帳戶嗎？刪除後將無法復原。"
      confirm-text="刪除"
      cancel-text="取消"
      confirm-type="danger"
      @confirm="confirmDialog.handleConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import type { Account, AccountCreate } from '@/types'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { useAccountsStore } from '@/stores/accounts'
import { useModal } from '@/composables/useModal'
import { useConfirm } from '@/composables/useConfirm'
import { useForm } from '@/composables/useForm'

const accountsStore = useAccountsStore()
const modal = useModal()
const confirmDialog = useConfirm()

const initialFormData: AccountCreate = {
  name: '',
  account_type: 'cash',
  currency: 'TWD',
  description: '',
  initial_balance: 0
}

const formController = useForm<AccountCreate>(initialFormData)

const handleEdit = (account: Account) => {
  formController.setForm({
    name: account.name,
    account_type: account.account_type,
    currency: account.currency,
    description: account.description || ''
  }, account.id)
  modal.open()
}

const handleDelete = (id: number) => {
  confirmDialog.confirm(id, async () => {
    try {
      await accountsStore.deleteAccount(id)
    } catch (err) {
      console.error('刪除帳戶時發生錯誤:', err)
    }
  })
}

const handleSubmit = async () => {
  try {
    modal.clearError()
    if (formController.isEditing()) {
      await accountsStore.updateAccount(formController.editingId.value!, {
        name: formController.form.value.name,
        description: formController.form.value.description,
        account_type: formController.form.value.account_type,
        currency: formController.form.value.currency
      })
    } else {
      await accountsStore.createAccount(formController.form.value)
    }
    handleClose()
  } catch (err: any) {
    modal.setError(err.response?.data?.detail || (formController.isEditing() ? '更新帳戶失敗' : '建立帳戶失敗'))
  }
}

const handleClose = () => {
  modal.close()
  formController.resetForm()
}

onMounted(() => {
  accountsStore.fetchAccounts()
})
</script>
