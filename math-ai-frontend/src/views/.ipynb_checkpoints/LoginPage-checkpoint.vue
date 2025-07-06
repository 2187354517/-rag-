<template>
  <div class="auth-container">
    <!-- 替换为Canvas泡泡背景 -->
    <canvas ref="bubbleCanvas" class="bubble-canvas"></canvas>

    <!-- 动态背景装饰元素 -->
    <div class="decorate-circle"></div>
    <div class="decorate-blur"></div>

    <div class="auth-card">
      <!-- 标题部分 -->
      <div class="header">
        <h1>
          <span class="gradient-text">AI Assistant</span>
          <div class="animated-underline"></div>
        </h1>
        <p class="subtitle">开启您的智能之旅</p>
      </div>

      <!-- 选项卡切换 -->
      <div class="tabs">
        <button 
          @click="switchTab('login')" 
          :class="{ active: activeTab === 'login' }"
          class="tab-button"
        >
          <i class="icon icon-login"></i>
          用户登录
        </button>
        <div class="tab-divider">OR</div>
        <button 
          @click="switchTab('register')" 
          :class="{ active: activeTab === 'register' }"
          class="tab-button"
        >
          <i class="icon icon-register"></i>
          新用户注册
        </button>
      </div>

      <!-- 表单容器，添加3D翻转效果 -->
      <div class="flip-container" :class="{ 'flipped': activeTab === 'register' }">
        <div class="flip-inner">
          <!-- 登录表单 - 正面 -->
          <div class="flip-front">
            <form @submit.prevent="handleSubmit" v-show="activeTab === 'login'">
              <div class="input-group">
                <i class="icon icon-user"></i>
                <input 
                  v-model="loginForm.username"
                  placeholder=" "
                  :class="{ error: loginErrors.username }"
                >
                <label>用户名</label>
                <div class="input-border"></div>
              </div>
              <div class="error-message" v-if="loginErrors.username">⚠️ 请输入3-12位字母/数字组合</div>

              <div class="input-group">
                <i class="icon icon-lock"></i>
                <input 
                  v-model="loginForm.password"
                  type="password" 
                  placeholder=" "
                  :class="{ error: loginErrors.password }"
                >
                <label>密码</label>
                <div class="input-border"></div>
              </div>
              <div class="error-message" v-if="loginErrors.password">⚠️ 密码至少需要8位字符</div>

              <button type="submit" class="auth-btn" :disabled="loading">
                <i class="icon" :class="loading ? 'icon-loading' : 'icon-arrow'"></i>
                {{ loading ? '正在验证...' : '立即进入' }}
              </button>
            </form>
          </div>

          <!-- 注册表单 - 背面 -->
          <div class="flip-back">
            <form @submit.prevent="handleSubmit" v-show="activeTab === 'register'">
              <div class="input-group">
                <i class="icon icon-user"></i>
                <input 
                  v-model="registerForm.username"
                  placeholder=" "
                  :class="{ error: registerErrors.username }"
                >
                <label>用户名</label>
                <div class="input-border"></div>
              </div>
              <div class="error-message" v-if="registerErrors.username">⚠️ 3-12位字母/数字组合</div>

              <div class="input-group">
                <i class="icon icon-lock"></i>
                <input 
                  v-model="registerForm.password"
                  type="password" 
                  placeholder=" "
                  :class="{ error: registerErrors.password }"
                >
                <label>密码</label>
                <div class="input-border"></div>
              </div>
              <div class="error-message" v-if="registerErrors.password">⚠️ 至少8位字符</div>

              <div class="input-group">
                <i class="icon icon-email"></i>
                <input 
                  v-model="registerForm.email"
                  type="email"
                  placeholder=" "
                  :class="{ error: registerErrors.email }"
                >
                <label>电子邮箱</label>
                <div class="input-border"></div>
              </div>
              <div class="error-message" v-if="registerErrors.email">⚠️ 请输入有效邮箱地址</div>

              <button type="submit" class="auth-btn" :disabled="loading">
                <i class="icon" :class="loading ? 'icon-loading' : 'icon-rocket'"></i>
                {{ loading ? '正在创建...' : '立即启程' }}
              </button>
            </form>
          </div>
        </div>
      </div>

      <!-- 全局错误提示 -->
      <transition name="bounce">
        <div v-if="error" class="global-error">
          <i class="icon icon-warning"></i>
          {{ error }}
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { API } from '@/api/config'
import { apiRequest } from '@/utils/request'

const router = useRouter()
const activeTab = ref('login')
const bubbleCanvas = ref(null)

// 登录表单数据及验证
const loginForm = ref({
  username: '',
  password: ''
})
const loginErrors = ref({
  username: false,
  password: false
})

// 注册表单数据及验证
const registerForm = ref({
  username: '',
  password: '',
  email: ''
})
const registerErrors = ref({
  username: false,
  password: false,
  email: false
})

const error = ref('')
const loading = ref(false)

// 泡泡配置
const bubbleConfig = {
  count: 10,
  minSize: 10,
  maxSize: 28,
  minSpeed: 0.2,
  maxSpeed: 1.2,
  minOpacity: 0.2,
  maxOpacity: 0.5,
  blur: 1,
  color: '255, 255, 255'
}

let bubbles = []
let animationFrameId = null

// 泡泡类
class Bubble {
  constructor(canvasWidth, canvasHeight) {
    this.size = Math.random() * (bubbleConfig.maxSize - bubbleConfig.minSize) + bubbleConfig.minSize
    this.x = Math.random() * canvasWidth
    this.y = canvasHeight + this.size
    this.speedY = Math.random() * (bubbleConfig.maxSpeed - bubbleConfig.minSpeed) + bubbleConfig.minSpeed
    this.speedX = (Math.random() - 0.5) * 1.5
    this.opacity = Math.random() * (bubbleConfig.maxOpacity - bubbleConfig.minOpacity) + bubbleConfig.minOpacity
    this.angle = Math.random() * Math.PI * 2
    this.angleSpeed = (Math.random() - 0.5) * 0.1
  }

  update(canvasWidth, canvasHeight) {
    this.y -= this.speedY
    this.x += this.speedX
    this.angle += this.angleSpeed
    this.x += Math.sin(this.angle) * 0.5
    
    if (this.y < -this.size * 2) {
      this.reset(canvasWidth, canvasHeight)
    }
    
    if (this.x < -this.size) {
      this.x = canvasWidth + this.size
    } else if (this.x > canvasWidth + this.size) {
      this.x = -this.size
    }
  }

  reset(canvasWidth, canvasHeight) {
    this.y = canvasHeight + this.size
    this.x = Math.random() * canvasWidth
    this.speedY = Math.random() * (bubbleConfig.maxSpeed - bubbleConfig.minSpeed) + bubbleConfig.minSpeed
    this.opacity = Math.random() * (bubbleConfig.maxOpacity - bubbleConfig.minOpacity) + bubbleConfig.minOpacity
  }

  draw(ctx) {
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${bubbleConfig.color}, ${this.opacity})`
    ctx.filter = `blur(${bubbleConfig.blur}px)`
    ctx.fill()
    ctx.closePath()
  }
}

// 初始化泡泡
const initBubbles = (canvas) => {
  bubbles = []
  for (let i = 0; i < bubbleConfig.count; i++) {
    bubbles.push(new Bubble(canvas.width, canvas.height))
  }
}

// 动画循环
const animate = (canvas, ctx) => {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  bubbles.forEach(bubble => {
    bubble.update(canvas.width, canvas.height)
    bubble.draw(ctx)
  })
  
  animationFrameId = requestAnimationFrame(() => animate(canvas, ctx))
}

// 处理窗口大小变化
const handleResize = (canvas) => {
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
  initBubbles(canvas)
}

// 组件挂载时初始化Canvas
onMounted(() => {
  const canvas = bubbleCanvas.value
  const ctx = canvas.getContext('2d')
  
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
  
  initBubbles(canvas)
  animate(canvas, ctx)
  
  window.addEventListener('resize', () => handleResize(canvas))
})

// 组件卸载时清理
onUnmounted(() => {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
  window.removeEventListener('resize', handleResize)
})

// 切换选项卡
const switchTab = (tab) => {
  if (activeTab.value !== tab) {
    activeTab.value = tab
  }
}

// 表单提交处理
const handleSubmit = async () => {
  resetErrors()
  
  if (activeTab.value === 'login') {
    if (!validateUsername(loginForm.value.username)) {
      loginErrors.value.username = true
      return
    }
    if (!validatePassword(loginForm.value.password)) {
      loginErrors.value.password = true
      return
    }
  } else {
    if (!validateUsername(registerForm.value.username)) {
      registerErrors.value.username = true
      return
    }
    if (!validatePassword(registerForm.value.password)) {
      registerErrors.value.password = true
      return
    }
    if (!validateEmail(registerForm.value.email)) {
      registerErrors.value.email = true
      return
    }
  }

  loading.value = true
  error.value = ''

  try {
    const endpoint = activeTab.value === 'login' ? API.AUTH : API.REGISTER
    const formData = activeTab.value === 'login' ? loginForm.value : registerForm.value
    
    const response = await apiRequest(endpoint, 'POST', formData)
    
    localStorage.setItem('token', response.access_token)
    localStorage.setItem('userId', response.user_id)
    localStorage.setItem('apiKey', response.api_key)
    
    if (activeTab.value === 'login') {
      loginForm.value = { username: '', password: '' }
    } else {
      registerForm.value = { username: '', password: '', email: '' }
    }
    
    router.push('/main')
  } catch (err) {
    error.value = err.message || '操作失败，请检查网络或重试'
    console.error('认证错误:', err)
  } finally {
    loading.value = false
  }
}

// 验证函数
const validateUsername = (username) => /^[a-zA-Z0-9_]{3,12}$/.test(username)
const validatePassword = (password) => password.length >= 8
const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

// 重置错误状态
const resetErrors = () => {
  if (activeTab.value === 'login') {
    loginErrors.value = { username: false, password: false }
  } else {
    registerErrors.value = { username: false, password: false, email: false }
  }
}

// 监听tab切换
watch(activeTab, () => {
  loginForm.value = { username: '', password: '' }
  registerForm.value = { username: '', password: '', email: '' }
  resetErrors()
  error.value = ''
})
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.bubble-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}

.decorate-circle {
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(rgba(255,255,255,0.1), transparent);
  border-radius: 50%;
  top: -20%;
  right: -10%;
  animation: float 12s infinite;
}

.decorate-blur {
  position: absolute;
  z-index:0;
  width: 100%;
  height: 100%;
  backdrop-filter: blur(40px);
}

.auth-card {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  padding: 2.5rem;
  border-radius: 20px;
  width: 420px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.2);
  z-index: 2;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.gradient-text {
  background: linear-gradient(45deg, #4f46e5, #ec4899);
  -webkit-background-clip: text;
  color: transparent;
  font-size: 2.2rem;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin-top: 0.5rem;
}

.tabs {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.tab-button {
  flex: 1;
  padding: 1rem;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: 500;
  color: #6b7280;
  transition: all 0.3s;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.tab-button.active {
  color: #4f46e5;
  font-weight: 600;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  width: 100%;
  height: 3px;
  background: #4f46e5;
  border-radius: 2px;
}

.tab-divider {
  color: #9ca3af;
  font-size: 0.9rem;
}

.flip-container {
  perspective: 1000px;
  height: 350px;
  position: relative;
}

.flip-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.8s;
  transform-style: preserve-3d;
}

.flip-container.flipped .flip-inner {
  transform: rotateY(180deg);
}

.flip-front, .flip-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.flip-back {
  transform: rotateY(180deg);
}

.input-group {
  position: relative;
  margin-bottom: 1.5rem;
}

.input-group input {
  width: 90%;
  padding: 1rem;
  border: none;
  border-bottom: 2px solid #e5e7eb;
  background: rgba(255,255,255,0.8);
  transition: all 0.3s;
}

.input-group input:focus {
  outline: none;
  border-bottom-color: #4f46e5;
}

.input-group label {
  position: absolute;
  left: 2rem;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  transition: all 0.3s;
  pointer-events: none;
}

.input-group input:focus ~ label,
.input-group input:not(:placeholder-shown) ~ label {
  top: -10px;
  left: 1rem;
  font-size: 0.8rem;
  color: #4f46e5;
}

.input-border {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: #4f46e5;
  transition: width 0.3s;
}

.input-group input:focus ~ .input-border {
  width: 100%;
}

.auth-btn {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(45deg, #4f46e5, #6366f1);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.auth-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79,70,229,0.3);
}

.icon {
  font-size: 1.2rem;
}

.icon-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

.bounce-enter-active {
  animation: bounce-in 0.5s;
}

@keyframes bounce-in {
  0% { transform: scale(0); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}
</style>