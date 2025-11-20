import { formatDateTime, formatDateTimeForBackend, formatDateTimeForInput } from '@/utils/dateFormat'

export function useDateTime() {
  const getCurrentDate = () => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const getCurrentDateTime = () => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    const hours = String(now.getHours()).padStart(2, '0')
    const minutes = String(now.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}`
  }

  const getNextMonthDate = () => {
    const now = new Date()
    const nextMonth = new Date(now.setMonth(now.getMonth() + 1))
    const year = nextMonth.getFullYear()
    const month = String(nextMonth.getMonth() + 1).padStart(2, '0')
    const day = String(nextMonth.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const getTodayString = () => {
    const now = new Date()
    const year = now.getFullYear()
    const month = String(now.getMonth() + 1).padStart(2, '0')
    const day = String(now.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  return {
    getCurrentDate,
    getCurrentDateTime,
    getNextMonthDate,
    getTodayString,
    formatDateTime,
    formatDateTimeForBackend,
    formatDateTimeForInput
  }
}
