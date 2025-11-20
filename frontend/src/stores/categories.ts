import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Category, CategoryCreate, CategoryUpdate } from '@/types'

export const useCategoriesStore = defineStore('categories', () => {
  const categories = ref<Category[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchCategories = async () => {
    loading.value = true
    error.value = null
    try {
      const response = await api.getCategories()
      categories.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '載入類別時發生錯誤'
      console.error('載入類別時發生錯誤:', err)
    } finally {
      loading.value = false
    }
  }

  const createCategory = async (categoryData: CategoryCreate) => {
    loading.value = true
    error.value = null
    try {
      await api.createCategory(categoryData)
      await fetchCategories()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '建立類別失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateCategory = async (id: number, categoryData: CategoryUpdate) => {
    loading.value = true
    error.value = null
    try {
      await api.updateCategory(id, categoryData)
      await fetchCategories()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '更新類別失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteCategory = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await api.deleteCategory(id)
      await fetchCategories()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '刪除類別失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  const reorderCategories = async (categoryIds: number[]) => {
    loading.value = true
    error.value = null
    try {
      await api.reorderCategories(categoryIds)
      await fetchCategories()
    } catch (err: any) {
      error.value = err.response?.data?.detail || '重新排序類別失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    categories,
    loading,
    error,
    fetchCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    reorderCategories
  }
})
