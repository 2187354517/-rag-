<template>
  <div class="api-doc-container">
    <h1>API使用文档</h1>
    <div class="api-doc-content">
      <h2>概述</h2>
      <p>本项目提供了一系列API接口，用于实现基于RAG和大模型的数学问题解答系统。这些接口包括数学问题解答、相关问题推荐、参考资料检索、用户知识库管理等功能。</p>

      <h2>认证</h2>
      <p>所有API接口都需要进行身份验证。用户需要通过登录接口获取API密钥（Bearer Token），并在每个请求的请求头中包含该密钥。</p>

      <h3>登录</h3>
      <pre>
POST /auth
请求头：
  Content-Type: application/json
请求体：
  {
    "username": "用户名",
    "password": "密码"
  }
响应：
  {
    "access_token": "API密钥",
    "token_type": "bearer",
    "user_id": "用户ID",
    "status": "success"
  }
      </pre>

      <h3>注册</h3>
      <pre>
POST /register
请求头：
  Content-Type: application/json
请求体：
  {
    "username": "用户名",
    "password": "密码",
    "email": "邮箱"
  }
响应：
  {
    "access_token": "API密钥",
    "token_type": "bearer",
    "user_id": "用户ID",
    "status": "success"
  }
      </pre>

      <h2>核心API</h2>

      <h3>1. 数学问题解答</h3>
      <pre>
POST /v1/chat/completions
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: application/json
请求体：
  {
    "model": "DeepSeek-Math-7B-Instruct",
    "messages": [
      {"role": "user", "content": "请输入您的数学问题"}
    ],
    "max_tokens": 1024,
    "temperature": 0.6,
    "stream": true
  }
响应：
  流式响应：
    data: {"id": "chatcmpl-...", "object": "chat.completion.chunk", "created": 1700000000, "model": "DeepSeek-Math-7B-Instruct", "choices": [{"index": 0, "delta": {"content": "响应内容"}, "finish_reason": null}]}
    data: [DONE]
  非流式响应：
    {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "created": 1700000000,
      "model": "DeepSeek-Math-7B-Instruct",
      "choices": [
        {
          "message": {
            "role": "assistant",
            "content": "响应内容"
          },
          "finish_reason": "stop"
        }
      ]
    }
      </pre>

      <h3>2. 相关问题推荐</h3>
      <pre>
POST /v1/related_questions
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: application/json
请求体：
  {
    "question": "请输入您的数学问题"
  }
响应：
  {
    "related_questions": ["相关问题1", "相关问题2", "相关问题3"],
    "status": "success",
    "message": ""
  }
      </pre>

      <h3>3. OCR图片识别</h3>
      <pre>
POST /v1/ocr
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: multipart/form-data
表单数据：
  image: 图片文件
  prompt: "提取图片中的数学公式和文字" (可选)
响应：
  {
    "status": "success",
    "text": "识别出的文本内容",
    "elapsed": 处理时间(秒)
  }
      </pre>

      <h3>4. 保存问题</h3>
      <pre>
POST /v1/questions
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: application/json
请求体：
  {
    "content": "请输入您的数学问题",
    "conversation_id": "会话ID（可选）"
  }
响应：
  {
    "question_id": "问题ID",
    "status": "success"
  }
      </pre>

      <h3>5. 参考资料检索</h3>
      <pre>
GET /v1/reference_files
请求头：
  Authorization: Bearer {API密钥}
查询参数：
  question_id: 问题ID（可选）
  query: 查询内容（可选）
响应：
  {
    "reference_files": [
      {
        "file_name": "文件名",
        "file_path": "文件路径",
        "file_type": "文件类型",
        "description": "文件描述",
        "similarity": 0.8,
        "source": "local",
        "download_url": "/api/download?file_path=文件名"
      }
    ],
    "status": "success",
    "source": "local_knowledge_base"
  }
      </pre>

      <h3>6. 下载文件</h3>
      <pre>
GET /api/download
请求头：
  Authorization: Bearer {API密钥}
查询参数：
  file_path: 文件路径
响应：
  文件流下载
      </pre>

      <h2>会话管理</h2>

      <h3>1. 创建会话</h3>
      <pre>
POST /conversations
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: application/json
请求体：
  {
    "title": "会话标题（可选）"
  }
响应：
  {
    "conversation_id": "会话ID"
  }
      </pre>

      <h3>2. 获取所有会话</h3>
      <pre>
GET /conversations
请求头：
  Authorization: Bearer {API密钥}
响应：
  [
    {
      "title": "会话标题",
      "messages": [消息列表],
      "conversation_id": "会话ID"
    }
  ]
      </pre>

      <h3>3. 获取会话消息</h3>
      <pre>
GET /conversations/{conversation_id}/messages
请求头：
  Authorization: Bearer {API密钥}
响应：
  {
    "messages": [消息列表]
  }
      </pre>

      <h3>4. 创建消息</h3>
      <pre>
POST /conversations/{conversation_id}/messages
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: application/json
请求体：
  {
    "role": "user/assistant",
    "content": "消息内容"
  }
响应：
  {
    "message_id": "消息ID"
  }
      </pre>

      <h3>5. 更新会话</h3>
      <pre>
PATCH /conversations/{conversation_id}
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: application/json
请求体：
  {
    "title": "新标题"
  }
响应：
  {
    "status": "success",
    "message": "会话更新成功"
  }
      </pre>

      <h3>6. 删除会话</h3>
      <pre>
DELETE /conversations/{conversation_id}
请求头：
  Authorization: Bearer {API密钥}
响应：
  {
    "status": "success",
    "message": "会话删除成功"
  }
      </pre>

      <h2>API密钥管理</h2>
      <pre>
GET /api-keys
请求头：
  Authorization: Bearer {API密钥}
响应：
  {
    "data": [
      {
        "id": "key_1",
        "user_id": "用户ID",
        "api_key": "API密钥",
        "created_at": "创建时间",
        "last_used": "最后使用时间"
      }
    ]
  }

POST /api-keys
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: application/json
请求体：
  {
    "action": "create/revoke",
    "key": "要撤销的密钥（仅revoke时需要）"
  }
响应（create）：
  {
    "status": "success",
    "message": "密钥生成成功",
    "data": {
      "api_key": "新API密钥",
      "created_at": "创建时间",
      "last_used": null
    }
  }
响应（revoke）：
  {
    "status": "success",
    "message": "密钥已删除"
  }
      </pre>

      <h2>用户知识库管理</h2>

      <h3>1. 上传文档</h3>
      <pre>
POST /user-knowledge/upload
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: multipart/form-data
表单数据：
  file: 文件（支持pdf, txt, jsonl, json）
响应：
  {
    "status": "success",
    "message": "文件上传成功"
  }
      </pre>

      <h3>2. 获取文档列表</h3>
      <pre>
GET /user-knowledge/list
请求头：
  Authorization: Bearer {API密钥}
查询参数：
  page: 页码（默认1）
  page_size: 每页数量（默认10，最大100）
响应：
  {
    "status": "success",
    "data": {
      "documents": [
        {
          "id": "文档ID",
          "file_name": "文件名",
          "file_size": 文件大小,
          "file_type": "文件类型",
          "created_at": "创建时间"
        }
      ],
      "total": 总数,
      "page": 当前页码,
      "page_size": 每页数量
    }
  }
      </pre>

      <h3>3. 获取文档内容</h3>
      <pre>
GET /user-knowledge/get/{filename}
请求头：
  Authorization: Bearer {API密钥}
响应：
  {
    "status": "success",
    "content": "文件内容"
  }
      </pre>

      <h3>4. 更新文档</h3>
      <pre>
PATCH /user-knowledge/update
请求头：
  Authorization: Bearer {API密钥}
  Content-Type: application/json
查询参数：
  filename: 文件名
请求体：
  "新文件内容"
响应：
  {
    "status": "success",
    "message": "文件更新成功"
  }
      </pre>

      <h3>5. 下载文档</h3>
      <pre>
GET /user-knowledge/download/{filename}
请求头：
  Authorization: Bearer {API密钥}
响应：
  文件流下载
      </pre>

      <h3>6. 删除文档</h3>
      <pre>
DELETE /user-knowledge/delete/{doc_id}
请求头：
  Authorization: Bearer {API密钥}
响应：
  {
    "status": "success",
    "message": "文件删除成功"
  }
      </pre>

      <h2>响应格式</h2>
      <p>所有API响应均以JSON格式返回，包含以下字段：</p>
      <ul>
        <li>status: 请求处理状态（success/error）</li>
        <li>message: 状态信息（通常在出错时提供详细信息）</li>
        <li>data: 响应数据（根据具体接口而定）</li>
      </ul>

      <h2>错误处理</h2>
      <p>当请求失败时，响应将包含错误信息和相应的HTTP状态码。常见的错误状态码包括：</p>
      <ul>
        <li>400: 请求参数错误</li>
        <li>401: 未授权（无效的API密钥）</li>
        <li>403: 无权限访问</li>
        <li>404: 资源未找到</li>
        <li>413: 文件大小超过限制</li>
        <li>500: 服务器内部错误</li>
      </ul>

      <h2>附录</h2>
      <ul>
        <li>API版本：2.1.0</li>
        <li>部署环境：云服务器或本地服务器</li>
        <li>支持的模型：DeepSeek-Math-7B-Instruct、Qwen2-Math等</li>
        <li>知识库数据量：不少于2000条</li>
        <li>OCR支持：支持图片中的数学公式识别</li>
        <li>文件限制：上传文件最大20MB</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.api-doc-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
  line-height: 1.6;
}

.api-doc-container h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}

.api-doc-container h2 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #444;
}

.api-doc-container h3 {
  margin-top: 15px;
  margin-bottom: 5px;
  color: #555;
}

.api-doc-container p {
  margin-bottom: 15px;
}

.api-doc-container ul {
  margin-bottom: 15px;
  padding-left: 20px;
}

.api-doc-container li {
  margin-bottom: 5px;
}

.api-doc-container pre {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 5px;
  overflow-x: auto;
  font-family: monospace;
  margin-bottom: 20px;
  white-space: pre-wrap;
}
</style>