import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// // 初始化 WebSocket
// const socket = new WebSocket('ws://30de5fdf.r6.cpolar.cn/ws');

// // 监听 WebSocket 连接打开
// socket.onopen = () => {
//   console.log('WebSocket connection established');
// };

// // 监听 WebSocket 消息
// socket.onmessage = (event) => {
//   console.log('Received message:', event.data);
// };

// // 监听 WebSocket 错误
// socket.onerror = (error) => {
//   console.error('WebSocket error:', error);
// };

// // 监听 WebSocket 关闭
// socket.onclose = () => {
//   console.log('WebSocket connection closed');
// };

// app.config.globalProperties.$socket = socket; // 将 WebSocket 实例挂载到全局




const app = createApp(App)

// 使用 ElementPlus 插件
app.use(ElementPlus)

// 全局注册 Element Plus 图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

app.use(router).mount('#app')