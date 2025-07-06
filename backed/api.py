from urllib.parse import quote
import time
import logging
import sys
import os
import json
import uuid
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, Literal

import tempfile
import io
from fastapi import FastAPI, HTTPException, Depends, Query, Security, Request, File, UploadFile, Body
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from enhanced_rag import EnhancedRAG
from auth import Auth
from constants import HISTORY_LIMIT, KNOWLEDGE_BASE_DIR, MULTILINGUAL_MODEL_NAME
from search_engine import SearchEngine
from knowledge_processor import EnhancedKnowledgeProcessor
from sentence_transformers import SentenceTransformer
# 初始化模型（建议放在全局）
sentence_model = SentenceTransformer(MULTILINGUAL_MODEL_NAME)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(levelname)s - %(module)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

app = FastAPI(
    title="Math Problem Solving API",
    description="基于RAG和大模型的数学问题解答系统",
    version="2.1.0"
)

auth = Auth()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 定义安全方案
security_scheme = HTTPBearer()

# API密钥验证依赖
async def get_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """验证API密钥"""
    if credentials is None:
        # 放行OPTIONS预检请求
        if request.method == 'OPTIONS':
            return None
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return credentials.credentials

# 定义请求模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    model: str
    messages: list
    max_tokens: int = 1024
    temperature: float = 0.6
    stream: bool = False

class RelatedQuestionsRequest(BaseModel):
    """相关问题请求模型"""
    question: str

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str

class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str
    password: str
    email: str

class AuthResponse(BaseModel):
    """认证响应模型"""
    access_token: str
    token_type: str = "bearer"
    user_id: Union[int, str]
    status: str = "success"

class ErrorResponse(BaseModel):
    """错误响应模型"""
    status: str = "error"
    message: str

class CreateConversationRequest(BaseModel):
    """创建会话请求模型"""
    title: Optional[str] = None

class MessageCreateRequest(BaseModel):
    """创建消息请求模型"""
    role: str
    content: str

class UpdateConversationRequest(BaseModel):
    """更新会话请求模型"""
    title: Optional[str] = None

class APIKeyAction(BaseModel):
    """API密钥操作模型"""
    action: Literal["create", "revoke"]
    key: Optional[str] = None

class QuestionRequest(BaseModel):
    """问题请求模型"""
    content: str
    conversation_id: Optional[int] = None

# 初始化RAG
rag = EnhancedRAG()

# 初始化搜索引擎
search_engine = SearchEngine()

# 聊天补全接口
@app.post("/v1/chat/completions")
async def chat_completions(
        request: ChatRequest,
        api_key: str = Security(get_api_key)
):
    """处理聊天补全请求（支持流式和非流式）"""
    # 验证和初始化
    logging.info(f"收到请求: model={request.model}, stream={request.stream}")
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 1. 处理对话历史
        valid_history = []
        last_user_msg = None
        expected_role = "user"

        for msg in reversed(request.messages[-HISTORY_LIMIT*2:]):
            if msg["role"] == "user":
                last_user_msg = msg
                if expected_role == "user":
                    valid_history.insert(0, msg)
                    expected_role = "assistant"
            elif msg["role"] == "assistant" and expected_role == "assistant":
                valid_history.insert(0, msg)
                expected_role = "user"

        if last_user_msg and (not valid_history or valid_history[-1]["role"] != "user"):
            valid_history.append(last_user_msg)

        if not valid_history or len(valid_history[-1]["content"]) < 1:
            raise HTTPException(status_code=400, detail="无效的问题输入")

        # 2. 流式响应处理
        if request.stream:
            async def stream_response():
                start_time = time.time()
                full_response = ""
                
                try:
                    async for chunk in rag.ask_stream(valid_history[-1]["content"], valid_history):
                        response_data = {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": request.model,
                            "choices": [ {
                                "index": 0,
                                "delta": {"content": chunk},
                                "finish_reason": None
                            } ]
                        }
                        yield f"data: {json.dumps(response_data)}\n\n"
                    
                    yield "data: [DONE]\n\n"

                except Exception as e:
                    error_msg = f"流式响应错误: {str(e)}"
                    yield f"data: {json.dumps({'error': error_msg})}\n\n"
                    yield "data: [DONE]\n\n"
                    
                    logging.info(f"流式响应完成 | 长度: {len(full_response)} | 耗时: {time.time()-start_time:.2f}s")
                
                except Exception as e:
                    logging.error(f"流式生成异常: {str(e)}", exc_info=True)
                    error_data = {
                        "error": {
                            "message": f"Stream generation error: {str(e)}",
                            "type": "api_error"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    yield "data: [DONE]\n\n"

            return StreamingResponse(
                stream_response(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )

        # 3. 非流式响应处理
        else:
            start_time = time.time()
            response = await rag.ask(valid_history[-1]["content"], valid_history)
            
            inputs = rag.tokenizer(rag.last_prompt or "", return_tensors="pt")
            prompt_tokens = inputs["input_ids"].shape[1]
            
            logging.info(f"非流式响应 | 耗时: {time.time()-start_time:.2f}s")
            
            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [ {
                    "message": {
                        "role": "assistant",
                        "content": response
                    },
                    "finish_reason": "stop"
                } ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": len(rag.tokenizer.encode(response)),
                    "total_tokens": prompt_tokens + len(rag.tokenizer.encode(response))
                }
            }

    except Exception as e:
        logging.error(f"请求处理失败：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")

# 相关问题接口
@app.post("/v1/related_questions",
          summary="获取相关问题接口",
          response_description="包含与输入问题相关的问题列表")
async def related_questions(
        request: RelatedQuestionsRequest,
        api_key: str = Security(get_api_key)
):
    """获取相关问题"""
    # 验证 API 密钥
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 调用大模型生成相关问题
        related_questions = await rag.generate_related_questions(request.question)
        return {
            "related_questions": related_questions,
            "status": "success",
            "message": ""
        }
    except Exception as e:
        logging.error(f"获取相关问题时发生错误: {str(e)}", exc_info=True)
        return {
            "related_questions": [],
            "status": "error",
            "message": f"获取相关问题时发生错误: {str(e)}"
        }

# 登录接口
@app.post("/auth")
async def authenticate_user(request: LoginRequest):
    """用户登录"""
    try:
        status, result = auth.login_user(request.username, request.password)
        if not status:
            return JSONResponse(
                status_code=401,
                content={"status": "error", "message": result}
            )

        return JSONResponse(
            status_code=200,
            content={
                "access_token": result["api_key"],
                "token_type": "bearer",
                "user_id": result["user_id"],
                "status": "success"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(e)}
        )

# 注册接口
@app.post("/register",
          response_model=AuthResponse,
          responses={400: {"model": ErrorResponse}} ,
          summary="用户注册接口",
          description="注册新用户账号")
async def register_user(request: RegisterRequest):
    """用户注册"""
    try:
        status, result = auth.register_user(
            request.username,
            request.password,
            request.email
        )
        if not status:
            raise HTTPException(
                status_code=400,
                detail={"message": result}
            )

        return {
            "access_token": result["api_key"],
            "user_id": result["user_id"]
        }
    except Exception as e:
        logging.error(f"注册失败: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={"message": f"注册失败: {str(e)}"}
        )

# 创建会话接口
@app.post("/conversations",
          summary="创建新会话",
          response_description="返回新创建的会话ID")
async def create_conversation(
    request: CreateConversationRequest,
    api_key: str = Security(get_api_key)
):
    """创建新会话"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(401, "无效的API密钥")

    try:
        conv_id = auth.db.create_conversation(user_id, request.title)
        return {"conversation_id": conv_id}
    except Exception as e:
        logging.error(f"创建会话失败: {str(e)}")
        raise HTTPException(500, "服务器内部错误")

# 获取用户所有会话接口
@app.get("/conversations",
         summary="获取用户的所有会话",
         response_description="返回用户的所有会话列表，包含会话标题、ID 和消息记录")
async def get_all_conversations(
    api_key: str = Security(get_api_key)
):
    """获取用户的所有会话"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(401, "无效的API密钥")

    try:
        # 获取用户的所有会话
        conversations = auth.db.get_conversations(user_id)
        result = []
        for conversation in conversations:
            conversation_id = conversation['id']
            # 获取每个会话的消息
            messages = auth.db.get_messages(conversation_id)
            result.append({
                "title": conversation['title'],
                "messages": messages,
                "conversation_id": conversation_id
            })
        return result
    except Exception as e:
        logging.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(500, "服务器内部错误")

# 获取会话消息接口
@app.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    api_key: str = Security(get_api_key)
):
    """获取会话消息"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    cursor = auth.db.connection.cursor()
    try:
        cursor.execute("SELECT user_id FROM conversations WHERE id = %s", (conversation_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="会话不存在")
        if result[0] != user_id:
            raise HTTPException(status_code=403, detail="无权限访问该会话")

        messages = auth.db.get_messages(conversation_id)
        return {"messages": messages}
    finally:
        cursor.close()

# 创建会话消息接口
@app.post("/conversations/{conversation_id}/messages")
async def create_message(
    conversation_id: int,
    request: MessageCreateRequest,
    api_key: str = Security(get_api_key)
):
    """创建会话消息"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(401, "无效的API密钥")

    # 验证会话归属
    cursor = auth.db.connection.cursor()
    try:
        cursor.execute("SELECT user_id FROM conversations WHERE id = %s", (conversation_id,))
        result = cursor.fetchone()
        if not result or result[0] != user_id:
            raise HTTPException(403, "无权限操作此会话")

        # 保存消息到数据库
        message_id = auth.db.add_message(conversation_id, request.role, request.content)
        return {"message_id": message_id}
    finally:
        cursor.close()

# 更新会话接口
@app.patch("/conversations/{conversation_id}",
          summary="更新会话信息",
          response_description="返回操作结果")
async def update_conversation(
    conversation_id: int,
    request: UpdateConversationRequest,
    api_key: str = Security(get_api_key)
):
    """更新会话信息"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(401, "无效的API密钥")

    cursor = auth.db.connection.cursor()
    try:
        # 验证会话归属
        cursor.execute("SELECT user_id FROM conversations WHERE id = %s", (conversation_id,))
        result = cursor.fetchone()
        if not result or result[0] != user_id:
            raise HTTPException(403, "无权限操作此会话")

        # 更新标题
        update_query = "UPDATE conversations SET title = %s WHERE id = %s"
        cursor.execute(update_query, (request.title, conversation_id))
        auth.db.connection.commit()
        return {"status": "success", "message": "会话更新成功"}
    except Exception as e:
        auth.db.connection.rollback()
        logging.error(f"更新会话失败: {str(e)}")
        raise HTTPException(500, "服务器内部错误")
    finally:
        cursor.close()

# 删除会话接口
@app.delete("/conversations/{conversation_id}",
           summary="删除会话",
           response_description="返回操作结果")
async def delete_conversation(
    conversation_id: int,
    api_key: str = Security(get_api_key)
):
    """删除会话"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(401, "无效的API密钥")

    cursor = auth.db.connection.cursor()
    try:
        # 验证会话归属
        cursor.execute("SELECT user_id FROM conversations WHERE id = %s", (conversation_id,))
        result = cursor.fetchone()
        if not result or result[0] != user_id:
            raise HTTPException(403, "无权限操作此会话")

        # 删除关联消息
        cursor.execute("DELETE FROM messages WHERE conversation_id = %s", (conversation_id,))
        # 删除会话
        cursor.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
        auth.db.connection.commit()
        return {"status": "success", "message": "会话删除成功"}
    except Exception as e:
        auth.db.connection.rollback()
        logging.error(f"删除会话失败: {str(e)}")
        raise HTTPException(500, "服务器内部错误")
    finally:
        cursor.close()

# 管理API密钥接口
@app.get("/api-keys",
         summary="获取API密钥列表")
@app.post("/api-keys",
          summary="管理API密钥")
async def manage_api_keys(
    request: Optional[APIKeyAction] = None,
    api_key: str = Security(get_api_key)
):
    """管理API密钥"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    # GET 请求：返回所有密钥
    if not request:
        keys = auth.db.get_all_api_keys(user_id)
        formatted_keys = [ {
            "id": f"key_{idx}",
            "user_id": user_id,
            "api_key": k["api_key"],
            "created_at": k["created_at"].strftime("%Y-%m-%d %H:%M:%S") if k["created_at"] else None,
            "last_used": k["last_used"].strftime("%Y-%m-%d %H:%M:%S") if k["last_used"] else None
        } for idx, k in enumerate(keys, 1) ]
        return {"data": formatted_keys}

    # POST 请求：创建密钥
    if request.action == "create":
        new_key = auth.generate_api_key(user_id)
        return {
            "status": "success",
            "message": "密钥生成成功",
            "data": {
                "api_key": new_key,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_used": None
            }
        }
    elif request.action == "revoke" and request.key:
        success = auth.db.delete_api_key(user_id, request.key)
        return {
            "status": "success" if success else "error",
            "message": "密钥已删除" if success else "删除失败"
        }

    raise HTTPException(status_code=400, detail="无效的操作类型")

# 获取参考资料接口
@app.get("/v1/reference_files")
async def reference_files(
    question_id: str = Query(None),
    query: str = Query(None),
    api_key: str = Security(get_api_key)
):
    """检索参考文件"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")
    
    try:
        logging.info(f"正在检索知识库目录: {KNOWLEDGE_BASE_DIR}")
        logging.info(f"查询内容: {query}")
        
        knowledge_files = []
        
        # 从知识库目录获取文件列表
        if os.path.exists(KNOWLEDGE_BASE_DIR):
            # 如果有查询内容，编码查询文本
            query_embedding = sentence_model.encode(query) if query else None
            
            for filename in os.listdir(KNOWLEDGE_BASE_DIR):
                file_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # 计算相似度
                            similarity = 0.0
                            if query_embedding is not None:
                                # 对文件内容进行编码
                                content_embedding = sentence_model.encode(content[:512])  # 取前512个字符避免内容过长
                                similarity = np.dot(query_embedding, content_embedding) / (
                                    np.linalg.norm(query_embedding) * np.linalg.norm(content_embedding)
                                )
                            
                        knowledge_files.append({
                            "file_name": filename,
                            "file_path": filename,
                            "file_type": filename.split('.')[-1].lower(),
                            "description": f"本地知识库文件: {filename}",
                            "similarity": float(similarity),  # 转换为 Python float
                            "source": "local",
                            "download_url": f"/api/download?file_path={filename}"
                        })
                    except Exception as e:
                        logging.warning(f"无法读取文件内容: {file_path}, 错误: {str(e)}")
                        continue
        
        # 如果有查询，按相似度排序并只返回前三个最相关的文件
        if query and knowledge_files:
            knowledge_files.sort(key=lambda x: x['similarity'], reverse=True)
            knowledge_files = knowledge_files[:3]
        
        # 如果提供了问题ID，保存参考资料到数据库
        if question_id and knowledge_files:
            auth.db.save_reference_files(question_id, knowledge_files)
        
        return {
            "status": "success",
            "reference_files": knowledge_files,
            "source": "local_knowledge_base"
        }
        
    except Exception as e:
        logging.error(f"获取参考文件时发生错误: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

# 添加文件下载接口
@app.get("/api/download")
async def download_file(
    file_path: str = Query(..., description="文件路径"),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    """下载文件接口"""
    try:
        # 验证token
        token = credentials.credentials
        if not auth.db.validate_api_key(token):
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # 清理文件路径，只保留文件名
        filename = os.path.basename(file_path)
        
        # 添加详细的调试日志
        logging.info(f"请求下载文件: {filename}")
        logging.info(f"原始文件路径: {file_path}")
        logging.info(f"知识库目录: {KNOWLEDGE_BASE_DIR}")
        
        # 构建完整的文件路径
        full_path = os.path.join(KNOWLEDGE_BASE_DIR, filename)
        logging.info(f"完整文件路径: {full_path}")
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            if os.path.exists(KNOWLEDGE_BASE_DIR):
                existing_files = os.listdir(KNOWLEDGE_BASE_DIR)
                logging.error(f"目录存在，但文件不存在。目录中的文件列表: {existing_files}")
            else:
                logging.error(f"知识库目录不存在: {KNOWLEDGE_BASE_DIR}")
            raise HTTPException(
                status_code=404, 
                detail=f"文件不存在: {filename}"
            )
        
        # 返回文件流
        return StreamingResponse(
            open(full_path, "rb"),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename*=UTF-8\'\'{quote(filename)}',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except Exception as e:
        logging.error(f"下载文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 保存问题接口
@app.post("/v1/questions",
          summary="保存问题并获取问题ID",
          response_description="返回生成的问题ID")
async def save_question(
    request: QuestionRequest,
    api_key: str = Security(get_api_key)
):
    """保存问题并获取问题ID"""
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")
    
    try:
        # 生成唯一的问题ID
        question_id = str(uuid.uuid4())
        
        # 保存问题到数据库
        success = auth.db.save_question(
            question_id=question_id,
            user_id=user_id,
            content=request.content,
            conversation_id=request.conversation_id
        )
        
        if not success:
            # 如果数据库保存失败，尝试保存到文件系统作为备份
            cache_dir = Path("question_cache")
            cache_dir.mkdir(exist_ok=True)
            
            with open(cache_dir / f"{question_id}.json", "w", encoding="utf-8") as f:
                json.dump({
                    "user_id": user_id,
                    "content": request.content,
                    "conversation_id": request.conversation_id,
                    "timestamp": time.time()
                }, f, ensure_ascii=False)
            
            logging.warning(f"问题保存到数据库失败，已保存到文件系统: {question_id}")
        else:
            logging.info(f"问题已保存到数据库: {question_id}")
            
            # 执行搜索并保存参考资料
            try:
                # 使用搜索引擎搜索相关资料
                search_results = await search_engine.search(request.content, max_results=5)
                
                if search_results:
                    # 保存参考资料到数据库
                    auth.db.save_reference_files(question_id, search_results)
                    logging.info(f"参考资料已保存到数据库: {question_id}")
            except Exception as search_error:
                logging.error(f"搜索和保存参考资料失败: {str(search_error)}")
        
        return {
            "question_id": question_id,
            "status": "success"
        }
    except Exception as e:
        logging.error(f"保存问题时发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存问题失败: {str(e)}")



#/*************************更新*************************/

# 新增用户知识库目录基础路径
USER_KNOWLEDGE_BASE_DIR = r"E:\math-ai\knowledge_base\user_knowledge"

# 获取用户文档内容接口
@app.get("/user-knowledge/get/{filename}")
async def get_user_document(
    filename: str,
    api_key: str = Security(get_api_key)
):
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    # 构建用户专属目录路径
    user_dir = os.path.join(USER_KNOWLEDGE_BASE_DIR, f"user_{user_id}")
    
    # 如果用户目录不存在，创建它
    os.makedirs(user_dir, exist_ok=True)
    
    try:
        file_path = os.path.join(user_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"status": "success", "content": content}
        else:
            raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        logging.error(f"读取用户文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail="读取文件失败")

# 修改后的上传接口
@app.post("/user-knowledge/upload")
async def upload_user_document(
    file: UploadFile = File(...),
    api_key: str = Security(get_api_key)
):
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    # 创建用户专属目录
    user_dir = os.path.join(USER_KNOWLEDGE_BASE_DIR, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    # 检查文件类型
    allowed_ext = {'pdf', 'txt', 'jsonl', 'json'}
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 检查文件大小
    max_size = 20 * 1024 * 1024  # 20MB
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置文件指针
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="文件大小超过20MB限制")

    try:
        # 检查文件是否已存在
        file_path = os.path.join(user_dir, file.filename)
        if os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="文件已存在")

        # 保存文件
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        file_size = os.path.getsize(file_path)
        success = auth.db.save_user_document(user_id, file.filename, file_path, file_ext, file_size)

        if not success:
            os.remove(file_path)  # 如果数据库保存失败，删除已上传的文件
            raise HTTPException(status_code=500, detail="保存文件记录失败")

        # 重新加载用户知识库
        rag.processor = EnhancedKnowledgeProcessor()
        rag.chunks = rag.processor.process_documents()
        
        return {"status": "success", "message": "文件上传成功"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"用户文件上传失败: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="上传文件失败")


# 修改后的文档列表接口
@app.get("/user-knowledge/list")
async def list_user_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    api_key: str = Security(get_api_key)
):
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")
    
    try:
        # 从数据库获取文档列表
        docs = auth.db.get_user_documents(user_id)
        
        # 转换为前端需要的格式
        documents = []
        for doc in docs:
            file_path = doc['file_path']
            if os.path.exists(file_path):
                documents.append({
                    "id": doc['id'],
                    "file_name": doc['file_name'],
                    "file_size": os.path.getsize(file_path),
                    "file_type": doc['file_type'],
                    "created_at": doc['created_at'].strftime("%Y-%m-%d %H:%M:%S") if doc['created_at'] else None
                })
        
        # 分页处理
        total = len(documents)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_docs = documents[start:end]
        
        return {
            "status": "success",
            "data": {
                "documents": paginated_docs,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }
    except Exception as e:
        logging.error(f"获取用户文档列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取文档列表失败")
# 编辑用户文档
@app.patch("/user-knowledge/update")
async def update_user_document(
    filename: str = Query(..., description="要更新的文件名"),
    content: str = Body(..., embed=True, description="新文件内容"),
    api_key: str = Security(get_api_key)
):
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 构建用户专属目录路径
        user_dir = os.path.join(USER_KNOWLEDGE_BASE_DIR, f"user_{user_id}")
        
        # 如果用户目录不存在，创建它
        os.makedirs(user_dir, exist_ok=True)
        
        # 获取文件扩展名
        file_ext = filename.split('.')[-1].lower()
        
        # 验证文件类型
        if file_ext in {'pdf', 'docx'}:
            raise HTTPException(status_code=400, detail="PDF和DOCX文件不支持直接编辑")
        if file_ext not in {'txt', 'md', 'json', 'jsonl'}:
            raise HTTPException(status_code=400, detail="不支持编辑该文件类型")

        # 构建完整路径
        file_path = os.path.join(user_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")

        # 写入新内容
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 重新加载知识库
        rag.processor = EnhancedKnowledgeProcessor()
        rag.chunks = rag.processor.process_documents()
        
        return {"status": "success", "message": "文件更新成功"}
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"更新用户文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="文件更新失败")

# 修改后的删除接口
@app.delete("/user-knowledge/delete/{doc_id}")
async def delete_user_document(
    doc_id: int,
    api_key: str = Security(get_api_key)
):
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(401, "无效的API密钥")

    try:
        # 先获取文件信息
        cursor = auth.db.connection.cursor(dictionary=True)
        cursor.execute("SELECT file_name, file_path FROM user_documents WHERE id = %s AND user_id = %s", 
                      (doc_id, user_id))
        doc = cursor.fetchone()
        
        if not doc:
            raise HTTPException(404, "文档不存在或无权访问")

        # 删除物理文件
        if os.path.exists(doc['file_path']):
            os.remove(doc['file_path'])
        
        # 删除数据库记录
        cursor.execute("DELETE FROM user_documents WHERE id = %s AND user_id = %s", 
                      (doc_id, user_id))
        auth.db.connection.commit()
        
        # 重新加载知识库
        rag.processor = EnhancedKnowledgeProcessor()
        rag.chunks = rag.processor.process_documents()
        
        return {"status": "success", "message": "文件删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        auth.db.connection.rollback()
        logging.error(f"删除用户文件失败: {str(e)}")
        raise HTTPException(500, detail=f"删除失败: {str(e)}")
    finally:
        cursor.close()


# 修改后的下载接口
@app.get("/user-knowledge/download/{filename}")
async def download_user_document(
    filename: str,
    api_key: str = Security(get_api_key)
):
    user_id = auth.db.validate_api_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    # 构建用户专属目录路径
    user_dir = os.path.join(USER_KNOWLEDGE_BASE_DIR, f"user_{user_id}")
    file_path = os.path.join(user_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 确定文件类型
    content_type = "application/octet-stream"
    if filename.endswith(".pdf"):
        content_type = "application/pdf"
    elif filename.endswith(".txt"):
        content_type = "text/plain"
    elif filename.endswith(".json"):
        content_type = "application/json"
    elif filename.endswith(".jsonl"):
        content_type = "application/jsonl"
    
    # 使用FileResponse返回文件
    return FileResponse(
        file_path,
        media_type=content_type,
        filename=filename
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)