<template>
  <div v-if="modelValue" class="modal">
    <div class="modal-content" style="max-width: 900px; max-height: 90vh; overflow-y: auto;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #00d4ff;">財務分析報告</h2>
        <button @click="closeModal" class="close-btn">&times;</button>
      </div>

      <div v-if="loading" style="text-align: center; padding: 40px;">
        <p>正在生成報告...</p>
      </div>

      <div v-else-if="error" style="color: #ff4444; padding: 20px; text-align: center;">
        {{ error }}
      </div>

      <div v-else-if="report">
        <!-- 日期選擇器 -->
        <div style="margin-bottom: 30px; padding: 20px; background: rgba(0, 212, 255, 0.1); border-radius: 8px;">
          <div style="display: grid; grid-template-columns: 1fr 1fr auto; gap: 15px; align-items: end;">
            <div>
              <label style="display: block; margin-bottom: 5px; color: #00d4ff;">開始日期</label>
              <input
                type="date"
                v-model="startDate"
                class="date-input"
                style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #00d4ff; background: #1a1a1a; color: white;"
              />
            </div>
            <div>
              <label style="display: block; margin-bottom: 5px; color: #00d4ff;">結束日期</label>
              <input
                type="date"
                v-model="endDate"
                class="date-input"
                style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #00d4ff; background: #1a1a1a; color: white;"
              />
            </div>
            <button
              @click="generateReport"
              style="padding: 8px 20px; background: #00d4ff; color: black; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;"
            >
              生成報告
            </button>
          </div>
        </div>

        <!-- 財務健康評分 -->
        <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(138, 43, 226, 0.2)); border-radius: 12px;">
          <h3 style="margin: 0 0 10px 0; color: #00d4ff;">財務健康評分</h3>
          <div style="font-size: 48px; font-weight: bold; color: #00d4ff; margin: 10px 0;">
            {{ report.financial_health_score.toFixed(1) }}
          </div>
          <div style="font-size: 14px; color: #aaa;">
            {{ getHealthScoreLevel(report.financial_health_score) }}
          </div>
        </div>

        <!-- 關鍵指標 -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px;">
          <div class="metric-card">
            <div class="metric-label">總收入</div>
            <div class="metric-value" style="color: #4ade80;">${{ report.total_income.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">總支出</div>
            <div class="metric-value" style="color: #f87171;">${{ report.total_expense.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">淨收入</div>
            <div class="metric-value" :style="{ color: report.net_income >= 0 ? '#00d4ff' : '#ff4444' }">
              ${{ report.net_income.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-label">儲蓄率</div>
            <div class="metric-value" :style="{ color: report.savings_rate >= 20 ? '#4ade80' : report.savings_rate >= 10 ? '#fbbf24' : '#f87171' }">
              {{ report.savings_rate.toFixed(1) }}%
            </div>
          </div>
        </div>

        <!-- 警示 -->
        <div v-if="report.alerts.length > 0" style="margin-bottom: 30px; padding: 15px; background: rgba(255, 68, 68, 0.1); border-left: 4px solid #ff4444; border-radius: 4px;">
          <h4 style="margin: 0 0 10px 0; color: #ff4444; display: flex; align-items: center; gap: 8px;">
            <span class="material-icons">warning</span>
            財務警示
          </h4>
          <ul style="margin: 0; padding-left: 20px;">
            <li v-for="(alert, index) in report.alerts" :key="index" style="margin: 5px 0; color: #ffaaaa;">
              {{ alert }}
            </li>
          </ul>
        </div>

        <!-- 財務數據 (Prompt格式) -->
        <div style="margin-bottom: 20px;">
          <h3 style="color: #00d4ff; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
            <span class="material-icons">smart_toy</span>
            分析提示詞
          </h3>
          <p style="color: #aaa; font-size: 14px; margin-bottom: 15px;">
            複製以下完整財務數據，貼給 ChatGPT、Claude 等 AI 助手，即可獲得專業的財務分析建議
          </p>
          <div style="position: relative;">
            <textarea
              ref="reportTextarea"
              :value="report.text_report"
              readonly
              style="width: 100%; height: 400px; padding: 15px; background: #1a1a1a; color: #fff; border: 1px solid #00d4ff; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 13px; resize: vertical;"
            ></textarea>
            <button
              @click="copyReport"
              style="position: absolute; top: 10px; right: 10px; padding: 8px 15px; background: #00d4ff; color: black; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; display: flex; align-items: center; gap: 5px;"
              :disabled="copied"
            >
              <span class="material-icons" style="font-size: 18px;">{{ copied ? 'check' : 'content_copy' }}</span>
              {{ copied ? '已複製' : '複製提示詞' }}
            </button>
          </div>
        </div>

        <!-- 操作按鈕 -->
        <div style="display: flex; gap: 10px; justify-content: flex-end;">
          <button
            @click="downloadReport"
            style="padding: 10px 20px; background: #8a2be2; color: white; border: none; border-radius: 4px; cursor: pointer;"
          >
            下載報告
          </button>
          <button
            @click="closeModal"
            style="padding: 10px 20px; background: #666; color: white; border: none; border-radius: 4px; cursor: pointer;"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import api from '@/services/api'
import type { AIFinancialSummary } from '@/types'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const report = ref<AIFinancialSummary | null>(null)
const loading = ref(false)
const error = ref('')
const copied = ref(false)
const reportTextarea = ref<HTMLTextAreaElement | null>(null)

// 默認日期範圍：最近30天
const today = new Date()
const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
const startDate = ref(thirtyDaysAgo.toISOString().split('T')[0])
const endDate = ref(today.toISOString().split('T')[0])

const closeModal = () => {
  emit('update:modelValue', false)
}

const getHealthScoreLevel = (score: number): string => {
  if (score >= 90) return '財務狀況優秀'
  if (score >= 70) return '財務狀況良好'
  if (score >= 50) return '財務狀況一般，需要注意'
  return '財務狀況較差，需要改善'
}

const generateReport = async () => {
  if (!startDate.value || !endDate.value) {
    error.value = '請選擇日期範圍'
    return
  }

  loading.value = true
  error.value = ''
  copied.value = false

  try {
    const response = await api.getAIFinancialSummary(startDate.value, endDate.value)
    report.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || '生成報告失敗'
  } finally {
    loading.value = false
  }
}

const copyReport = async () => {
  if (!report.value) return

  try {
    await navigator.clipboard.writeText(report.value.text_report)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
    // Fallback: select and copy
    if (reportTextarea.value) {
      reportTextarea.value.select()
      document.execCommand('copy')
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
    }
  }
}

const downloadReport = () => {
  if (!report.value) return

  const blob = new Blob([report.value.text_report], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `財務分析報告_${report.value.report_period_start}_${report.value.report_period_end}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// 監聽模態框打開，自動生成報告
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    // 重置狀態
    report.value = null
    error.value = ''
    copied.value = false
    // 自動生成報告
    generateReport()
  }
})
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
  position: relative;
  width: 90%;
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  color: #00d4ff;
  cursor: pointer;
  padding: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.3s;
}

.close-btn:hover {
  background: rgba(0, 212, 255, 0.2);
}

.metric-card {
  background: rgba(0, 212, 255, 0.1);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.3);
}

.metric-label {
  font-size: 12px;
  color: #aaa;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
}

/* Fix for date input icon visibility in dark mode */
.date-input::-webkit-calendar-picker-indicator {
    filter: invert(1);
    cursor: pointer;
}
</style>
