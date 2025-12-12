<template>
  <div class="container">
    <h1>匯率查詢</h1>

    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">
        <div style="display: flex; gap: 10px; align-items: center;">
          <label style="margin: 0;">選擇銀行：</label>
          <select v-model="selectedBank" @change="handleBankChange" style="padding: 8px 12px; border-radius: 5px; border: 1px solid #4a5568; background: #2d3748; color: white;">
            <option value="bot">臺灣銀行</option>
            <option value="esun">玉山銀行 (網銀/App優惠)</option>
          </select>
        </div>
        <button @click="handleRefresh" class="btn btn-primary" :disabled="exchangeRatesStore.isLoading" style="display: flex; align-items: center; gap: 6px;">
          <span class="material-icons" v-if="!exchangeRatesStore.isLoading" style="font-size: 18px;">refresh</span>
          {{ exchangeRatesStore.isLoading ? '載入中...' : '刷新資料' }}
        </button>
      </div>

      <div v-if="lastUpdateTime" style="margin-bottom: 20px; color: #a0aec0; font-size: 14px;">
        最後更新時間：{{ lastUpdateTime }}
      </div>

      <div v-if="exchangeRatesStore.error" class="error" style="margin-bottom: 20px;">
        {{ exchangeRatesStore.error }}
      </div>

      <div v-if="exchangeRatesStore.isLoading" style="text-align: center; padding: 40px;">
        <p>載入中...</p>
      </div>

      <div v-else-if="exchangeRatesStore.rates.length > 0" style="overflow-x: auto;">
        <table class="table">
          <thead>
            <tr>
              <th>幣別代碼</th>
              <th>幣別名稱</th>
              <th>本行買入</th>
              <th>本行賣出</th>
              <th>更新時間</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rate in exchangeRatesStore.rates" :key="rate.id">
              <td><strong>{{ rate.currency_code }}</strong></td>
              <td>{{ rate.currency_name }}</td>
              <td>{{ rate.buying_rate !== null ? rate.buying_rate.toFixed(4) : '-' }}</td>
              <td>{{ rate.selling_rate !== null ? rate.selling_rate.toFixed(4) : '-' }}</td>
              <td>{{ formatDateTimeToTaipei(rate.updated_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else style="text-align: center; padding: 40px;">
        <p>目前沒有匯率資料</p>
        <p style="color: #a0aec0; font-size: 14px; margin-top: 10px;">請等待後台排程更新匯率資料</p>
      </div>
    </div>

    <div class="card" style="margin-top: 20px;">
      <h3>說明</h3>
      <ul style="line-height: 1.8; color: #a0aec0;">
        <li><strong>臺灣銀行</strong>：即期匯率（每小時更新）</li>
        <li><strong>玉山銀行</strong>：網銀/App優惠匯率（每小時更新）</li>
        <li>本行買入：您賣出外幣時的匯率（銀行向您買入外幣）</li>
        <li>本行賣出：您買入外幣時的匯率（銀行向您賣出外幣）</li>
        <li>匯率資料由後台排程自動更新，點擊「刷新資料」可重新載入最新資料</li>
        <li>部分幣別可能無即期匯率，顯示為「-」</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useExchangeRatesStore } from '@/stores/exchangeRates'
import { formatDateTimeToTaipei } from '@/utils/dateFormat'

const exchangeRatesStore = useExchangeRatesStore()
const selectedBank = ref('bot') // 預設臺灣銀行

const lastUpdateTime = computed(() => {
  if (exchangeRatesStore.rates.length === 0) return null
  // 取所有匯率中最新的更新時間
  const latestTime = exchangeRatesStore.rates.reduce((latest, rate) => {
    const rateTime = new Date(rate.updated_at)
    return rateTime > latest ? rateTime : latest
  }, new Date(0))
  return formatDateTimeToTaipei(latestTime.toISOString())
})

const handleBankChange = async () => {
  await exchangeRatesStore.fetchRates(selectedBank.value)
}

const handleRefresh = async () => {
  await exchangeRatesStore.fetchRates(selectedBank.value)
}

onMounted(() => {
  exchangeRatesStore.fetchRates(selectedBank.value)
})
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  background: rgba(45, 55, 72, 0.6);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.table th,
.table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #4a5568;
}

.table th {
  background: rgba(0, 212, 255, 0.1);
  color: #00d4ff;
  font-weight: 600;
}

.table tbody tr:hover {
  background: rgba(0, 212, 255, 0.05);
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 212, 255, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid #ef4444;
  color: #ef4444;
  padding: 10px;
  border-radius: 5px;
}

h1 {
  color: #00d4ff;
  margin-bottom: 20px;
}

h3 {
  color: #00d4ff;
  margin-bottom: 15px;
}
</style>
