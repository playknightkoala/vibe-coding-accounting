import { ref } from 'vue'

export function useConfirm() {
  const isOpen = ref(false)
  const itemId = ref<number | null>(null)
  const onConfirmCallback = ref<(() => void | Promise<void>) | null>(null)

  const confirm = (id: number, callback: () => void | Promise<void>) => {
    itemId.value = id
    onConfirmCallback.value = callback
    isOpen.value = true
  }

  const handleConfirm = async () => {
    if (onConfirmCallback.value) {
      await onConfirmCallback.value()
    }
    reset()
  }

  const handleCancel = () => {
    reset()
  }

  const reset = () => {
    isOpen.value = false
    itemId.value = null
    onConfirmCallback.value = null
  }

  return {
    isOpen,
    itemId,
    confirm,
    handleConfirm,
    handleCancel
  }
}
