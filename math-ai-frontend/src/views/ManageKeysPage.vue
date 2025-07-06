<template>
  <div class="keys-container">
    <!-- 顶部标题和操作区 -->
    <div class="header-section">
      <div class="title-group">
        <h1 class="page-title">
          <el-icon class="title-icon"><Key /></el-icon>
          API密钥管理
        </h1>
        <p class="page-subtitle">管理您的应用程序访问密钥</p>
      </div>
      
      <el-button 
        type="primary" 
        @click="generateKey" 
        :icon="Refresh" 
        class="generate-btn"
      >
        生成新密钥
      </el-button>
    </div>

    <!-- 消息提示 -->
    <el-alert 
      v-if="message" 
      :title="message" 
      :type="messageType" 
      show-icon 
      closable
      class="message-alert"
    />

    <!-- 密钥列表 -->
    <el-card class="keys-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">我的密钥</span>
          <el-button 
            type="text" 
            :icon="Refresh" 
            @click="loadKeys" 
            :loading="loading"
          >
            刷新列表
          </el-button>
        </div>
      </template>

      <el-empty v-if="!loading && keys.length === 0" description="暂无API密钥">
        <el-button type="primary" @click="generateKey">立即创建</el-button>
      </el-empty>

      <div v-loading="loading" class="keys-list">
        <div 
          v-for="key in keys" 
          :key="key.api_key" 
          class="key-item"
        >
          <div class="key-content">
            <div class="key-meta">
              <div class="key-dates">
                <div class="date-item">
                  <el-icon><Calendar /></el-icon>
                  <span>创建时间: {{ formatDate(key.created_at) }}</span>
                </div>
                <div class="date-item">
                  <el-icon><Clock /></el-icon>
                  <span>最后使用: {{ key.last_used ? formatDate(key.last_used) : '从未使用' }}</span>
                </div>
              </div>
              
              <div class="key-status">
                <el-tag v-if="key.last_used" type="warning">正在使用</el-tag>
                <el-tag v-else type="info">未使用</el-tag>
              </div>
              
              <div class="key-value">
                <el-tag type="info" class="key-prefix">{{ key.api_key.slice(0, 8) }}</el-tag>
                <span class="key-mask">••••••••</span>
                <el-tag type="info" class="key-suffix">{{ key.api_key.slice(-8) }}</el-tag>
              </div>
            </div>

            <div class="key-actions">
              <el-tooltip content="复制密钥" placement="top">
                <el-button 
                  @click="copyKey(key.api_key)" 
                  :icon="DocumentCopy" 
                  circle 
                  plain
                />
              </el-tooltip>
              
              <el-popconfirm 
                width="200px"
                title="确定要删除此密钥吗？" 
                confirm-button-text="确认" 
                cancel-button-text="取消"
                @confirm="deleteKey(key.api_key)"
              >
                <template #reference>
                  <el-button 
                    :icon="Delete" 
                    circle 
                    plain 
                    type="danger"
                  />
                </template>
              </el-popconfirm>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 新密钥弹窗 -->
    <el-dialog 
      v-model="tempKeyVisible" 
      :title="`新API密钥生成成功`" 
      width="600px"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <div class="new-key-dialog">
        <el-alert 
          title="请立即保存此密钥，关闭后将无法再次查看" 
          type="warning" 
          show-icon 
          class="key-alert"
        />
        
        <div class="key-display">
          <div class="key-timer">
            <el-icon><Timer /></el-icon>
            <span>自动隐藏倒计时: {{ countdown }}秒</span>
          </div>
          
          <el-input 
            v-model="tempKey" 
            readonly 
            class="key-input"
            @click="copyKey(tempKey)"
          >
            <template #append>
              <el-button 
                @click="copyKey(tempKey)" 
                :icon="DocumentCopy"
              >
                复制
              </el-button>
            </template>
          </el-input>
        </div>
        
        <div class="dialog-footer">
          <el-button 
            type="primary" 
            @click="hideTempKey" 
            class="confirm-btn"
          >
            我已保存
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 返回按钮 -->
    <el-button 
      @click="router.push('/login')" 
      class="back-btn"
      :icon="ArrowLeft"
    >
      退出登录
    </el-button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '@/utils/request'
import { API } from '@/api/config'
import {
  Key,
  Refresh,
  DocumentCopy,
  Delete,
  Calendar,
  Clock,
  Timer,
  ArrowLeft
} from '@element-plus/icons-vue'

const router = useRouter()
const keys = ref([])
const tempKey = ref('')
const tempKeyVisible = ref(false)
const countdown = ref(15)
const message = ref('')
const messageType = ref('info')
const loading = ref(true)

// 消息提示
const showMessage = (text, type = 'info', duration = 5000) => {
  message.value = text
  messageType.value = type
  if (duration) {
    setTimeout(() => message.value = '', duration)
  }
}

// 日期格式化
const formatDate = (dateStr) => {
  if (!dateStr) return '从未使用'
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

// 加载密钥列表
const loadKeys = async () => {
  try {
    loading.value = true
    const response = await apiRequest(API.API_KEYS) 
    
    if (response.data && Array.isArray(response.data)) {
      keys.value = response.data
    } else {
      throw new Error('无效的响应数据结构')
    }
  } catch (err) {
    showMessage(`加载失败: ${err.message}`, 'error')
    console.error('加载密钥列表错误:', err)
  } finally {
    loading.value = false
  }
}

// 生成新密钥
const generateKey = async () => {
  try {
    const response = await apiRequest(API.API_KEYS, 'POST', { action: 'create' })
    
    if (response.data && response.data.api_key) {
      tempKey.value = response.data.api_key
      tempKeyVisible.value = true
      countdown.value = 60
      
      // 启动倒计时
      const timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          clearInterval(timer)
          tempKeyVisible.value = false
        }
      }, 1000)
      
      showMessage('新密钥生成成功！', 'success')
      await loadKeys()
    } else {
      throw new Error('未获取到有效密钥')
    }
  } catch (err) {
    showMessage(`生成失败: ${err.message}`, 'error')
    tempKeyVisible.value = false
  }
}

// 删除密钥
// 删除密钥
const deleteKey = async (apiKey) => {
  try {
    // 查找密钥是否正在使用
    const keyToRevoke = keys.value.find(key => key.api_key === apiKey);
    if (!keyToRevoke) {
      throw new Error('密钥不存在');
    }

    // 检查密钥是否正在使用（例如：最近半小时内有使用记录）
    if (keyToRevoke.last_used) {
      const lastUsedDate = new Date(keyToRevoke.last_used);
      const now = new Date();
      const diffHours = (now - lastUsedDate) / (1000 * 60 * 60);

      if (diffHours < 0.5) { // 如果最近24小时内有使用，则不允许删除
        showMessage('无法删除正在使用的密钥', 'error');
        return;
      }
    }

    // 如果通过了检查，继续删除操作
    await apiRequest(API.API_KEYS, 'POST', { action: 'revoke', key: apiKey });
    showMessage('密钥已删除', 'success');
    await loadKeys();
  } catch (err) {
    showMessage(`删除失败: ${err.message}`, 'error');
  }
};

// 隐藏临时密钥
const hideTempKey = () => {
  tempKeyVisible.value = false
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
</script>

<style scoped lang="scss">
.keys-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .title-group {
    .page-title {
      display: flex;
      align-items: center;
      font-size: 24px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0 0 8px 0;
      
      .title-icon {
        margin-right: 12px;
        font-size: 28px;
        color: var(--el-color-primary);
      }
    }
    
    .page-subtitle {
      margin: 0;
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }
  
  .generate-btn {
    height: 40px;
  }
}

.message-alert {
  margin-bottom: 24px;
}

.keys-card {
  border-radius: 8px;
  margin-bottom: 24px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .card-title {
      font-size: 16px;
      font-weight: 600;
    }
  }
}

.keys-list {
  .key-item {
    padding: 16px;
    border-radius: 6px;
    background-color: var(--el-fill-color-light);
    margin-bottom: 12px;
    transition: all 0.3s;
    
    &:hover {
      background-color: var(--el-fill-color);
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    }
    
    .key-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .key-meta {
      flex: 1;
      
      .key-dates {
        display: flex;
        gap: 16px;
        margin-bottom: 12px;
        font-size: 13px;
        color: var(--el-text-color-secondary);
        .key-status {
          align-self: flex-end;
          }
        .date-item {
          display: flex;
          align-items: center;
          
          .el-icon {
            margin-right: 6px;
            font-size: 14px;
          }
        }
      }
      
      .key-value {
        display: flex;
        align-items: center;
        font-family: 'Roboto Mono', monospace;
        
        .key-prefix, .key-suffix {
          font-family: inherit;
          letter-spacing: 1px;
        }
        
        .key-mask {
          margin: 0 4px;
          letter-spacing: 2px;
        }
      }
    }
    
    .key-actions {
      display: flex;
      gap: 8px;
    }
  }
}

.new-key-dialog {
  .key-alert {
    margin-bottom: 20px;
  }
  
  .key-display {
    .key-timer {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      font-size: 14px;
      color: var(--el-text-color-secondary);
      
      .el-icon {
        margin-right: 6px;
        color: var(--el-color-warning);
      }
    }
    
    .key-input {
      font-family: 'Roboto Mono', monospace;
      font-size: 14px;
      cursor: pointer;
      
      :deep(.el-input__inner) {
        letter-spacing: 0.5px;
      }
    }
  }
  
  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    margin-top: 24px;
    
    .confirm-btn {
      width: 120px;
    }
  }
}

.back-btn {
  width: 100%;
  margin-top: 16px;
}
</style>