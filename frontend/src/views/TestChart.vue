<template>
  <div class="test-chart">
    <h1>ECharts 測試頁面</h1>
    <div ref="chartContainer" style="width: 600px; height: 400px; border: 1px solid #00d4ff;"></div>
    <p style="margin-top: 20px; color: #fff;">如果看到圓餅圖,說明 ECharts 工作正常</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const chartContainer = ref<HTMLElement | null>(null)

onMounted(() => {
  if (!chartContainer.value) {
    console.error('Chart container not found!')
    return
  }

  console.log('Initializing ECharts...')
  const chart = echarts.init(chartContainer.value)

  const option = {
    title: {
      text: '測試圓餅圖',
      left: 'center',
      textStyle: {
        color: '#fff'
      }
    },
    tooltip: {
      trigger: 'item'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: 335, name: '類別A' },
          { value: 234, name: '類別B' },
          { value: 154, name: '類別C' }
        ]
      }
    ]
  }

  chart.setOption(option)
  console.log('ECharts initialized successfully!')
})
</script>

<style scoped>
.test-chart {
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

h1 {
  color: #00d4ff;
  margin-bottom: 30px;
}
</style>
