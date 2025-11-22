<template>
  <div v-if="show" class="calculator-overlay" @click.self="handleClose">
    <div class="calculator">
      <div class="calculator-display">
        <div class="calculator-expression">{{ displayExpression }}</div>
        <div class="calculator-result">{{ displayValue }}</div>
      </div>
      <div class="calculator-buttons">
        <button @click="clear" class="calc-btn calc-btn-clear">C</button>
        <button @click="backspace" class="calc-btn calc-btn-operator">←</button>
        <button @click="appendOperator('/')" class="calc-btn calc-btn-operator">÷</button>
        <button @click="appendOperator('*')" class="calc-btn calc-btn-operator">×</button>

        <button @click="appendNumber('7')" class="calc-btn">7</button>
        <button @click="appendNumber('8')" class="calc-btn">8</button>
        <button @click="appendNumber('9')" class="calc-btn">9</button>
        <button @click="appendOperator('-')" class="calc-btn calc-btn-operator">−</button>

        <button @click="appendNumber('4')" class="calc-btn">4</button>
        <button @click="appendNumber('5')" class="calc-btn">5</button>
        <button @click="appendNumber('6')" class="calc-btn">6</button>
        <button @click="appendOperator('+')" class="calc-btn calc-btn-operator">+</button>

        <button @click="appendNumber('1')" class="calc-btn">1</button>
        <button @click="appendNumber('2')" class="calc-btn">2</button>
        <button @click="appendNumber('3')" class="calc-btn">3</button>
        <button @click="calculate" class="calc-btn calc-btn-equal" style="grid-row: span 2;">=</button>

        <button @click="appendNumber('0')" class="calc-btn" style="grid-column: span 2;">0</button>
        <button @click="appendDecimal" class="calc-btn">.</button>
      </div>
      <div class="calculator-actions">
        <button @click="handleConfirm" class="btn btn-primary" style="flex: 1;">確認</button>
        <button @click="handleClose" class="btn btn-secondary" style="flex: 1;">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

interface Props {
  modelValue: boolean
  initialValue?: number
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', value: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const show = ref(props.modelValue)
const expression = ref('')
const currentValue = ref('0')
const lastOperator = ref('')
const waitingForOperand = ref(false)

watch(() => props.modelValue, (newVal) => {
  show.value = newVal
  if (newVal && props.initialValue !== undefined && props.initialValue > 0) {
    currentValue.value = props.initialValue.toString()
    expression.value = props.initialValue.toString()
  } else if (newVal) {
    clear()
  }
})

const displayExpression = ref('')
const displayValue = ref('0')

watch([expression, currentValue], () => {
  displayExpression.value = expression.value || '0'
  displayValue.value = currentValue.value || '0'
})

const appendNumber = (num: string) => {
  if (waitingForOperand.value) {
    currentValue.value = num
    waitingForOperand.value = false
  } else {
    currentValue.value = currentValue.value === '0' ? num : currentValue.value + num
  }
}

const appendDecimal = () => {
  if (waitingForOperand.value) {
    currentValue.value = '0.'
    waitingForOperand.value = false
  } else if (!currentValue.value.includes('.')) {
    currentValue.value += '.'
  }
}

const appendOperator = (op: string) => {
  const value = parseFloat(currentValue.value)

  if (expression.value && !waitingForOperand.value) {
    calculate()
  }

  expression.value = currentValue.value + ' ' + op + ' '
  lastOperator.value = op
  waitingForOperand.value = true
}

const calculate = () => {
  if (!expression.value || !lastOperator.value) {
    return
  }

  try {
    const parts = expression.value.trim().split(' ')
    const leftOperand = parseFloat(parts[0])
    const operator = parts[1]
    const rightOperand = parseFloat(currentValue.value)

    let result = 0
    switch (operator) {
      case '+':
        result = leftOperand + rightOperand
        break
      case '-':
        result = leftOperand - rightOperand
        break
      case '*':
        result = leftOperand * rightOperand
        break
      case '/':
        if (rightOperand === 0) {
          currentValue.value = 'Error'
          expression.value = ''
          return
        }
        result = leftOperand / rightOperand
        break
    }

    // 保留最多 2 位小數
    currentValue.value = Math.round(result * 100) / 100 + ''
    expression.value = ''
    lastOperator.value = ''
    waitingForOperand.value = false
  } catch (error) {
    currentValue.value = 'Error'
    expression.value = ''
  }
}

const clear = () => {
  currentValue.value = '0'
  expression.value = ''
  lastOperator.value = ''
  waitingForOperand.value = false
}

const backspace = () => {
  if (currentValue.value.length > 1) {
    currentValue.value = currentValue.value.slice(0, -1)
  } else {
    currentValue.value = '0'
  }
}

const handleConfirm = () => {
  // 如果有未完成的計算，先完成它
  if (expression.value && !waitingForOperand.value) {
    calculate()
  }

  const value = parseFloat(currentValue.value)
  if (!isNaN(value) && value >= 0) {
    emit('confirm', value)
    emit('update:modelValue', false)
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (!show.value) return

  // Prevent default action for calculator keys to avoid side effects (like scrolling)
  if (['+', '-', '*', '/', 'Enter', 'Escape', 'Backspace'].includes(e.key)) {
    e.preventDefault()
  }

  // Numbers
  if (/^[0-9]$/.test(e.key)) {
    appendNumber(e.key)
    return
  }

  // Operators
  switch (e.key) {
    case '+':
      appendOperator('+')
      break
    case '-':
      appendOperator('-')
      break
    case '*':
      appendOperator('*')
      break
    case '/':
      appendOperator('/')
      break
    case '.':
      appendDecimal()
      break
    case 'Enter':
    case '=':
      // If Shift+Enter or just Enter, we might want different behavior?
      // Standard calculator: Enter = Calculate/Equal
      // But user might want Enter to Confirm if calculation is done.
      // Let's stick to: Enter = Calculate if expression exists, otherwise Confirm
      if (expression.value && !waitingForOperand.value) {
        calculate()
      } else {
        handleConfirm()
      }
      break
    case 'Escape':
      handleClose()
      break
    case 'Backspace':
      backspace()
      break
    case 'Delete':
      clear()
      break
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.calculator-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.calculator {
  background: linear-gradient(135deg, #1a1f3a 0%, #2d3561 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  max-width: 320px;
  width: 100%;
}

.calculator-display {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  text-align: right;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 5px;
}

.calculator-expression {
  color: #a0aec0;
  font-size: 14px;
  min-height: 20px;
}

.calculator-result {
  color: #00d4ff;
  font-size: 32px;
  font-weight: bold;
  word-break: break-all;
}

.calculator-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.calc-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: #e0e6ed;
  font-size: 20px;
  padding: 18px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.calc-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(0, 212, 255, 0.4);
  transform: translateY(-2px);
}

.calc-btn:active {
  transform: translateY(0);
}

.calc-btn-operator {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.4);
  color: #00d4ff;
}

.calc-btn-operator:hover {
  background: rgba(0, 212, 255, 0.3);
}

.calc-btn-clear {
  background: rgba(255, 107, 107, 0.2);
  border-color: rgba(255, 107, 107, 0.4);
  color: #ff6b6b;
}

.calc-btn-clear:hover {
  background: rgba(255, 107, 107, 0.3);
}

.calc-btn-equal {
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  border-color: #00d4ff;
  color: white;
  font-size: 24px;
}

.calc-btn-equal:hover {
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
}

.calculator-actions {
  display: flex;
  gap: 10px;
}
</style>
