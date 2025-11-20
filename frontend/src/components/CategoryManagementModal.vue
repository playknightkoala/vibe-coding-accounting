<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content" style="max-width: 600px;">
      <h2 style="color: #00d4ff;">管理類別</h2>

      <!-- 新增類別 -->
      <div style="margin-bottom: 20px;">
        <div style="display: flex; gap: 10px;">
          <input
            type="text"
            v-model="newCategoryName"
            placeholder="輸入新類別名稱"
            style="flex: 1; padding: 8px; border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 4px; background: rgba(26, 31, 58, 0.6); color: #e0e6ed;"
          />
          <button @click="handleAddCategory" class="btn btn-primary" style="padding: 8px 15px;">
            新增
          </button>
        </div>
      </div>

      <!-- 類別列表（可拖拉排序） -->
      <div style="margin-bottom: 20px;">
        <p style="color: #a0aec0; font-size: 14px; margin-bottom: 10px;">
          拖拉以調整順序
        </p>
        <div ref="sortableContainer" style="display: flex; flex-direction: column; gap: 8px;">
          <div
            v-for="category in categories"
            :key="category.id"
            :data-id="category.id"
            style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(26, 31, 58, 0.6); border: 1px solid rgba(0, 212, 255, 0.2); border-radius: 6px; cursor: move;"
          >
            <div style="display: flex; align-items: center; gap: 10px;">
              <span style="color: #a0aec0; font-size: 18px;">☰</span>
              <input
                v-if="editingCategoryId === category.id"
                type="text"
                v-model="editingCategoryName"
                @keyup.enter="handleSaveCategory(category.id)"
                @blur="handleSaveCategory(category.id)"
                style="padding: 4px 8px; border: 1px solid rgba(0, 212, 255, 0.5); border-radius: 4px; background: rgba(26, 31, 58, 0.8); color: #e0e6ed;"
                autofocus
              />
              <span v-else style="color: #e0e6ed;">{{ category.name }}</span>
            </div>
            <div style="display: flex; gap: 8px;">
              <button
                v-if="editingCategoryId !== category.id"
                @click="handleStartEdit(category)"
                class="btn btn-primary"
                style="padding: 4px 12px; font-size: 13px;"
              >
                編輯
              </button>
              <button
                @click="handleDeleteCategory(category.id)"
                class="btn btn-danger"
                style="padding: 4px 12px; font-size: 13px;"
              >
                刪除
              </button>
            </div>
          </div>
        </div>
      </div>

      <button @click="handleClose" class="btn btn-secondary" style="width: 100%;">
        關閉
      </button>
    </div>

    <!-- 刪除確認對話框 -->
    <ConfirmModal
      v-model="showConfirmModal"
      title="確認刪除"
      message="確定要刪除此類別嗎？刪除後將無法復原。"
      confirm-text="刪除"
      cancel-text="取消"
      confirm-type="danger"
      @confirm="confirmDeleteCategory"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import api from '@/services/api'
import type { Category } from '@/types'
import Sortable from 'sortablejs'
import ConfirmModal from '@/components/ConfirmModal.vue'

interface Props {
  modelValue: boolean
  categories: Category[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'update:categories', value: Category[]): void
  (e: 'categoriesChanged'): void
  (e: 'showMessage', type: 'success' | 'error', message: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const sortableContainer = ref<HTMLElement | null>(null)
const newCategoryName = ref('')
const editingCategoryId = ref<number | null>(null)
const editingCategoryName = ref('')

// Confirm modal
const showConfirmModal = ref(false)
const deleteCategoryId = ref<number | null>(null)

// 監聽 modal 打開，初始化 Sortable
watch(() => props.modelValue, async (newVal) => {
  if (newVal) {
    await nextTick()
    initSortable()
  }
})

const initSortable = () => {
  if (sortableContainer.value) {
    Sortable.create(sortableContainer.value, {
      animation: 150,
      ghostClass: 'sortable-ghost',
      onEnd: async (evt) => {
        if (evt.oldIndex !== undefined && evt.newIndex !== undefined) {
          const updatedCategories = [...props.categories]
          const movedCategory = updatedCategories.splice(evt.oldIndex, 1)[0]
          updatedCategories.splice(evt.newIndex, 0, movedCategory)

          // 準備更新資料
          const orders = updatedCategories.map((cat, index) => ({
            category_id: cat.id,
            order_index: index
          }))

          try {
            await api.reorderCategories(orders)
            emit('update:categories', updatedCategories)
            emit('categoriesChanged')
          } catch (err) {
            console.error('更新類別順序失敗:', err)
            emit('showMessage', 'error', '更新類別順序失敗')
            emit('categoriesChanged')
          }
        }
      }
    })
  }
}

const handleAddCategory = async () => {
  if (!newCategoryName.value.trim()) return

  try {
    await api.createCategory({
      name: newCategoryName.value.trim(),
      order_index: props.categories.length
    })
    newCategoryName.value = ''
    emit('showMessage', 'success', '類別已新增')
    emit('categoriesChanged')
  } catch (err: any) {
    console.error('新增類別失敗:', err)
    emit('showMessage', 'error', err.response?.data?.detail || '新增類別失敗')
  }
}

const handleStartEdit = (category: Category) => {
  editingCategoryId.value = category.id
  editingCategoryName.value = category.name
}

const handleSaveCategory = async (categoryId: number) => {
  if (!editingCategoryName.value.trim()) {
    editingCategoryId.value = null
    return
  }

  try {
    await api.updateCategory(categoryId, {
      name: editingCategoryName.value.trim()
    })
    editingCategoryId.value = null
    editingCategoryName.value = ''
    emit('showMessage', 'success', '類別已更新')
    emit('categoriesChanged')
  } catch (err: any) {
    console.error('更新類別失敗:', err)
    emit('showMessage', 'error', err.response?.data?.detail || '更新類別失敗')
    editingCategoryId.value = null
  }
}

const handleDeleteCategory = (categoryId: number) => {
  deleteCategoryId.value = categoryId
  showConfirmModal.value = true
}

const confirmDeleteCategory = async () => {
  if (deleteCategoryId.value === null) return

  try {
    await api.deleteCategory(deleteCategoryId.value)
    emit('showMessage', 'success', '類別已刪除')
    emit('categoriesChanged')
  } catch (err: any) {
    console.error('刪除類別失敗:', err)
    emit('showMessage', 'error', err.response?.data?.detail || '刪除類別失敗')
  }
  deleteCategoryId.value = null
}

const handleClose = () => {
  emit('update:modelValue', false)
  newCategoryName.value = ''
  editingCategoryId.value = null
  editingCategoryName.value = ''
}
</script>
