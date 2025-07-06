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
                <img src="@/assets/images/北极熊 logo2.png" alt="AI Avatar">
              </div>
            </div>
            <!-- 修改消息内容部分 -->
            <div class="content">
              <div v-if="msg.role === 'assistant'">
                <div v-if="msg.isLoading" class="response-stream-container">
                  <div v-if="msg.displayContent" class="typewriter-content">
                    <MarkdownRenderer :content="msg.displayContent" />
                    <span class="typing-cursor" v-if="!msg.isComplete"></span>
                  </div>
                  <div v-else class="loading-animation">
                    <div class="wave-dots">
                      <div class="wave-dot"></div>
                      <div class="wave-dot"></div>
                      <div class="wave-dot"></div>
                    </div>
                  </div>
                </div>
                <MarkdownRenderer v-else :content="msg.content" />
                <!-- 只在 AI 回答时显示参考资料 -->
                <!-- 参考资料区域 -->
                <div v-if="msg.role === 'assistant' && referenceFiles.length > 0 && index === history.length - 1 && !msg.isLoading && msg.isComplete" class="reference-files-container">
                  <h3>参考资料</h3>
                  <ul class="reference-files-list">
                    <li v-for="(file, index) in referenceFiles" :key="index" class="reference-file-item">
                      <a @click="downloadFile(file)" class="reference-file-link">
                        <el-icon><Document /></el-icon>
                        <span>{{ file.file_name }}</span>
                      </a>
                    </li>
                  </ul>
                </div>
              </div>
              <span v-else>{{ msg.content }}</span>
              <!-- 在AI回答内容下方显示相关问题 -->
              <div v-if="msg.role === 'assistant' && relatedQuestions.length > 0 && index === history.length - 1 && !msg.isLoading && !msg.wasStopped" class="related-questions-container">
                <div class="related-questions">
                  <h3>相关问题：</h3>
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

        <!-- 修改图片上传区域 -->
        <div class="image-upload-area" v-if="uploadedImage || isProcessingImage">
          <div class="image-preview-container">
            <img v-if="uploadedImage" :src="uploadedImage" class="preview-image" />
            <div class="progress-overlay" v-if="isProcessingImage">
              <div class="progress-text">
                <span v-if="ocrProgress < 100">识别中 {{ ocrProgress }}%</span>
                <span v-else>正在优化识别结果...</span>
              </div>
              <el-progress 
                :percentage="ocrProgress" 
                :stroke-width="4"
                :status="ocrProgress < 100 ? '' : 'success'"
              />
              <div class="progress-tip" v-if="ocrProgress < 50">
                小提示：清晰的文字图片识别效果更好
              </div>
            </div>
            <el-icon class="close-icon" @click="clearImage">
              <Close />
            </el-icon>
          </div>
          <div class="ocr-result" v-if="ocrText">
            <div class="ocr-result-header">
              <span>识别结果：</span>
              <div class="ocr-actions">
                <el-button size="small" @click="copyOcrText">复制文本</el-button>
                <el-button size="small" type="primary" @click="insertOcrText">
                  插入到输入框
                </el-button>
              </div>
            </div>
            <div class="ocr-result-content" :class="{ 'expanded': isOcrExpanded }">
              {{ ocrText }}
              <el-button 
                v-if="ocrText.length > 150" 
                class="expand-btn" 
                text 
                @click="isOcrExpanded = !isOcrExpanded"
              >
                {{ isOcrExpanded ? '收起' : '展开全部' }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 输入框 -->
        <div class="input-area">
          <div class="input-wrapper">
            <el-upload
              class="upload-demo"
              action=""
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleImageUpload"
              accept="image/*"
            >
              <el-icon class="input-icon image-icon">
                <Picture />
              </el-icon>
            </el-upload>
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
import { API, BASE_URL } from '@/api/config'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Top, Edit, Delete, VideoPause, Picture, Close } from '@element-plus/icons-vue'
import MathJaxSupport from '@/components/MathJaxSupport.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const router = useRouter()

// 聊天相关状态
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
const lastQuestionId = ref(null)
const referenceFiles = ref([])

// OCR相关状态
const uploadedImage = ref(null)
const ocrText = ref('')
const isProcessingImage = ref(false)
const ocrProgress = ref(0)
const isOcrExpanded = ref(false)

// 处理回车键
const handleEnterKey = () => {
  if (isGenerating.value) {
    showStopHint.value = true
    setTimeout(() => {
      showStopHint.value = false
    }, 2000)
  } else if (userInput.value.trim() || ocrText.value) {
    submitQuestion()
  }
}

// 复制 OCR 文本
const copyOcrText = () => {
  if (ocrText.value) {
    navigator.clipboard.writeText(ocrText.value)
    ElMessage.success('已复制到剪贴板')
  }
}

// 修改 handleImageUpload 方法
const handleImageUpload = async (file) => {
  try {
    // 检查文件类型和大小
    if (!file.raw.type.startsWith('image/')) {
      ElMessage.error('请上传图片文件')
      return
    }
    
    if (file.raw.size > 2 * 1024 * 1024) { // 降低到2MB限制
      ElMessage.error('图片大小不能超过2MB')
      return
    }
    
    // 显示预览
    const reader = new FileReader()
    reader.onload = (e) => {
      uploadedImage.value = e.target.result
    }
    reader.readAsDataURL(file.raw)
    
    // 开始处理
    isProcessingImage.value = true
    ocrProgress.value = 10 // 立即显示进度
    
    // 模拟处理进度
    const progressInterval = setInterval(() => {
      if (ocrProgress.value < 90) {
        ocrProgress.value +=1
      } else {
        clearInterval(progressInterval)
      }
    }, 300)
    
    // 实际OCR处理
    const formData = new FormData()
    formData.append('image', file.raw)
    formData.append('prompt', '提取图片中的数学公式和文字，保持原始格式')
    
    const response = await apiRequest('/v1/ocr', 'POST', formData, {
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          ocrProgress.value = 10 + Math.round((progressEvent.loaded * 40) / progressEvent.total)
        }
      }
    })
    
    // 处理完成
    clearInterval(progressInterval)
    ocrProgress.value = 100
    ocrText.value = response.text
    isProcessingImage.value = false
    
    // 自动展开短文本
    isOcrExpanded.value = ocrText.value.length <= 150
    
  } catch (error) {
    console.error('OCR处理失败:', error)
    let errorMsg = 'OCR处理失败'
    if (error.response?.data?.message) {
      errorMsg = error.response.data.message
    } else if (error.message) {
      errorMsg = error.message
    }
    ElMessage.error(errorMsg)
    clearImage()
  }
}

// 清除图片和OCR结果
const clearImage = () => {
  uploadedImage.value = null
  ocrText.value = ''
  isProcessingImage.value = false
  ocrProgress.value = 0
}

// 将OCR结果插入到输入框
const insertOcrText = () => {
  if (ocrText.value) {
    userInput.value = ocrText.value
    // 自动聚焦到输入框
    nextTick(() => {
      document.querySelector('.input-area input')?.focus()
    })
  }
}

// 停止生成回答
const stopGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  isGenerating.value = false
  
  if (history.value.length > 0) {
    const lastMsg = history.value[history.value.length - 1]
    if (lastMsg.role === 'assistant' && lastMsg.isLoading) {
      lastMsg.isLoading = false
      lastMsg.isComplete = true
      lastMsg.wasStopped = true
      lastMsg.content = lastMsg.displayContent || ''
    }
  }
  
  relatedQuestions.value = []
}

// 提交问题
const submitQuestion = async () => {
  if (!userInput.value.trim() && !ocrText.value) return;

  // 如果有OCR文本但用户没有输入，自动使用OCR文本
  if (ocrText.value && !userInput.value.trim()) {
    userInput.value = ocrText.value
  }

  relatedQuestions.value = [];
  isGenerating.value = true;
  showStopHint.value = false;
  
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
      content: userMessageContent,
      referenceFiles: []
    };

    // 保存用户消息到会话
    await apiRequest(
      `/conversations/${currentConversation.conversation_id}/messages`,
      'POST',
      userMessage
    );

    userInput.value = '';
    nextTick(scrollToBottom);

    currentConversation.messages.push(userMessage);
    history.value.push(userMessage);

    // 智能更新标题的逻辑
    if (currentConversation.title === "新会话" && currentConversation.messages.length === 1) {
      const newTitle = userMessageContent.substring(0, 10).trim() || "新会话";
      try {
        await apiRequest(
          `/conversations/${currentConversation.conversation_id}`, 
          'PATCH',
          { title: newTitle }
        );
        currentConversation.title = newTitle;
      } catch (error) {
        console.error('标题更新失败:', error);
        ElMessage.warning('自动标题更新失败，您可以在左侧手动修改标题');
      }
    }
    
    // 添加AI响应消息（显示加载状态）
    const aiMessage = {
      role: 'assistant',
      content: '',
      displayContent: '',
      isLoading: true,
      isComplete: false,
      wasStopped: false,
      referenceFiles: []
    };
    history.value.push(aiMessage);
    currentConversation.messages.push(aiMessage);
    
    nextTick(scrollToBottom);

    // 保存问题并获取问题ID
    try {
      const questionResponse = await apiRequest(
        API.SAVE_QUESTION,
        'POST',
        {
          content: userMessageContent,
          conversation_id: currentConversation.conversation_id
        }
      );
      
      if (questionResponse.question_id) {
        lastQuestionId.value = questionResponse.question_id;
        
        // 获取参考文件
        if (!history.value[history.value.length - 1]?.wasStopped) {
          await fetchReferenceFiles(lastQuestionId.value);
        }
      }
    } catch (error) {
      console.error('保存问题失败:', error);
    }

    // 生成AI回答
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

    await streamingRequest(
      API.GENERATE,
      'POST',
      requestBody,
      (chunk, isDone) => {
        const lastMsgIndex = history.value.length - 1;
        if (lastMsgIndex >= 0) {
          const aiMessage = history.value[lastMsgIndex];
          chunk = chunk.split('').join('');
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
          // 保存AI回答
          await apiRequest(
            `/conversations/${currentConversation.conversation_id}/messages`,
            'POST',
            { 
              role: 'assistant',
              content: fullContent.split('').join('')
            }
          );

          // 获取相关问题
          if (!history.value[history.value.length - 1]?.wasStopped) {
            try {
              const related = await apiRequest(API.RELATED_QUESTIONS, 'POST', {
                question: userMessageContent
              });
              relatedQuestions.value = related.related_questions || [];
            } catch (error) {
              console.warn('获取相关问题失败:', error);
            }
          }
        } catch (error) {
          console.error('保存AI回答失败:', error);
        }
      },
      abortController.value.signal
    );

    // 发送后清空OCR相关状态
    clearImage();

  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('请求已中止');
    } else {
      console.error('提交问题失败:', error);
      ElMessage.error('请求失败: ' + (error.message || '未知错误'));
      
      if (history.value[history.value.length - 1]?.isLoading) {
        history.value.pop();
      }
    }
    isGenerating.value = false;
    abortController.value = null;
  }
};

// 开始重命名会话
const startRename = (index) => {
  historyList.value[index].editing = true
  historyList.value[index].originalTitle = historyList.value[index].title || `会话 ${index + 1}`
  nextTick(() => {
    renameInput.value[index]?.focus()
  })
}

// 确认重命名
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

// 取消重命名
const cancelRename = (index) => {
  const conversation = historyList.value[index]
  conversation.title = conversation.originalTitle
  conversation.editing = false
}

// 删除会话
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
    
    const wasCurrent = currentConversationIndex.value === index
    const wasLast = index === historyList.value.length - 1
    
    historyList.value.splice(index, 1)
    
    if (wasCurrent) {
      if (historyList.value.length > 0) {
        currentConversationIndex.value = Math.max(0, Math.min(index - 1, historyList.value.length - 1))
        await loadHistory(historyList.value[currentConversationIndex.value].conversation_id)
      } else {
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

// 加载历史消息
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
      ElMessage.warning('该会话不存在，已自动刷新列表')
      await refreshConversationList()
      history.value = []
    } else {
      console.error('加载历史失败:', err.message)
      ElMessage.error('会话历史加载失败')
    }
  }
}

// 刷新会话列表
const refreshConversationList = async () => {
  try {
    const conversations = await apiRequest('/conversations')
    historyList.value = conversations.map(conv => ({
      ...conv,
      editing: false
    }))
    
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

// 创建新会话
const createConversation = async () => {
  try {
    const response = await apiRequest(API.CONVERSATIONS, 'POST', { 
      title: "新会话" 
    })
    if (response.conversation_id) {
      historyList.value.unshift({
        title: "新会话",
        messages: [],
        conversation_id: response.conversation_id,
        editing: false,
        timestamp: new Date().getTime()
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

// 选择会话
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

// 选择相关问题
const selectRelatedQuestion = (question) => {
  userInput.value = question
  submitQuestion()
}

// 退出登录
const logout = () => {
  localStorage.clear()
  router.push('/login')
}

// 滚动到底部
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

// 下载文件
const downloadFile = async (file) => {
  try {
    const token = localStorage.getItem('token')
    
    const downloadUrl = `${BASE_URL}${API.DOWNLOAD}?file_path=${encodeURIComponent(file.file_name)}`
    
    const response = await fetch(downloadUrl, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.statusText}`)
    }
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = file.file_name
    document.body.appendChild(link)
    link.click()
    
    window.URL.revokeObjectURL(url)
    document.body.removeChild(link)
    
    ElMessage.success('文件下载成功')
  } catch (error) {
    console.error('下载文件失败:', error)
    ElMessage.error('下载文件失败：' + error.message)
  }
}

// 获取参考资料
const fetchReferenceFiles = async (questionId) => {
  try {
    const currentQuestion = history.value[history.value.length - 2]?.content || ''
    
    const response = await apiRequest(
      `${API.REFERENCE_FILES}?question_id=${questionId}&query=${encodeURIComponent(currentQuestion)}&source=knowledge_base`,
      'GET'
    )
    
    if (response.status === 'success' && response.reference_files && response.reference_files.length > 0) {
      referenceFiles.value = response.reference_files.map(file => ({
        ...file,
        file_path: `knowledge_base/${file.file_path}`
      }))
    } else {
      referenceFiles.value = []
    }
  } catch (error) {
    console.error('获取参考资料失败:', error)
    referenceFiles.value = []
  }
}

// 组件挂载时加载会话列表
onMounted(async () => {
  try {
    const conversations = await apiRequest('/conversations')
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
/* 图片上传区域样式优化 */
.image-upload-area {
  margin: 0 10% 15px;
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  padding: 12px;
  background-color: var(--el-bg-color);
  transition: all 0.3s ease;
}

.image-preview-container {
  position: relative;
  max-height: 200px;
  overflow: hidden;
  border-radius: 6px;
  margin-bottom: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-image {
  width: 100%;
  max-height: 200px;
  object-fit: contain;
  display: block;
}

.progress-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  padding: 20px;
  text-align: center;
}

.progress-text {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 500;
}

.progress-tip {
  margin-top: 10px;
  font-size: 12px;
  opacity: 0.8;
}

.close-icon {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border-radius: 50%;
  padding: 5px;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
}

.close-icon:hover {
  background: rgba(0, 0, 0, 0.7);
  transform: scale(1.1);
}

.ocr-result {
  border-top: 1px solid var(--el-border-color);
  padding-top: 12px;
  margin-top: 12px;
}

.ocr-result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.ocr-actions {
  display: flex;
  gap: 8px;
}

.ocr-result-content {
  background: var(--el-fill-color-light);
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.6;
  max-height: 150px;
  overflow: hidden;
  position: relative;
  transition: max-height 0.3s ease;
}

.ocr-result-content.expanded {
  max-height: none;
}

.expand-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  background: linear-gradient(to right, transparent, var(--el-bg-color) 30%);
  padding-left: 20px;
}

/* 调整图片上传按钮样式 */
.image-icon {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  color: #007bff;
  font-size: 26px;
  cursor: pointer;
  transition: color 0.3s ease;
}
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
  margin-bottom:15px;
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
.message.user .avatar {
  display: none;
}

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
  background-color: transparent;
  padding: 14px 20px;
  border-radius: 15px;
  max-width: 90%;
  width: fit-content;
  font-size: 16px;
  line-height: 1.8;
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
/*晚间更新至最底 参考文件样式 */
.reference-files-container {
  margin-top: 15px;
  border-top: 1px solid #eaeaea;
  padding-top: 12px;
}

.reference-files h4 {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.reference-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.reference-item {
  background-color: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 10px;
  width: calc(50% - 5px);
  transition: all 0.2s;
}

.reference-item:hover {
  background-color: #f0f0f0;
  border-color: #ccc;
}

.reference-link {
  text-decoration: none;
  color: inherit;
  display: block;
}

.reference-title {
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 5px;
  font-size: 14px;
}

.reference-description {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.reference-similarity {
  font-size: 11px;
  color: #999;
  text-align: right;
}

.reference-source {
  font-size: 0.8em;
  color: #666;
  font-weight: normal;
  margin-left: 5px;
}

.reference-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8em;
  color: #666;
  margin-top: 5px;
}

.reference-source-tag {
  background-color: #f0f0f0;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 0.8em;
}


/* 参考资料样式 */
.reference-files-container {
  margin-top: 15px;
  border-top: 1px solid #eaeaea;
  padding-top: 12px;
}

.reference-files-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
}

.reference-file-item {
  margin-bottom: 8px;
}

.reference-file-link {
  display: flex;
  align-items: center;
  color: #409eff;
  cursor: pointer;
  text-decoration: none;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.reference-file-link:hover {
  background-color: #ecf5ff;
}

.reference-file-link .el-icon {
  margin-right: 8px;
}
</style>