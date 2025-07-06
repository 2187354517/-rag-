<template>
  <el-container class="layout-container-demo" style="height: 100%">
    <!-- 左侧导航栏 -->
    <el-aside width="100px" class="sidebar">
      <!-- 添加气泡容器 -->
      <div class="bubbles">
        <div v-for="n in 20" :key="n" class="bubble" 
             :style="{ 
               '--delay': `${Math.random() * 8}s`, 
               '--size': `${5 + Math.random() * 8}px`,
               '--left': `${Math.random() * 100}%`
             }">
        </div>
      </div>
      
      <el-scrollbar>
        <div class="top1-logo nav-logo" @click="goToLogin">
          <img src="@/assets/images/北极熊 logo1.png"/>
          <div class="system-name">PolarSolve</div>
        </div>
        
        <el-menu class="transparent-menu">
          <div class="nav-menu-item" 
               :class="{ 'active': currentComponent === 'ChatPage' }"
               @click="selectComponent('ChatPage')">
            <el-icon><ChatDotSquare/></el-icon>
            <span>聊天</span>
          </div>
          <div class="nav-menu-item" 
               :class="{ 'active': currentComponent === 'ManageKeysPage' }"
               @click="selectComponent('ManageKeysPage')">
            <el-icon><Document/></el-icon>
            <span>密钥</span>
          </div>
          <div class="nav-menu-item" 
               :class="{ 'active': currentComponent === 'EmptyPage2' }"
               @click="selectComponent('EmptyPage2')">
            <el-icon><Edit/></el-icon>
            <span>文档</span>
          </div>
          <div class="nav-menu-item" 
               :class="{ 'active': currentComponent === 'EmptyPage3' }"
               @click="selectComponent('EmptyPage3')">
            <el-icon><User/></el-icon>
            <span>知识库</span>
          </div>
        </el-menu>
        
        <!-- 底部图标部分保持不变 -->
        <div class="bottom-icons">
          <el-button class="icon-button" @click="handleToolsClick">
            <img src="@/assets/images/shezhi.png" class="custom-icon" />
          </el-button>
        </div>
      </el-scrollbar>
    </el-aside>
    <!-- 功能页面 -->
    <el-main style="margin-left: 100px;"> <!-- 增加边距以避免内容覆盖 -->
      <div>
        <component :is="showComponent"></component>
      </div>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import ChatPage from "@/views/content/chat/ChatPage.vue";
import KnowledgeBaseManager from "@/views/content/empty/KnowledgeBaseManager.vue";
import EmptyPage2 from "@/views/content/empty/EmptyPage2.vue";
import ManageKeysPage from "@/views/ManageKeysPage.vue";
// 使用组件实例作为类型
const showComponent = ref(null)
const currentComponent = ref('ChatPage')
const router = useRouter()

// 初始化默认组件
showComponent.value = ChatPage

const selectComponent = (component) => {
  currentComponent.value = component
  switch (component) {
    case 'ManageKeysPage':
      showComponent.value = ManageKeysPage
      break
    case 'ChatPage':
      showComponent.value = ChatPage
      break
    case 'EmptyPage2':
      showComponent.value = EmptyPage2
      break
    case 'EmptyPage3':
      showComponent.value = KnowledgeBaseManager
      break
  }
}

const handleToolsClick = () => {
  console.log('工具图标被点击')
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.layout-container-demo .el-aside {
  color: var(--el-text-color-primary);
}

.sidebar {
  position: fixed; /* 修改为fixed */
  left: 0; /* 添加left属性 */
  top: 0; /* 可以根据需要调整top位置 */
  height: 100%; /* 设置高度为100% */
  overflow: hidden;
  background: linear-gradient(to bottom, 
    #1cb5e0 0%,
    #0069e0 20%,
    #0052bc 40%,
    #003894 60%,
    #001e6c 80%,
    #000046 100%
  );
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  user-select: none;
}

.layout-container-demo .el-header {
  position: relative;
  background-color: var(--el-color-primary-light-7);
  color: var(--el-text-color-primary);
}

.layout-container-demo .el-menu {
  border-right: none;
}

.layout-container-demo .el-main {
  padding: 0;
}

.layout-container-demo .toolbar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  right: 20px;
}

.transparent-menu {
  background-color: transparent;
}

.nav-menu-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: transparent !important;
  height: auto;
  padding: 28px 10px;
  color: #ffffff;
  transition: all 0.3s ease;
  user-select: none;
  position: relative;
  overflow: hidden;
}

.nav-menu-item .el-icon {
  font-size: 24px;
  margin-bottom: 5px;
  transition: transform 0.3s ease;
}

.nav-menu-item span {
  font-size: 12px;
  font-weight: bold;
}

.nav-menu-item::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: width 0.3s ease, height 0.3s ease;
}

.nav-menu-item.active::before {
  width: 80px;
  height: 80px;
}

.nav-menu-item.active {
  color: #ffffff;
  font-weight: bold;
}

.nav-menu-item:hover .el-icon {
  transform: scale(1.2);
}

.nav-menu-item:hover {
  transform: none;
}

.bottom-icons {
  position: absolute;
  bottom: 30px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0;
}

.icon-button {
  background: transparent;
  border: none;
  padding: 8px 0;
  margin: 4px 0;
  width: 100%;
  height: 35px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.icon-button + .icon-button {
  margin-top: 25px;
}

.icon-button:hover {
  
  transform: scale(1.1);
}

.nav-logo {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  padding: 20px 0;
}

.nav-logo img {
  width: 50px;
  height: auto;
  transition: transform 0.3s ease;
}

.system-name {
  font-size: 12px;
  color: white;
  font-weight: bold;
  margin-top: 5px;
  text-align: center;
  word-break: break-word;
  max-width: 80px;
  padding: 0 5px;
}

.nav-logo img:hover {
  transform: scale(1.1);
}

.top1-logo img {
  width: 50px;
  height: auto;
}

.top2-logo img {
  margin-bottom: 10px;
}

.custom-icon {
  width: 28px;
  height: 28px;
  filter: brightness(0) invert(1);
}

.icon-button:hover .custom-icon {
  transform: scale(1.1);
}

.bubble {
  position: absolute;
  left: var(--left);
  bottom: -10px;
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  animation: rise 12s infinite ease-in;
  animation-delay: var(--delay);
}

@keyframes rise {
  0% {
    transform: translateY(0) translateX(0);
    opacity: 0;
  }
  20% {
    opacity: 0.5;
  }
  40% {
    transform: translateY(-30vh) translateX(5px);
  }
  60% {
    opacity: 0.7;
  }
  80% {
    transform: translateY(-60vh) translateX(-5px);
  }
  100% {
    transform: translateY(-100vh) translateX(3px);
    opacity: 0;
  }
}

@keyframes sway {
  0%, 100% {
    transform: translateX(-1px);
  }
  50% {
    transform: translateX(1px);
  }
}

.bubbles {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
  pointer-events: none;
  opacity: 0.7;
}

.el-scrollbar {
  position: relative;
  z-index: 1;
}
</style>