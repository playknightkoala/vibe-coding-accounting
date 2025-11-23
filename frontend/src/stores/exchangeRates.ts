import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ExchangeRate } from '@/types'
import api from '@/services/api'

export const useExchangeRatesStore = defineStore('exchangeRates', () => {
    const rates = ref<ExchangeRate[]>([])
    const isLoading = ref(false)
    const error = ref<string | null>(null)

    const fetchRates = async () => {
        isLoading.value = true
        error.value = null
        try {
            const response = await api.getExchangeRates()
            rates.value = response.data
        } catch (err) {
            console.error('Failed to fetch exchange rates:', err)
            error.value = '無法取得匯率資料'
        } finally {
            isLoading.value = false
        }
    }

    return {
        rates,
        isLoading,
        error,
        fetchRates
    }
})
