import { ref } from 'vue'

export function useModal() {
  const isOpen = ref(false)
  const error = ref('')

  const open = () => {
    isOpen.value = true
    error.value = ''
  }

  const close = () => {
    isOpen.value = false
    error.value = ''
  }

  const setError = (message: string) => {
    error.value = message
  }

  const clearError = () => {
    error.value = ''
  }

  return {
    isOpen,
    error,
    open,
    close,
    setError,
    clearError
  }
}
