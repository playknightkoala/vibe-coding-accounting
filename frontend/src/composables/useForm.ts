import { ref } from 'vue'

export function useForm<T>(initialData: T) {
  const form = ref<T>({ ...initialData } as T)
  const editingId = ref<number | null>(null)

  const resetForm = () => {
    form.value = { ...initialData } as T
    editingId.value = null
  }

  const setForm = (data: T, id?: number) => {
    form.value = { ...data } as T
    if (id !== undefined) {
      editingId.value = id
    }
  }

  const isEditing = () => {
    return editingId.value !== null
  }

  return {
    form,
    editingId,
    resetForm,
    setForm,
    isEditing
  }
}
