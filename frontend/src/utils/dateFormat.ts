/**
 * 將 ISO 格式的日期時間轉換為顯示格式
 * @param dateString - ISO 格式的日期時間字符串 (如: "2025-11-19T00:00:00" 或 "2025-11-19T00:00:00Z")
 * @returns 格式化後的日期時間字符串 (如: "2025-11-19 00:00:00")
 */
export function formatDateTime(dateString: string): string {
  if (!dateString) return ''

  // 移除時區標記 (Z) 和毫秒
  let cleaned = dateString.replace('Z', '').split('.')[0]

  // 將 T 替換為空格
  return cleaned.replace('T', ' ')
}

/**
 * 將 datetime-local 輸入格式轉換為後端需要的格式
 * @param dateTimeLocal - datetime-local 輸入的值 (如: "2025-11-19T14:30")
 * @returns ISO 格式的日期時間字符串 (如: "2025-11-19T14:30:00")
 */
export function formatDateTimeForBackend(dateTimeLocal: string): string {
  if (!dateTimeLocal) return ''

  // 如果已經包含秒數，直接返回
  if (dateTimeLocal.length === 19) {
    return dateTimeLocal
  }

  // 如果是 datetime-local 格式 (YYYY-MM-DDTHH:mm)，添加秒數
  if (dateTimeLocal.length === 16) {
    return `${dateTimeLocal}:00`
  }

  return dateTimeLocal
}

/**
 * 將顯示格式的日期時間轉換為 datetime-local 輸入格式
 * @param dateString - 顯示格式的日期時間 (如: "2025-11-19 00:00:00" 或 "2025-11-19T00:00:00")
 * @returns datetime-local 格式 (如: "2025-11-19T00:00")
 */
export function formatDateTimeForInput(dateString: string): string {
  if (!dateString) return ''

  // 將空格替換為 T，並只保留到分鐘
  const normalized = dateString.replace(' ', 'T')
  return normalized.substring(0, 16)
}
