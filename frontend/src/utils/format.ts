/**
 * Format a number with thousand separators.
 * @param value The value to format.
 * @param fractionDigits Number of decimal digits (default: 2 for non-integers usually, but strict 2 is safer for currency).
 *                       If explicitly provided, it uses that fixed precision.
 *                       If omitted, it defaults to 2 maximum fraction digits.
 * @returns Formatted string.
 */
export const formatNumber = (value: number | string | null | undefined, minFractionDigits: number = 0, maxFractionDigits: number = 2): string => {
  if (value === null || value === undefined || value === '') return '0'
  
  const num = Number(value)
  if (isNaN(num)) return '0'

  return num.toLocaleString('en-US', {
    minimumFractionDigits: minFractionDigits,
    maximumFractionDigits: maxFractionDigits
  })
}

/**
 * Format currency specifically (usually 2 decimals, maybe 0 if user prefers, but standard is 2).
 */
export const formatAmount = (value: number | string | null | undefined): string => {
  return formatNumber(value, 2, 2)
}

/**
 * Format integer values (e.g. counts, or rounded amounts).
 */
export const formatInteger = (value: number | string | null | undefined): string => {
  return formatNumber(value, 0, 0)
}

/**
 * Format exchange rates (usually 4 decimals).
 */
export const formatRate = (value: number | string | null | undefined): string => {
  return formatNumber(value, 4, 4)
}
