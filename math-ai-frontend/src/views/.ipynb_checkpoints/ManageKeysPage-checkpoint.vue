<template>
  <div class="keys-container">
    <h1>🔑 API密钥管理</h1>
    
    <!-- 操作提示 -->
    <div v-if="message" :class="['alert', messageType]">
      {{ message }}
    </div>

    <div class="keys-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else>
        <!-- 密钥列表渲染，严格匹配后端字段：api_key/created_at/last_used -->
        <div 
          v-for="key in keys" 
          :key="key.api_key" 
          class="key-item"
        >
          <div class="key-info">
            <div class="key-meta">
              <!-- 创建时间：使用后端返回的 created_at 字段 -->
              <span class="created">🗓️ {{ formatDate(key.created_at) }}</span>
              <!-- 最后使用时间：处理 null 情况 -->
              <span class="used">⏱️ {{ key.last_used ? formatDate(key.last_used) : '从未使用' }}</span>
            </div>
            <!-- 显示掩码后的 API 密钥 -->
            <div class="key-value">{{ maskKey(key.api_key) }}</div>
          </div>
          <div class="key-actions">
            <button 
              @click="copyKey(key.api_key)" 
              class="copy-btn"
            >
              <span>📋 复制</span>
            </button>
            <button 
              @click="deleteKey(key.api_key)" 
              class="delete-btn"
            >
              <span>🗑️ 删除</span>
            </button>
          </div>
        </div>
        <!-- 空状态提示 -->
        <div v-if="keys.length === 0" class="empty">尚未生成任何API密钥</div>
      </div>
    </div>

    <div class="key-operations">
      <button 
        @click="generateKey" 
        class="generate-btn"
      >
        🔄 生成新密钥
      </button>

      <!-- 临时密钥显示（60秒自动隐藏） -->
      <div v-if="tempKey" class="temp-key">
        <div class="temp-key-header">
          <span>新生成的密钥（{{ countdown }} 秒后自动隐藏）:</span>
          <button @click="hideTempKey" class="hide-btn">×</button>
        </div>
        <code 
          @click="copyKey(tempKey)" 
          class="key-content"
        >
          {{ tempKey }}
          <span class="copy-hint">点击复制</span>
        </code>
      </div>
    </div>

    <button 
      @click="router.push('/main')" 
      class="back-btn"
    >
      ← 返回主界面
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '@/utils/request'
import { API } from '@/api/config'

const router = useRouter()
const keys = ref([])
const tempKey = ref(null)
const tempKeyExpire = ref(0)
const message = ref('')
const messageType = ref('info')
const loading = ref(true)
const countdown = ref(0) // 倒计时显示

// 消息提示函数
const showMessage = (text, type = 'info', duration = 60000) => {
  message.value = text
  messageType.value = type
  if (duration) {
    setTimeout(() => message.value = '', duration)
  }
}

// 日期格式化（处理可能的 null/undefined）
const formatDate = (dateStr) => {
  if (!dateStr) return '从未使用' // 处理后端可能返回的 null
  try {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    console.error('日期解析错误:', dateStr, error)
    return '无效日期'
  }
}

// 密钥掩码
const maskKey = (key) => {
  if (!key || typeof key !== 'string') return '无效密钥'
  return `${key.slice(0, 8)}****${key.slice(-8)}`
}

// 加载密钥列表（核心函数）
const loadKeys = async () => {
  try {
    loading.value = true
    // 发送 GET 请求到 /api-keys
    const response = await apiRequest(API.API_KEYS) 
    console.log('[API响应] 密钥列表加载', response) // 关键调试日志
    
    // 确保后端返回的是 { data: [...] } 结构
    if (response.data && Array.isArray(response.data)) {
      keys.value = response.data
      console.log('[数据绑定] 密钥列表', keys.value)
    } else {
      throw new Error('无效的响应数据结构')
    }
  } catch (err) {
    showMessage(`加载失败: ${err.message}`, 'error')
    console.error('[错误] 加载密钥列表', err)
  } finally {
    loading.value = false
  }
}

// 生成新密钥
const generateKey = async () => {
  try {
    const response = await apiRequest(API.API_KEYS, 'POST', { action: 'create' })
    console.log('[API响应] 生成密钥', response)
    
    // 后端响应结构：{ status: 'success', data: { api_key: 'xxx' } }
    if (response.data && response.data.api_key) {
      tempKey.value = response.data.api_key
      tempKeyExpire.value = Date.now() + 60000 // 60秒后隐藏
      
      // 启动倒计时
      const timer = setInterval(() => {
        countdown.value = Math.max(0, Math.floor((tempKeyExpire.value - Date.now()) / 1000))
        if (countdown.value <= 0) {
          clearInterval(timer)
          tempKey.value = null
        }
      }, 1000)
      
      showMessage('新密钥生成成功！', 'success')
      await loadKeys() // 重新加载列表
    } else {
      throw new Error('未获取到有效密钥')
    }
  } catch (err) {
    showMessage(`生成失败: ${err.message}`, 'error')
    tempKey.value = null
  }
}

// 删除密钥
const deleteKey = async (apiKey) => {
  if (confirm('确定要永久删除此密钥吗？该操作不可撤销！')) {
    try {
      await apiRequest(API.API_KEYS, 'POST', { action: 'revoke', key: apiKey })
      showMessage('密钥已删除', 'success')
      await loadKeys()
    } catch (err) {
      showMessage(`删除失败: ${err.message}`, 'error')
    }
  }
}

// 隐藏临时密钥
const hideTempKey = () => {
  tempKey.value = null
}

// 复制密钥
const copyKey = async (apiKey) => {
  try {
    await navigator.clipboard.writeText(apiKey)
    showMessage('密钥已复制到剪贴板', 'success')
  } catch (err) {
    showMessage('复制失败，请手动选择复制', 'error')
  }
}

// 组件挂载时加载密钥列表
onMounted(() => {
  loadKeys()
})

// 监听临时密钥过期（辅助逻辑）
watch(tempKeyExpire, (newVal) => {
  if (newVal < Date.now()) {
    tempKey.value = null
  }
})
</script>

<style scoped>
/* 样式部分保持不变，以下是必要的基础样式（可根据实际调整） */
.keys-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.alert {
  padding: 1rem;
  margin: 1rem 0;
  border-radius: 6px;
}

.alert.success {
  background: #e6ffed;
  color: #2b8a3e;
}

.alert.error {
  background: #fff5f5;
  color: #c92a2a;
}

.key-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  margin: 1rem 0;
  background: #f8f9fa;
  border-radius: 8px;
  transition: transform 0.2s;
}

.key-item:hover {
  transform: translateY(-2px);
}

.key-meta {
  font-size: 0.9rem;
  color: #666;
}

.key-meta span {
  display: block;
  margin: 0.2rem 0;
}

.key-value {
  font-family: monospace;
  margin: 0.5rem 0;
  color: #333;
  word-break: break-all; /* 允许长密钥换行 */
}

.key-actions {
  display: flex;
  gap: 0.8rem;
}

button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn {
  background: #e7f5ff;
  color: #228be6;
}

.delete-btn {
  background: #fff5f5;
  color: #fa5252;
}

.generate-btn {
  background: #40c057;
  color: white;
  padding: 0.8rem 1.5rem;
  width: 100%;
  max-width: 300px;
}

.temp-key {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.key-content {
  display: block;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  font-family: monospace;
}

.copy-hint {
  position: absolute;
  right: 1rem;
  color: #868e96;
  font-size: 0.8rem;
}

.back-btn {
  margin-top: 2rem;
  width: 100%;
  background: #f1f3f5;
  padding: 0.8rem;
  border-radius: 6px;
  text-align: center;
}
</style>