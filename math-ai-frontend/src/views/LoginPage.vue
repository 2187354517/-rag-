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
        <div class="title-container">
          <img src="@/assets/images/北极熊 logo1.png" alt="PolarSolve Logo" class="logo">
          <h1>
            <span class="gradient-text">PolarSolve</span>
            <div class="animated-underline"></div>
          </h1>
        </div>
        <p class="subtitle">开启您的数学极地之旅</p>
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
              <div class="form-group">
                <div class="input-group">
                  <i class="icon icon-user"></i>
                  <input 
                    v-model="loginForm.username"
                    placeholder=" "
                    :class="{ error: loginErrors.username }"
                    @input="validateUsernameOnInput('login')"
                  >
                  <label>用户名</label>
                  <div class="input-border"></div>
                </div>
                <div class="error-message" v-if="showUsernameError('login')">⚠️ 用户名请输入3-12位字母/数字组合</div>
              </div>

              <div class="form-group">
                <div class="input-group">
                  <i class="icon icon-lock"></i>
                  <input 
                    v-model="loginForm.password"
                    type="password" 
                    placeholder=" "
                    :class="{ error: loginErrors.password }"
                    @input="validatePasswordOnInput('login')"
                  >
                  <label>密码</label>
                  <div class="input-border"></div>
                </div>
                <div class="error-message" v-if="showPasswordError('login')">⚠️ 密码至少需要8位字符</div>
              </div>

              <button type="submit" class="auth-btn" :disabled="loading">
                <i class="icon" :class="loading ? 'icon-loading' : 'icon-arrow'"></i>
                {{ loading ? '正在验证...' : '立即进入' }}
              </button>
              
              <!-- 浮动全局错误提示 - 登录表单内 -->
              <transition name="fade">
                <div v-if="error && activeTab === 'login'" class="global-error floating-error">
                  <i class="icon icon-warning"></i>
                  {{ error }}
                </div>
              </transition>
            </form>
          </div>

          <!-- 注册表单 - 背面 -->
          <div class="flip-back">
            <form @submit.prevent="handleSubmit" v-show="activeTab === 'register'">
              <div class="form-group">
                <div class="input-group">
                  <i class="icon icon-user"></i>
                  <input 
                    v-model="registerForm.username"
                    placeholder=" "
                    :class="{ error: registerErrors.username }"
                    @input="validateUsernameOnInput('register')"
                  >
                  <label>用户名</label>
                  <div class="input-border"></div>
                </div>
                <div class="error-message" v-if="showUsernameError('register')">⚠️ 用户名3-12位字母/数字组合</div>
              </div>

              <div class="form-group">
                <div class="input-group">
                  <i class="icon icon-lock"></i>
                  <input 
                    v-model="registerForm.password"
                    type="password" 
                    placeholder=" "
                    :class="{ error: registerErrors.password }"
                    @input="validatePasswordOnInput('register')"
                  >
                  <label>密码</label>
                  <div class="input-border"></div>
                </div>
                <div class="error-message" v-if="showPasswordError('register')">⚠️ 密码至少需要8位字符</div>
              </div>

              <div class="form-group">
                <div class="input-group">
                  <i class="icon icon-email"></i>
                  <input 
                    v-model="registerForm.email"
                    type="email"
                    placeholder=" "
                    :class="{ error: registerErrors.email }"
                    @input="validateEmailOnInput('register')"
                  >
                  <label>电子邮箱</label>
                  <div class="input-border"></div>
                </div>
                <div class="error-message" v-if="showEmailError('register')">⚠️ 请输入有效邮箱地址</div>
              </div>

              <button type="submit" class="auth-btn" :disabled="loading">
                <i class="icon" :class="loading ? 'icon-loading' : 'icon-rocket'"></i>
                {{ loading ? '正在创建...' : '立即启程' }}
              </button>
              
              <!-- 浮动全局错误提示 - 注册表单内 -->
              <transition name="fade">
                <div v-if="error && activeTab === 'register'" class="global-error floating-error">
                  <i class="icon icon-warning"></i>
                  {{ error }}
                </div>
              </transition>
            </form>
          </div>
        </div>
      </div>
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
const showLoginUsernameError = ref(false)
const showLoginPasswordError = ref(false)

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
const showRegisterUsernameError = ref(false)
const showRegisterPasswordError = ref(false)
const showRegisterEmailError = ref(false)

const error = ref('')
const loading = ref(false)
let errorTimeout = null

// 泡泡配置 - 调整为蓝色调
const bubbleConfig = {
  count: 10,
  minSize: 10,
  maxSize: 28,
  minSpeed: 0.2,
  maxSpeed: 1.2,
  minOpacity: 0.2,
  maxOpacity: 0.5,
  blur: 1,
  color: '173, 216, 230' // 浅蓝色
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
  if (errorTimeout) {
    clearTimeout(errorTimeout)
  }
  window.removeEventListener('resize', handleResize)
})

// 切换选项卡
const switchTab = (tab) => {
  if (activeTab.value !== tab) {
    activeTab.value = tab
  }
}

// 用户名输入实时验证
const validateUsernameOnInput = (type) => {
  const username = type === 'login' ? loginForm.value.username : registerForm.value.username
  const isValid = validateUsername(username)
  
  if (type === 'login') {
    showLoginUsernameError.value = username.length > 0 && !isValid
  } else {
    showRegisterUsernameError.value = username.length > 0 && !isValid
  }
}

// 密码输入实时验证
const validatePasswordOnInput = (type) => {
  const password = type === 'login' ? loginForm.value.password : registerForm.value.password
  const isValid = validatePassword(password)
  
  if (type === 'login') {
    showLoginPasswordError.value = password.length > 0 && !isValid
  } else {
    showRegisterPasswordError.value = password.length > 0 && !isValid
  }
}

// 邮箱输入实时验证
const validateEmailOnInput = () => {
  const email = registerForm.value.email
  const isValid = validateEmail(email)
  showRegisterEmailError.value = email.length > 0 && !isValid
}

// 显示用户名错误
const showUsernameError = (type) => {
  return type === 'login' ? showLoginUsernameError.value : showRegisterUsernameError.value
}

// 显示密码错误
const showPasswordError = (type) => {
  return type === 'login' ? showLoginPasswordError.value : showRegisterPasswordError.value
}

// 显示邮箱错误
const showEmailError = () => {
  return showRegisterEmailError.value
}

// 表单提交处理
const handleSubmit = async () => {
  resetErrors()
  
  // 先进行本地验证
  if (activeTab.value === 'login') {
    if (!validateUsername(loginForm.value.username)) {
      loginErrors.value.username = true
      showLoginUsernameError.value = true
      return
    }
    if (!validatePassword(loginForm.value.password)) {
      loginErrors.value.password = true
      showLoginPasswordError.value = true
      return
    }
  } else {
    if (!validateUsername(registerForm.value.username)) {
      registerErrors.value.username = true
      showRegisterUsernameError.value = true
      return
    }
    if (!validatePassword(registerForm.value.password)) {
      registerErrors.value.password = true
      showRegisterPasswordError.value = true
      return
    }
    if (!validateEmail(registerForm.value.email)) {
      registerErrors.value.email = true
      showRegisterEmailError.value = true
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
    // 登录失败时清空输入框
    if (activeTab.value === 'login') {
      loginForm.value = { username: '', password: '' }
    }
    error.value = '用户名或密码错误'
    
    // 3秒后自动清除错误提示
    if (errorTimeout) {
      clearTimeout(errorTimeout)
    }
    errorTimeout = setTimeout(() => {
      error.value = ''
    }, 3000)
    
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
    showLoginUsernameError.value = false
    showLoginPasswordError.value = false
  } else {
    registerErrors.value = { username: false, password: false, email: false }
    showRegisterUsernameError.value = false
    showRegisterPasswordError.value = false
    showRegisterEmailError.value = false
  }
}

// 监听tab切换
watch(activeTab, () => {
  loginForm.value = { username: '', password: '' }
  registerForm.value = { username: '', password: '', email: '' }
  resetErrors()
  error.value = ''
  
  if (errorTimeout) {
    clearTimeout(errorTimeout)
  }
})
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); /* 深蓝到蓝色渐变 */
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
  background: radial-gradient(rgba(191, 219, 254, 0.2), transparent);
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
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  z-index: 2;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.title-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.logo {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.gradient-text {
  background: linear-gradient(45deg, #2563eb, #3b82f6); /* 蓝色渐变 */
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
  color: #2563eb; /* 深蓝色 */
  font-weight: 600;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  width: 100%;
  height: 3px;
  background: #2563eb; /* 深蓝色 */
  border-radius: 2px;
}

.tab-divider {
  color: #9ca3af;
  font-size: 0.9rem;
}

.flip-container {
  perspective: 1000px;
  height: 360px; /* 增加高度以适应错误提示 */
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

.form-group {
  margin-bottom: 2.8rem; /* 增加1.3倍间距 (1.5 * 1.3 = 1.95) */
  position: relative;
}

.input-group {
  position: relative;
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
  border-bottom-color: #2563eb; /* 深蓝色 */
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
  color: #2563eb; /* 深蓝色 */
}

.input-border {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: #2563eb; /* 深蓝色 */
  transition: width 0.3s;
}

.error-message {
  color: #ef4444;
  font-size: 0.8rem;
  position: absolute;
  bottom: -1.2rem;
  left: 0;
  width: 100%;
  height: 1rem;
  transition: all 0.3s;
}

.auth-btn {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(45deg, #2563eb, #3b82f6); /* 蓝色渐变 */
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
  margin-top: 1.5rem; /* 增加按钮与上方元素的间距 */
  margin-bottom: 1.5rem; /* 增加按钮与错误提示的间距 */
}

.auth-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); /* 深蓝色阴影 */
}

.auth-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
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

.global-error {
  padding: 0.75rem;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%; /* 使错误提示与按钮同宽 */
  box-sizing: border-box;
}

/* 浮动错误提示样式 */
.floating-error {
  position: relative;
  margin-top: 1rem; /* 增加与按钮的距离 */
  z-index: 10;
  animation: fadeIn 0.3s;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease; /* 更平滑的消失效果 */
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>