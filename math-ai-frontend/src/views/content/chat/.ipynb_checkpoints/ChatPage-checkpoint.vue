<template>
  <div class="ai-practice-container">
    <!-- 左侧历史对话记录 -->
    <div class="history-panel">
      <!-- 固定在顶部的新建会话按钮 -->
      <div class="new-chat-container" style="position: sticky; top: 0px;">
        <button class="new-chat-btn" @click="createConversation">
          新建会话
          <el-icon class="plus-icon">
            <Plus />
          </el-icon>
        </button>
      </div>

      <!-- 可滚动的会话列表 -->
      <div class="history-list-container" style="flex: 1; overflow-y: auto; margin: 20px 0;">
        <ul class="history-list">
          <li v-for="(item, index) in historyList" :key="index" 
              @click="selectConversation(index)"
              :class="{ active: currentConversationIndex === index }">
            <div class="conversation-item">
              <span v-if="!item.editing">{{ item.title || `会话 ${historyList.length - index}` }}</span>
              <input v-else
                    v-model="item.title"
                    @keyup.enter="confirmRename(index)"
                    @blur="confirmRename(index)"
                    @keydown.esc="cancelRename(index)"
                    class="rename-input"
                    ref="renameInput" />
              <div class="action-buttons">
                <el-icon class="edit-icon" @click.stop="startRename(index)">
                  <Edit />
                </el-icon>
                <el-icon class="delete-icon" @click.stop="deleteConversation(index)">
                  <Delete />
                </el-icon>
              </div>
            </div>
          </li>
        </ul>
      </div>

      <!-- 固定在底部的退出登录按钮 -->
      <div class="logout-btn-container" style="position: sticky; bottom: 20px;">
        <button class="logout-btn" @click="logout">退出登录</button>
      </div>
    </div>

    <!-- 右侧对话页面 -->
    <div class="chat-wrapper">
      <div class="chat-panel">
        <!-- 修改后的聊天消息区域 -->
        <div class="chat-messages" ref="chatMessagesRef">
          <div v-for="(msg, index) in history" :key="index" :class="['message', msg.role]">
            <div class="avatar">
              <div v-if="msg.role !== 'user'" class="ai-avatar">
                <img src="@/assets/images/hailuo2.png" alt="AI Avatar">
              </div>
              <div v-else>
                <img src="@/assets/images/user.png" alt="Me">
              </div>
            </div>
            <div class="content">
              <template v-if="msg.role === 'assistant'">
                <div v-if="msg.isLoading" class="response-stream-container">
                  <div class="typewriter-content" :style="{ '--text-length': msg.displayContent?.length || 0 }">
                    {{ msg.displayContent }}
                    <span class="typing-cursor" v-if="!msg.isComplete"></span>
                  </div>
                  <div v-if="!msg.displayContent" class="loading-animation">
                    <div class="wave-dots">
                      <div class="wave-dot"></div>
                      <div class="wave-dot"></div>
                      <div class="wave-dot"></div>
                    </div>
                  </div>
                </div>
                <MathJaxSupport v-else :content="msg.content" />
              </template>
              <span v-else>{{ msg.content }}</span>
              <!-- 在AI回答内容下方显示相关问题 -->
              <div v-if="msg.role === 'assistant' && relatedQuestions.length > 0 && index === history.length - 1 && !msg.isLoading && !msg.wasStopped" class="related-questions-container">
                <div class="related-questions">
                  <h4>相关问题：</h4>
                  <button 
                    v-for="(question, qIndex) in relatedQuestions" 
                    :key="qIndex"
                    @click="selectRelatedQuestion(question)">
                    <MathJaxSupport :content="question" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入框 -->
        <div class="input-area">
          <div class="input-wrapper">
            <el-icon class="input-icon link-icon">
              <Link />
            </el-icon>
            <input
                v-model="userInput"
                @keyup.enter="handleEnterKey"
                placeholder="输入消息，按回车发送..."
                type="text"
            >
            <div class="button-group">
              <el-popover
                  placement="top"
                  :width="200"
                  trigger="hover"
                  :disabled="!!userInput.trim() || isGenerating"
              >
                <template #reference>
                  <div class="send-button-container" :class="{ 'pulse-animation': isGenerating }">
                    <el-button
                        class="send-button"
                        circle
                        @click="isGenerating ? stopGeneration() : submitQuestion()"
                        :disabled="!userInput.trim() && !isGenerating"
                        :type="isGenerating ? 'danger' : 'primary'"
                    >
                      <el-icon v-if="!isGenerating">
                        <Top />
                      </el-icon>
                      <el-icon v-else>
                        <VideoPause />
                      </el-icon>
                    </el-button>
                  </div>
                </template>
                <span v-if="!isGenerating">请输入消息后发送</span>
                <span v-else>点击停止生成回答</span>
              </el-popover>
            </div>
          </div>
          <!-- 停止生成提示 -->
          <div v-if="showStopHint" class="stop-hint">
            请点击停止按钮停止生成
          </div>
        </div>

        <div class="disclaimer">
          服务生成的所有内容均由AI生成，其生成内容的准确性和完整性无法保证
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest, streamingRequest } from '@/utils/request'
import { API } from '@/api/config'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Link, Top, Edit, Delete,VideoPause} from '@element-plus/icons-vue'
import MathJaxSupport from '@/components/MathJaxSupport.vue'

const router = useRouter()

const userInput = ref('')
const history = ref([])
const relatedQuestions = ref([])
const chatMessagesRef = ref(null)
const currentConversationIndex = ref(0)
const historyList = ref([])
const renameInput = ref([])
const isGenerating = ref(false)
const abortController = ref(null)
const showStopHint = ref(false)

// 处理回车键
const handleEnterKey = () => {
  if (isGenerating.value) {
    // 正在生成时显示提示
    showStopHint.value = true
    setTimeout(() => {
      showStopHint.value = false
    }, 2000)
  } else if (userInput.value.trim()) {
    submitQuestion()
  }
}

// 停止生成
const stopGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  isGenerating.value = false
  
  // 标记最后一条消息为已完成但被停止
  if (history.value.length > 0) {
    const lastMsg = history.value[history.value.length - 1]
    if (lastMsg.role === 'assistant' && lastMsg.isLoading) {
      lastMsg.isLoading = false
      lastMsg.isComplete = true
      lastMsg.wasStopped = true
      lastMsg.content = lastMsg.displayContent || ''
    }
  }
  
  // 不显示相关问题
  relatedQuestions.value = []
}

const submitQuestion = async () => {
  if (!userInput.value.trim()) return;

  // 重置状态
  relatedQuestions.value = [];
  isGenerating.value = true;
  showStopHint.value = false;
  
  // 创建中止控制器
  abortController.value = new AbortController();

  try {
    let currentConversation = historyList.value[currentConversationIndex.value];

    if (!currentConversation?.conversation_id) {
      await createConversation();
      currentConversation = historyList.value[currentConversationIndex.value];
    }

    const userMessageContent = userInput.value.trim();
    const userMessage = { 
      role: 'user', 
      content: userMessageContent
    };

    // 保存用户消息到服务器
    await apiRequest(
      `/conversations/${currentConversation.conversation_id}/messages`,
      'POST',
      userMessage
    );

    // 更新本地消息记录
    currentConversation.messages.push(userMessage);
    history.value.push(userMessage);

    // 智能标题更新逻辑（新增部分）
    if (currentConversation.title === "新会话" && currentConversation.messages.length === 1) {
      const newTitle = userMessageContent.substring(0, 10).trim() || "新会话";
      try {
        // 更新服务器标题
        await apiRequest(
          `/conversations/${currentConversation.conversation_id}`, 
          'PATCH',
          { title: newTitle }
        );
        // 更新本地标题
        currentConversation.title = newTitle;
      } catch (error) {
        console.error('标题更新失败:', error);
        ElMessage.warning('自动标题更新失败，您可以在左侧手动修改标题');
      }
    }

    // 添加AI响应消息
    const aiMessage = {
      role: 'assistant',
      content: '',
      displayContent: '',
      isLoading: true,
      isComplete: false,
      wasStopped: false
    };
    history.value.push(aiMessage);
    currentConversation.messages.push(aiMessage);

    userInput.value = '';
    nextTick(scrollToBottom);

    // 准备请求参数
    const requestBody = {
      model: "deepseek-math",
      messages: history.value
        .filter(msg => !msg.isLoading)
        .map(msg => ({
          role: msg.role,
          content: msg.content
        })),
      max_tokens: 2048,
      temperature: 0.6,
      stream: true
    };

    // 流式请求处理
    await streamingRequest(
      API.GENERATE,
      'POST',
      requestBody,
      (chunk, isDone) => {
        const lastMsgIndex = history.value.length - 1;
        if (lastMsgIndex >= 0) {
          const aiMessage = history.value[lastMsgIndex];
          chunk = chunk.split('<｜end▁of▁sentence｜>').join('');
          requestAnimationFrame(() => {
            if (chunk) {
              aiMessage.displayContent += chunk;
              history.value = [...history.value];
            }
            if (isDone) {
              aiMessage.isComplete = true;
              setTimeout(() => {
                aiMessage.isLoading = false;
                aiMessage.content = aiMessage.displayContent;
                history.value = [...history.value];
                isGenerating.value = false;
                abortController.value = null;
              }, 100);
            }
          });
          
          nextTick(scrollToBottom);
        }
      },
      async (fullContent) => {
        try {
          const currentConv = historyList.value[currentConversationIndex.value];
          if (!currentConv?.conversation_id) return;

          // 保存完整AI响应到服务器
          await apiRequest(
            `/conversations/${currentConv.conversation_id}/messages`,
            'POST',
            { 
              role: 'assistant',
              content: fullContent 
            }
          );
          
          // 获取相关问题（仅在正常完成时）
          if (!history.value[history.value.length - 1]?.wasStopped) {
            try {
              const related = await apiRequest(API.RELATED_QUESTIONS, 'POST', {
                question: userMessageContent
              });
              relatedQuestions.value = related.related_questions || [];
            } catch (relatedError) {
              console.warn('获取相关问题失败:', relatedError);
            }
          }
        } catch (e) {
          console.error('保存AI消息失败:', e);
        }
      },
      abortController.value.signal
    );

  } catch (err) {
    if (err.name === 'AbortError') {
      console.log('请求已中止');
    } else {
      console.error('提交问题失败:', err);
      ElMessage.error('请求失败: ' + (err.message || '未知错误'));
      
      if (history.value[history.value.length - 1]?.isLoading) {
        history.value.pop();
      }
    }
    isGenerating.value = false;
    abortController.value = null;
  }
};

// 会话操作方法
const startRename = (index) => {
  historyList.value[index].editing = true
  historyList.value[index].originalTitle = historyList.value[index].title || `会话 ${index + 1}`
  nextTick(() => {
    renameInput.value[index]?.focus()
  })
}

const confirmRename = async (index) => {
  const conversation = historyList.value[index]
  conversation.editing = false
  
  if (!conversation.title || conversation.title === conversation.originalTitle) {
    conversation.title = conversation.originalTitle
    return
  }

  try {
    await apiRequest(`/conversations/${conversation.conversation_id}`, 'PATCH', {
      title: conversation.title
    })
    ElMessage.success('重命名成功')
  } catch (error) {
    conversation.title = conversation.originalTitle
    ElMessage.error('重命名失败')
    console.error('Rename error:', error)
  }
}

const cancelRename = (index) => {
  const conversation = historyList.value[index]
  conversation.title = conversation.originalTitle
  conversation.editing = false
}

const deleteConversation = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除此会话吗？删除后将无法恢复', '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'delete-confirm-btn'
    })
    
    const conversation = historyList.value[index]
    await apiRequest(`/conversations/${conversation.conversation_id}`, 'DELETE')
    
    // 删除后处理逻辑优化
    const wasCurrent = currentConversationIndex.value === index
    const wasLast = index === historyList.value.length - 1
    
    // 先删除条目
    historyList.value.splice(index, 1)
    
    // 处理当前选中会话
    if (wasCurrent) {
      if (historyList.value.length > 0) {
        // 优先选择前一个会话，如果不存在则选第一个
        currentConversationIndex.value = Math.max(0, Math.min(index - 1, historyList.value.length - 1))
        await loadHistory(historyList.value[currentConversationIndex.value].conversation_id)
      } else {
        // 没有会话时自动创建新会话
        await createConversation()
      }
    } else if (!wasLast && currentConversationIndex.value > index) {
      currentConversationIndex.value--
    }
    
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('Delete error:', error)
    }
  }
}

// 优化后的加载历史方法
const loadHistory = async (conversationId) => {
  if (!conversationId) {
    history.value = []
    relatedQuestions.value = []
    return
  }
  
  try {
    const response = await apiRequest(`/conversations/${conversationId}/messages`)
    history.value = (response.messages || []).map(msg => ({
      ...msg,
      isLoading: false,
      displayContent: msg.content,
      isComplete: true,
      wasStopped: false
    }))
    relatedQuestions.value = []
  } catch (err) {
    if (err.response?.status === 404) {
      // 处理会话不存在的情况
      ElMessage.warning('该会话不存在，已自动刷新列表')
      await refreshConversationList()
      history.value = []
    } else {
      console.error('加载历史失败:', err.message)
      ElMessage.error('会话历史加载失败')
    }
  }
}

// 新增刷新会话列表方法
const refreshConversationList = async () => {
  try {
    const conversations = await apiRequest('/conversations')
    historyList.value = conversations.map(conv => ({
      ...conv,
      editing: false
    }))
    
    // 确保当前选中索引有效
    if (historyList.value.length > 0) {
      currentConversationIndex.value = Math.min(
        currentConversationIndex.value,
        historyList.value.length - 1
      )
    } else {
      await createConversation()
    }
  } catch (err) {
    console.error('刷新会话列表失败:', err)
    ElMessage.error('会话列表刷新失败')
  }
}

const createConversation = async () => {
  try {
    const response = await apiRequest(API.CONVERSATIONS, 'POST', { 
      title: "新会话" 
    })
    if (response.conversation_id) {
      // 修改为添加到列表开头
      historyList.value.unshift({
        title: "新会话",
        messages: [],
        conversation_id: response.conversation_id,
        editing: false,
        timestamp: new Date().getTime() // 添加时间戳用于排序
      })
      currentConversationIndex.value = 0
      await loadHistory(response.conversation_id)
      ElMessage.success('会话创建成功')
    }
  } catch (err) {
    console.error('创建会话失败:', err)
    ElMessage.error('创建会话失败: ' + err.message)
  }
}

const selectConversation = (index) => {
  currentConversationIndex.value = index
  const selectedConversation = historyList.value[index]
  if (selectedConversation.conversation_id) {
    loadHistory(selectedConversation.conversation_id)
  } else {
    history.value = selectedConversation.messages
    relatedQuestions.value = []
  }
  nextTick(() => {
    scrollToBottom()
  })
}

const selectRelatedQuestion = (question) => {
  userInput.value = question
  submitQuestion()
}

const logout = () => {
  localStorage.clear()
  router.push('/login')
}

const scrollToBottom = () => {
  const container = chatMessagesRef.value;
  if (container) {
    clearTimeout(container.__scrollTimer);
    container.__scrollTimer = setTimeout(() => {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
    }, 50);
  }
}

// 修改加载会话列表的逻辑
onMounted(async () => {
  try {
    const conversations = await apiRequest('/conversations')
    // 按时间倒序排列
    historyList.value = conversations
      .map(conv => ({
        ...conv,
        editing: false,
        timestamp: new Date(conv.created_at).getTime() || new Date().getTime()
      }))
      .sort((a, b) => b.timestamp - a.timestamp)
      
    if (historyList.value.length > 0) {
      currentConversationIndex.value = 0
      const defaultConversation = historyList.value[0]
      if (defaultConversation.conversation_id) {
        loadHistory(defaultConversation.conversation_id)
      }
    }
    nextTick(() => {
      scrollToBottom()
    })
  } catch (err) {
    console.error('加载会话列表失败:', err)
    ElMessage.error('会话列表加载失败')
  }
})
</script>

<style scoped>
/* 新增停止提示样式 */
.stop-hint {
  color: #f56c6c;
  font-size: 12px;
  text-align: center;
  margin-top: 5px;
  animation: fadeInOut 2s ease;
}

@keyframes fadeInOut {
  0% { opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% { opacity: 0; }
}

/* 调整发送/停止按钮样式 */
.send-button {
  width: 40px !important;
  height: 40px !important;
  transition: all 0.3s ease;
}
.send-button:hover {
  transform: scale(1.05);
}

.send-button:active {
  transform: scale(0.95);
}

/* 调整图标大小 */
.send-button .el-icon {
  font-size: 18px;
}
/* 整体布局样式 */
.ai-practice-container {
  overflow: hidden !important;
  height: 100%;
  width: 100%;
  display: flex;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #f4f7fa, #e9f0f5);
  height: 100vh;
}

/* 左侧历史面板样式 */
.history-panel {
  width: 280px;
  background: #ffffff;
  padding: 20px;
  overflow-y: auto;
  border-right: 1px solid #eaeaea;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100vh;
}

/* 新建会话按钮 */
.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 15px;
  font-weight: 600;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
  background: linear-gradient(135deg, #0056b3, #007bff);
}

/* 历史会话列表 */
.history-list {
  list-style-type: none;
  padding: 0;
  margin: 0;
  width: 100%;
}

.history-list li {
  margin: 0 0 10px 0;
  padding: 10px 12px;
  background-color: #f9f9f9;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.history-list li:hover,
.history-list li.active {
  background-color: rgba(0, 123, 255, 0.1);
  color: #0056b3;
  transform: translateX(5px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* 会话操作按钮 */
.conversation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.action-buttons {
  display: none;
  gap: 8px;
}

.history-list li:hover .action-buttons {
  display: flex;
}

.edit-icon, .delete-icon {
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  cursor: pointer;
  font-size: 16px;
}

.edit-icon:hover {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.delete-icon:hover {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.rename-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  outline: none;
  font-size: 14px;
  height: 28px;
  margin-right: 8px;
}

/* 退出登录按钮 */
.logout-btn {
  width: 100%;
  padding: 12px;
  margin-top: 20px;
  background: linear-gradient(135deg, #ff6b6b, #ff8e8e);
  color: white;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
  background: linear-gradient(135deg, #ff8e8e, #ff6b6b);
}

/* 右侧聊天区域 */
.chat-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f4f7fa;
}

.chat-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: transparent;
  box-shadow: none;
  padding-top: 12px;
}

/* 聊天消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 10%;
  background-color: transparent;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 123, 255, 0.3) transparent;
  scroll-behavior: smooth;
  overflow-anchor: none;
}

.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background-color: rgba(0, 123, 255, 0.3);
  border-radius: 4px;
}

/* 消息项样式 */
.message {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 头像样式 */
.message .avatar {
  width: 48px;
  height: 48px;
  min-width: 48px;
  min-height: 48px;
  border-radius: 50%;
  background-color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.message .avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

/* 消息内容样式 */
.message .content {
  background-color: #ffffff;
  padding: 14px 20px;
  border-radius: 15px;
  max-width: 90%;
  width: fit-content;
  font-size: 16px;
  line-height: 1.8;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow-x: auto;
  position: relative;
  transition: all 0.3s ease;
  word-break: break-word;
}

/* 用户消息特殊样式 */
.message.user {
  flex-direction: row-reverse;
}

.message.user .avatar {
  margin-right: 0;
  margin-left: 15px;
}

.message.user .content {
  background-color: rgba(0, 123, 255, 0.1);
  color: black;
}

/* 输入区域样式 */
.input-area {
  padding: 20px 10% 0 10%;
  border-top: 1px solid #eaeaea;
  background-color: #f9f9f9;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

input {
  width: 100%;
  padding: 16px 120px 16px 60px;
  border: 1px solid #ccc;
  border-radius: 25px;
  font-size: 16px;
  background-color: #ffffff;
  transition: border-color 0.3s ease;
  height: 60px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.2);
}

input::placeholder {
  color: #969696;
}

/* 按钮组样式 */
.button-group {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
}

/* 输入图标样式 */
.input-icon {
  color: #007bff;
  font-size: 26px;
  cursor: pointer;
  transition: color 0.3s ease;
}

.input-icon:hover {
  color: #0056b3;
}

.link-icon {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
}

/* 发送按钮容器 */
.send-button-container {
  position: relative;
}

/* 升级版脉冲动画效果 */
.pulse-animation::before {
  content: '';
  position: absolute;
  top: -8px;
  left: -8px;
  right: -8px;
  bottom: -8px;
  border: 2px solid rgba(64, 158, 255, 0.8);
  border-radius: 50%;
  animation: pulseGlow 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  pointer-events: none;
  box-shadow: 0 0 10px rgba(64, 158, 255, 0.5);
}

.pulse-animation::after {
  content: '';
  position: absolute;
  top: -12px;
  left: -12px;
  right: -12px;
  bottom: -12px;
  border: 1px solid rgba(64, 158, 255, 0.4);
  border-radius: 50%;
  animation: pulseOuter 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  pointer-events: none;
}

@keyframes pulseGlow {
  0% {
    transform: scale(0.9);
    opacity: 0.8;
    box-shadow: 0 0 5px rgba(64, 158, 255, 0.8);
  }
  50% {
    transform: scale(1.1);
    opacity: 0.4;
    box-shadow: 0 0 20px rgba(64, 158, 255, 0.6);
  }
  100% {
    transform: scale(0.9);
    opacity: 0.8;
    box-shadow: 0 0 5px rgba(64, 158, 255, 0.8);
  }
}

@keyframes pulseOuter {
  0% {
    transform: scale(0.8);
    opacity: 0.6;
  }
  70% {
    transform: scale(1.2);
    opacity: 0;
  }
  100% {
    transform: scale(0.8);
    opacity: 0;
  }
}

/* 悬停时增强效果 */
.send-button:hover .pulse-animation::before {
  animation: pulseGlow 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
  border-width: 3px;
}

.send-button:hover .pulse-animation::after {
  animation: pulseOuter 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

/* 发送按钮样式 */
.send-button {
  width: 40px !important;
  height: 40px !important;
  background: linear-gradient(to right, #0069e0, #0052bc);
  border: none;
  color: white;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.send-button:disabled {
  background: rgba(0, 123, 255, 0.1);
  color: rgba(0, 86, 179, 0.3);
  cursor: default;
}

.send-button:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
  background: linear-gradient(135deg, #0056b3, #007bff);
}

.send-button :deep(.el-icon) {
  font-size: 26px;
}

/* 免责声明样式 */
.disclaimer {
  font-size: 12px;
  color: #999;
  text-align: center;
  margin-top: 12px;
  margin-bottom: 12px;
}

/* 相关问题样式 */
.related-questions-container {
  width: 100%;
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 10px;
}

.related-questions {
  padding: 5px 0;
}

.related-questions h4 {
  margin-bottom: 8px;
  color: #666;
  font-size: 14px;
  font-weight: 500;
}

.related-questions button {
  display: inline-block;
  margin: 3px;
  padding: 6px 12px;
  background-color: rgba(0, 123, 255, 0.08);
  border: none;
  border-radius: 16px;
  color: #007bff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 13px;
}

.related-questions button:hover {
  background-color: rgba(0, 123, 255, 0.15);
}
/* 确保MathJax在按钮中正确显示 */
.related-questions button :deep(.MathJax),
.related-questions button :deep(.MJXc-display) {
  display: inline !important;
  margin: 0 !important;
  padding: 0 !important;
}

.related-questions button :deep(.MathJax_Display) {
  display: inline-block !important;
  margin: 0 !important;
  text-align: left !important;
}
/* 流式响应容器 */
.response-stream-container {
  min-height: 40px;
  position: relative;
  width: 100%;
}

/* 打字机内容样式 */
.typewriter-content {
  display: inline-block;
  white-space: pre-wrap;
  word-break: break-word;
  max-width: 100%;
  line-height: 1.8;
}

/* 打字机光标 */
.typing-cursor {
  display: inline-block;
  width: 8px;
  height: 1.2em;
  background: #007bff;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
  opacity: 1;
  transition: opacity 0.3s ease;
}

/* 波浪点加载动画 */
.wave-dots {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  height: 24px;
}

.wave-dot {
  width: 6px;
  height: 6px;
  background: #007bff;
  border-radius: 50%;
  animation: wave 1.2s ease-in-out infinite;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .message .content {
    max-width: 85%;
    padding: 12px 16px;
  }
  
  .chat-messages {
    padding: 15px 5%;
  }
  
  .input-area {
    padding: 15px 5% 0 5%;
  }
  
  .history-panel {
    width: 240px;
  }
}

/* 动画优化 */
@keyframes wave {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
  30% { transform: translateY(-6px); opacity: 1; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 删除确认按钮特殊样式 */
:deep(.delete-confirm-btn) {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
}

/* 历史列表容器滚动条 */
.history-list-container {
  flex: 1;
  margin-top: 20px;
  margin-bottom: 20px;
  overflow-x: hidden;
  white-space: nowrap;
}

.history-list-container::-webkit-scrollbar {
  width: 6px;
}

.history-list-container::-webkit-scrollbar-track {
  background: #f0f0f0;
}

.history-list-container::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 3px;
}

/* 数学公式样式 */
.message .content :deep(.MathJax) {
  outline: none;
  display: inline-block;
}

.message .content :deep(.mjx-chtml) {
  display: inline-block;
  line-height: 1.2;
  vertical-align: middle;
}

.message .content :deep(.mjx-block) {
  display: block;
  margin: 0.5em 0;
  text-align: center;
}
</style>