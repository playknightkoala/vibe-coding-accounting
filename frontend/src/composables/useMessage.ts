import { ref } from 'vue'

export function useMessage() {
  const isOpen = ref(false)
  const type = ref<'success' | 'error'>('success')
  const message = ref('')

  const showSuccess = (msg: string) => {
    type.value = 'success'
    message.value = msg
    isOpen.value = true
  }

  const showError = (msg: string) => {
    type.value = 'error'
    message.value = msg
    isOpen.value = true
  }

  const show = (msgType: 'success' | 'error', msg: string) => {
    type.value = msgType
    message.value = msg
    isOpen.value = true
  }

  const close = () => {
    isOpen.value = false
  }

  return {
    isOpen,
    type,
    message,
    showSuccess,
    showError,
    show,
    close
  }
}
