<template>
  <div class="user-knowledge-container">
    <!-- 头部操作区 -->
    <div class="header-section">
      <div class="title-group">
        <h1 class="page-title">
          <el-icon class="title-icon"><FolderOpened /></el-icon>
          我的知识库
        </h1>
        <p class="page-subtitle">管理您的私有文档资源</p>
      </div>

      <div class="header-actions">
        <el-upload
          class="upload-demo"
          :action="uploadConfig.url"
          :headers="uploadConfig.headers"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :show-file-list="false"
          :before-upload="beforeUpload"
          accept=".pdf,.json,.txt,.jsonl"
        >
          <el-button type="primary" :icon="Upload">上传文档</el-button>
        </el-upload>

        <el-button 
          type="text" 
          :icon="Refresh" 
          @click="loadDocuments"
          :loading="loading"
          style="margin-left: 16px"
        >
          刷新
        </el-button>
      </div>
    </div>

    <!-- 文档列表 -->
    <el-card class="documents-card" shadow="never">
      <el-table
        :data="documents"
        v-loading="loading"
        style="width: 100%"
        empty-text="暂无文档，请点击上方按钮上传"
        stripe
        :default-sort="{ prop: 'file_name', order: 'ascending' }"
      >
        <el-table-column prop="file_name" label="文件名" sortable min-width="300">
          <template #default="{ row }">
            <div class="file-name-cell">
              <el-icon class="file-icon">
                <component :is="getFileIcon(row.file_name)" />
              </el-icon>
              <el-tooltip 
                :content="row.file_name" 
                placement="top" 
                :disabled="row.file_name.length < 30"
              >
                <span class="file-name">{{ truncateFileName(row.file_name) }}</span>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="file_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag effect="plain">{{ row.file_type.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="file_size" label="大小" width="120" sortable>
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="上传时间" width="200" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" align="right">
          <template #default="{ row }">
            <el-button-group>
              <el-tooltip content="查看内容" placement="top">
                <el-button 
                  size="small" 
                  @click="showContent(row.file_name)"
                  :icon="View"
                  circle
                >
                  <component :is="View" />
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="下载文件" placement="top">
                <el-button 
                  size="small" 
                  @click="downloadDocument(row)"
                  circle
                >
                  <component :is="Download" />
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="删除文件" placement="top">
                <el-button 
                  size="small" 
                  @click="deleteDocument(row.id)"
                  circle
                  type="danger"
                >
                  <component :is="Delete" />
                </el-button>
              </el-tooltip>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadDocuments"
          @current-change="loadDocuments"
        />
      </div>
    </el-card>

    <!-- 文件内容对话框 -->
    <el-dialog 
      v-model="contentVisible" 
      :title="`文件内容 - ${currentFileName}`" 
      width="70%"
      top="5vh"
      destroy-on-close
    >
      <div class="file-content-wrapper">
        <el-scrollbar height="65vh">
          <pre v-if="fileContent" class="file-content">{{ fileContent }}</pre>
          <el-empty v-else description="空文件内容" />
        </el-scrollbar>
      </div>
      
      <template #footer>
        <el-button @click="contentVisible = false">关闭</el-button>
        <el-button 
          type="primary" 
          @click="editDocument(currentFileName)"
          v-if="fileContent"
        >
          编辑内容
        </el-button>
      </template>
    </el-dialog>

    <!-- 上传提示 -->
    <el-dialog v-model="uploadTipVisible" title="上传说明" width="500px">
      <div class="upload-tip-content">
        <h4>支持的文件类型：</h4>
        <el-tag 
          v-for="type in allowedTypes" 
          :key="type" 
          class="type-tag"
          type="info"
        >
          .{{ type }}
        </el-tag>

        <h4 style="margin-top: 20px;">注意事项：</h4>
        <ul class="tip-list">
          <li>单个文件大小不超过 20MB</li>
          <li>建议使用明确命名的文件名</li>
          <li>敏感文件请先加密处理</li>
        </ul>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { 
  FolderOpened, Upload, Document, View, Refresh,
  Picture, Notebook, Tickets, Files,
  Download, Delete
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiRequest,fileUploadRequest } from '@/utils/request.js'

// 响应式数据
const documents = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const contentVisible = ref(false)
const fileContent = ref('')
const currentFileName = ref('')
const uploadTipVisible = ref(false)

// 常量配置
const allowedTypes = ['pdf', 'json', 'txt', 'jsonl']
const maxFileSize = 20 * 1024 * 1024 // 20MB

// 计算属性
const uploadConfig = computed(() => {
  const token = localStorage.getItem('token')
  return {
    url: `/user-knowledge/upload`,
    headers: {
      Authorization: token ? `Bearer ${token}` : ''
    }
  }
})


// 生命周期钩子
onMounted(() => {
  loadDocuments()
})

// 方法
const loadDocuments = async () => {
  try {
    loading.value = true
    const res = await apiRequest({
      url: '/user-knowledge/list',
      method: 'GET',
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })

    if (res.data) {
      documents.value = res.data.documents || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    ElMessage.error(`加载失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// 方法
const beforeUpload = (file) => {
  const fileType = file.name.split('.').pop().toLowerCase()
  const isValidType = allowedTypes.includes(fileType)
  const isValidSize = file.size <= maxFileSize

  if (!isValidType) {
    ElMessage.error(`不支持的文件类型: ${fileType}`)
    uploadTipVisible.value = true
    return false
  }

  if (!isValidSize) {
    ElMessage.error('文件大小超过20MB限制')
    return false
  }

  // 显示上传进度提示
  const progressMessage = ElMessage({
    type: 'info',
    message: '文件上传中...',
    duration: 0
  })

  fileUploadRequest(
    uploadConfig.value.url,
    file,
    uploadConfig.value.headers,
    (message, isDone) => {
      if (isDone) {
        progressMessage.close()
        if (message.includes('成功')) {
          ElMessage.success(message)
          loadDocuments()
        } else {
          ElMessage.error(message)
        }
      }
    },
    () => {
      // 上传完成后的清理工作
    }
  )

  return false
}
const handleUploadSuccess = (response) => {
  if (response.status === 'success') {
    ElMessage.success('上传成功')
    loadDocuments()
  }
}

const handleUploadError = (error) => {
  ElMessage.error(`上传失败: ${error.message}`)
}

const deleteDocument = async (docId) => {  
  try {
    await ElMessageBox.confirm(
      '确定要删除此文档吗？此操作不可恢复。',
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await apiRequest({
      url: `/user-knowledge/delete/${docId}`,
      method: 'DELETE'
    })
    
    if (response.status === 'success') {
      ElMessage.success('删除成功')
      loadDocuments()
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`删除失败: ${error.message}`)
    }
  }
}
const downloadDocument = async (doc) => {
  try {
    loading.value = true
    const response = await apiRequest({
      url: `/user-knowledge/download/${encodeURIComponent(doc.file_name)}`,
      method: 'GET',
      responseType: 'blob' // 确保返回blob类型
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', doc.file_name)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载失败: ' + error.message)
    console.error('下载错误:', error)
  } finally {
    loading.value = false
  }
}


const showContent = async (filename) => {
  try {
    loading.value = true
    const response = await apiRequest(`/user-knowledge/get/${filename}`)
    fileContent.value = response.content
    currentFileName.value = filename
    contentVisible.value = true
  } catch (error) {
    ElMessage.error('获取文件内容失败')
    console.error(error) // 使用 error 调试
  } finally {
    loading.value = false
  }
}

const editDocument = async (filename) => {
  try {
    const contentRes = await apiRequest(`/user-knowledge/get/${filename}`)
    
    ElMessageBox.prompt('编辑文件内容', `编辑 ${filename}`, {
      inputType: 'textarea',
      inputValue: contentRes.content,
      inputPlaceholder: '请输入文件内容',
      customClass: 'edit-dialog',
      inputValidator: (value) => {
        if (!value || value.trim() === '') {
          return '内容不能为空'
        }
        return true
      }
    }).then(async ({ value }) => {
      try {
        await apiRequest({
          url: `/user-knowledge/update?filename=${encodeURIComponent(filename)}`,
          method: 'PATCH',
          data: { content: value }
        })
        ElMessage.success('文件更新成功')
        loadDocuments()
      } catch (error) {
        ElMessage.error('文件更新失败')
        console.error(error) // 使用 error 调试
      }
    })
  } catch (error) {
    ElMessage.error('获取文件内容失败')
    console.error(error) // 使用 error 调试
  }
}

// 辅助方法
const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  switch (ext) {
    case 'pdf': return Picture
    case 'txt': return Notebook
    case 'json': return Tickets
    case 'jsonl': return Files
    default: return Document
  }
}

const truncateFileName = (name) => {
  return name.length > 30 ? name.substring(0, 27) + '...' : name
}

const formatFileSize = (size) => {
  if (!size) return '-'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const formatDateTime = (timestamp) => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped lang="scss">
.user-knowledge-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;

  .header-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    .title-group {
      .page-title {
        display: flex;
        align-items: center;
        font-size: 24px;
        margin: 0 0 8px 0;

        .title-icon {
          margin-right: 12px;
          color: var(--el-color-primary);
          font-size: 28px;
        }
      }

      .page-subtitle {
        margin: 0;
        color: var(--el-text-color-secondary);
        font-size: 14px;
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
    }
  }

  .documents-card {
    margin-top: 24px;
    border-radius: 8px;

    :deep(.el-card__body) {
      padding: 0;
    }

    .file-name-cell {
      display: flex;
      align-items: center;

      .file-icon {
        margin-right: 12px;
        font-size: 20px;
        color: var(--el-color-primary);
      }

      .file-name {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .pagination-wrapper {
      padding: 16px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .file-content-wrapper {
    background-color: var(--el-fill-color-lighter);
    border-radius: 6px;
    padding: 16px;

    .file-content {
      margin: 0;
      font-family: 'Menlo', 'Consolas', monospace;
      font-size: 13px;
      line-height: 1.6;
      color: var(--el-text-color-primary);
      white-space: pre-wrap;
      word-break: break-word;
    }
  }

  .upload-tip-content {
    .type-tag {
      margin: 8px 8px 0 0;
    }

    .tip-list {
      padding-left: 20px;
      color: var(--el-text-color-secondary);

      li {
        line-height: 1.8;
      }
    }
  }
}
.edit-dialog {
  width: 80%;
  max-width: 800px;
  
  .el-message-box__content {
    padding: 20px;
  }
  
  .el-textarea__inner {
    min-height: 300px;
    font-family: 'Menlo', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.5;
  }
}
</style>