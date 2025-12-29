<template>
  <div class="budget-report">
    <!-- Summary Cards -->
    <div class="stats-grid">
      <div class="stat-card budget">
        <h3>總預算</h3>
        <p class="amount">{{ formatCurrency(stats.total_budget) }}</p>
      </div>
      
      <div class="stat-card expense">
        <h3>已使用</h3>
        <p class="amount">{{ formatCurrency(stats.total_spent) }}</p>
      </div>
      
      <div class="stat-card remaining" :class="stats.remaining >= 0 ? 'positive' : 'negative'">
        <h3>剩餘預算</h3>
        <p class="amount">{{ formatCurrency(stats.remaining) }}</p>
      </div>
      
      <div class="stat-card average">
        <h3>平均每日花費</h3>
        <p class="amount">{{ formatCurrency(stats.daily_average) }}</p>
      </div>
    </div>

    <!-- Budget Usage Progress -->
    <div class="card usage-card" v-if="stats.total_budget > 0">
      <div class="card-header">
        <h2>預算使用率</h2>
        <span :class="['status-badge', stats.status]">{{ getStatusText(stats.status) }}</span>
      </div>
      
      <div class="progress-container">
        <div class="progress-bar-bg">
          <div 
            class="progress-bar-fill"
            :class="stats.status"
            :style="{ width: Math.min((stats.total_spent / stats.total_budget) * 100, 100) + '%' }"
          >
            <div class="progress-glow"></div>
          </div>
        </div>
        <div class="progress-labels">
          <span>0%</span>
          <span class="current-percent">{{ Math.round((stats.total_spent / stats.total_budget) * 100) }}%</span>
        </div>
      </div>
    </div>

    <!-- Transactions List -->
    <div class="card transactions-card">
      <div class="card-header">
        <h2>預算內交易明細</h2>
      </div>
      
      <div class="transactions-list">
        <div v-if="transactions.length === 0" class="empty-message">
          此期間無相關交易
        </div>
        
        <div v-else class="table-container">
          <table class="transactions-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>類別</th>
                <th>描述</th>
                <th>帳戶</th>
                <th class="text-right">金額</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in transactions" :key="t.id">
                <td class="date-cell">{{ formatDate(t.transaction_date) }}</td>
                <td>
                  <span class="category-tag">{{ t.category || '未分類' }}</span>
                </td>
                <td class="description-cell">{{ t.description }}</td>
                <td class="account-cell">{{ t.account_name }}</td>
                <td class="amount-cell text-right">{{ formatCurrency(t.amount) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import { formatAmount } from '@/utils/format';

const props = defineProps({
  stats: {
    type: Object,
    required: true,
    default: () => ({
      total_budget: 0,
      total_spent: 0,
      remaining: 0,
      daily_average: 0,
      status: 'on_track'
    })
  },
  transactions: {
    type: Array,
    required: true,
    default: () => []
  }
});

const formatCurrency = (value) => {
  return formatAmount(value);
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

const getStatusText = (status) => {
  switch (status) {
    case 'over_budget': return '超支';
    case 'warning': return '預警';
    default: return '正常';
  }
};
</script>

<style scoped>
.budget-report {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.stat-card {
  padding: 25px;
  border-radius: 12px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.stat-card h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #a0aec0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.stat-card .amount {
  margin: 0;
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

/* Card Variants */
.stat-card.budget {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
  border-color: rgba(255, 255, 255, 0.1);
}

.stat-card.expense {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 107, 107, 0.05) 100%);
  border-color: rgba(255, 107, 107, 0.3);
}
.stat-card.expense .amount { color: #ff6b6b; }

.stat-card.remaining.positive {
  background: linear-gradient(135deg, rgba(81, 207, 102, 0.1) 0%, rgba(81, 207, 102, 0.05) 100%);
  border-color: rgba(81, 207, 102, 0.3);
}
.stat-card.remaining.positive .amount { color: #51cf66; }

.stat-card.remaining.negative {
  background: linear-gradient(135deg, rgba(255, 107, 107, 0.1) 0%, rgba(255, 107, 107, 0.05) 100%);
  border-color: rgba(255, 107, 107, 0.3);
}
.stat-card.remaining.negative .amount { color: #ff6b6b; }

.stat-card.average {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%);
  border-color: rgba(0, 212, 255, 0.3);
}
.stat-card.average .amount { color: #00d4ff; }

/* General Card Style */
.card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.1);
  padding: 25px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  color: #fff;
  font-weight: 600;
}

/* Status Badge */
.status-badge {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-badge.on_track {
  background: rgba(81, 207, 102, 0.2);
  color: #51cf66;
  border: 1px solid rgba(81, 207, 102, 0.4);
}

.status-badge.warning {
  background: rgba(255, 204, 0, 0.2);
  color: #ffcc00;
  border: 1px solid rgba(255, 204, 0, 0.4);
}

.status-badge.over_budget {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border: 1px solid rgba(255, 107, 107, 0.4);
}

/* Progress Bar */
.progress-container {
  margin-top: 10px;
}

.progress-bar-bg {
  width: 100%;
  height: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 6px;
  position: relative;
  transition: width 1s ease-out;
}

.progress-bar-fill.on_track { background: #51cf66; box-shadow: 0 0 10px rgba(81, 207, 102, 0.5); }
.progress-bar-fill.warning { background: #ffcc00; box-shadow: 0 0 10px rgba(255, 204, 0, 0.5); }
.progress-bar-fill.over_budget { background: #ff6b6b; box-shadow: 0 0 10px rgba(255, 107, 107, 0.5); }

.progress-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0) 100%);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 14px;
  color: #a0aec0;
}

.current-percent {
  color: #fff;
  font-weight: bold;
}

/* Transactions Table */
.table-container {
  overflow-x: auto;
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
}

.transactions-table th {
  text-align: left;
  padding: 15px;
  color: #a0aec0;
  font-weight: 500;
  font-size: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.transactions-table td {
  padding: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: #fff;
  font-size: 15px;
}

.transactions-table tr:last-child td {
  border-bottom: none;
}

.transactions-table tr:hover td {
  background: rgba(255, 255, 255, 0.05);
}

.date-cell {
  color: #a0aec0 !important;
  font-size: 14px !important;
  white-space: nowrap;
}

.category-tag {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(0, 212, 255, 0.1);
  color: #00d4ff;
  border-radius: 12px;
  font-size: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.description-cell {
  font-weight: 500;
}

.account-cell {
  color: #a0aec0 !important;
  font-size: 14px !important;
}

.amount-cell {
  font-weight: bold;
  color: #ff6b6b !important;
  font-family: 'Roboto Mono', monospace;
}

.text-right {
  text-align: right;
}

.empty-message {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
  font-style: italic;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .transactions-table th, 
  .transactions-table td {
    padding: 10px;
  }
  
  .account-cell {
    display: none;
  }
}
</style>
