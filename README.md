# -rag-
项目概述：

![image](https://github.com/user-attachments/assets/141348f1-7263-419e-9586-2b33e0af6778)

![image](https://github.com/user-attachments/assets/4a8cd8fb-8bfa-4e76-81f8-30ac8e8a9110)

当前数学问题解答领域面临诸多挑战：传统搜索引擎提供的答案往往零散且缺乏系统性，难以满足深度学习需求；人工辅导虽然精准但成本高昂且受时空限制；现有AI工具则普遍存在交互生硬、自然语言理解能力不足等问题。针对这些痛点，PolarSolve创新性地融合了RAG技术和大语言模型的优势，打造了一个智能化的数学问题解答平台。系统通过构建覆盖中小学到高等数学的结构化知识库，能够精准理解用户以自然语言提出的各类数学问题，并提供包含详细解题步骤的完整答案。其特色在于不仅给出最终结果，更注重展示完整的推理过程，支持多轮交互追问，真正实现了"授人以渔"的教学理念。该平台突破了传统工具的局限性，在准确性、易用性和交互体验等方面都具有显著优势，为数学学习者提供了一个随时可用的智能辅导助手，有效提升了学习效率和问题解决能力。
![image](https://github.com/user-attachments/assets/3ef2f89a-a67b-410c-bdda-e11a65e578de)
技术框架：
![image](https://github.com/user-attachments/assets/024ddfd7-f32d-43c1-a168-6b029dc0e60b)

![image](https://github.com/user-attachments/assets/e24ed4da-50c2-404f-a1be-ffad40dae2d1)

优势：
![image](https://github.com/user-attachments/assets/b5bef2a0-c74d-496a-b517-ae490b0ae567)
解决：
![image](https://github.com/user-attachments/assets/b72bcfea-5b94-40a9-9218-627a393a1e4d)

![image](https://github.com/user-attachments/assets/dcef5823-d358-4fc4-b60f-e3ce237a5351)

![image](https://github.com/user-attachments/assets/e05c1706-6eb7-484a-abfe-87ada66ee4d5)

![image](https://github.com/user-attachments/assets/39ed1a40-96ba-4952-8a7c-b0ac315d52f7)

![image](https://github.com/user-attachments/assets/f8c2cb0e-018f-436b-8a60-5ae27e217a45)

技术架构：

![image](https://github.com/user-attachments/assets/bbbb182a-d4b6-4576-bda9-4950be77083a)

系统结构：

![image](https://github.com/user-attachments/assets/ffd9bf78-3d99-44c9-8260-f1899a641d26)


概念模型：

![image](https://github.com/user-attachments/assets/0156a486-8280-4446-bbfe-3e2f74660078)


八、API接口
1.接口名称：authenticate_user
该接口用于用户登录，验证用户名和密码，并返回访问令牌（API 密钥）。这是用户访问其他受保护接口的前提。
表8-1接口authenticate_user表
字段	描述
请求方式	POST
URL	http://30de5fdf.r6.cpolar.cn/auth
请求头	Content-Type: application/json
请求参数	JSON 格式，包含以下字段：
字段: username
类型: String
必填: 是
描述: 用户名
字段: password
类型: String
必填: 是
描述: 密码
响应格式	JSON 格式，包含以下字段：
字段: access_token
类型: String
描述: 访问令牌
字段: token_type
类型: String
描述: 令牌类型（通常为 bearer）
字段: user_id
类型: Integer
描述: 用户 ID
字段:status
类型: String
描述:请求状态（success/error）
字段: message
类型: String
描述: 错误信息（如果状态为 error）
错误处理	401-认证失败
400-参数错误
访问权限	开放访问
备注	登录成功后，返回的访问令牌需在后续请求中通过 Authorization 头提供。成功返回API密钥




2.接口名称：register_user
该接口用于注册新用户，创建用户账户并生成初始 API 密钥。
表8-2接口register_user表
字段	描述
请求方式	POST
URL	http://30de5fdf.r6.cpolar.cn/register
请求头	Content-Type: application/json
请求参数	JSON 格式，包含以下字段：
字段: username
类型: String
必填: 是
描述: 用户名
字段: password 
类型: String
必填: 是
描述: 密码
字段: email
类型: String
必填: 是
描述: 电子邮箱
响应格式	JSON 格式，包含以下字段：
字段: access_token 
类型: String
描述: 新用户的 API 密钥
字段: user_id
类型: Integer
描述: 用户 ID
字段:status
类型: String
描述:请求状态（success/error） 
字段: message
类型: String
描述: 错误信息（如果状态为 error）
错误处理	400-注册失败
访问权限	开放访问
备注	注册时需确保用户名和邮箱唯一，密码符合安全要求。







3.接口名称：chat_completions
该接口用于与聊天模型进行交互，生成基于用户输入的自然语言响应。用户可以提交消息并指定使用的模型，接口将返回模型生成的回答。此接口广泛应用于聊天机器人、内容生成、问答系统等场景，是实现自然语言处理的核心功能。
表8-3接口chat_completions表
字段	描述
请求方式	POST
URL	http://30de5fdf.r6.cpolar.cn/v1/chat/completions
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
请求参数	JSON 格式，包含以下字段：
字段: model
类型: String
必填: 是
描述: 要使用的模型（如 "Deepseek-Math-7B-Instruct"）
字段: messages
类型: Array
必填: 是
描述: 消息列表，包含用户和助手的对话历史
字段: max_tokens
类型: Integer
必填: 否
描述: 生成的最大 token 数
字段: temperature
类型: Float
必填: 否
描述: 控制输出的随机性（0-2）
字段: stream
类型: Boolean
必填: 否
描述: 是否以流式方式返回响应
响应格式	JSON 格式，包含以下字段：
字段: id
类型: String
描述: 响应 ID
字段: object
类型: String
描述: 对象类型
字段: created
类型: Integer
描述: 创建时间戳
字段: model
类型: String
描述: 模型名字（如 " Qwen/Qwen2.5-Math-7B-Instruct"）
字段: choices
类型: Array
描述: 生成的文本选项列表
字段: usage
类型: Object
描述: 使用的 token 信息
错误处理	400 Bad Request（如果请求参数无效）
401 Unauthorized（如果 API 密钥无效）
500 Internal Server Error（服务器内部错误）
访问权限	该接口需要有效的 API 密钥，未提供密钥的请求将被拒绝。
备注	确保按照 API 文档的要求构造请求体，避免格式错误。请求中应包含有效的模型名称和消息内容。

4.接口名称：related_questions
该接口用于获取与输入问题相关的其他问题列表。这在构建智能问答系统时非常有用，可以帮助用户扩展问题范围或发现相关主题。
表8-4接口related_questions表
字段	描述
请求方式	POST
URL	http://30de5fdf.r6.cpolar.cn/v1/related_questions
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
请求参数	JSON 格式，包含以下字段：
字段: question
类型: String
必填: 是
描述: 输入的问题文本
响应格式	JSON 格式，包含以下字段：
字段: related_questions
类型: Array
描述: 相关问题列表
字段: status
类型: String
描述: 请求状态（success/error）
字段: message
类型: String
描述: 错误信息（如果状态为 error）
错误处理	400 Bad Request（如果请求参数无效）
401 Unauthorized（如果 API 密钥无效）
500 Internal Server Error（服务器内部错误）
访问权限	该接口需要有效的 API 密钥，未提供密钥的请求将被拒绝。
备注	确保传入的问题有足够的上下文，使系统能返回相关的问题。

5.接口名称：create_conversation
该接口用于创建新的对话会话，用户可以在会话中发送和接收消息。
表8-5接口create_conversation表
字段	描述
请求方式	POST
URL	http://30de5fdf.r6.cpolar.cn/conversations
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
请求参数	JSON 格式，包含以下字段：
字段: title
类型: String
必填: 否
描述: 会话标题（可选）
响应格式	JSON 格式，包含以下字段：
字段: conversation_id
类型: Integer
描述: 新创建的会话 ID
错误处理	401-认证失败
500-创建失败
访问权限	该接口需要有效的 API 密钥，未提供密钥的请求将被拒绝。
备注	确保传入的问题具有足够的上下文，以便系统能够返回相关的问题。

6.接口名称：get_all_conversations
该接口用于获取当前用户的所有对话会话列表，包括会话标题、ID 和消息记录。
表8-6接口get_all_conversations表
字段	描述
请求方式	GET
URL	http://30de5fdf.r6.cpolar.cn/conversations
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
请求参数	JSON 格式，包含以下字段：
字段: title
类型: String
描述: 会话标题
响应格式	JSON 格式，包含以下字段：
字段: title
类型: String
描述: 会话标题
字段: conversation_id
类型: Integer
描述: 新创建的会话 ID
字段: messages
类型: Array
描述: 会话中的消息列表
错误处理	401-认证失败
500-查询失败
访问权限	该接口需要有效的 API 密钥，未提供密钥的请求将被拒绝。
备注	返回的会话列表按时间排序，最近的会话在前。

7.接口名称：get_conversation_messages
该接口用于获取指定会话中的所有消息记录。
表8-7接口get_conversation_messages表
字段	描述
请求方式	GET
URL	http://30de5fdf.r6.cpolar.cn/conversations/{conversation_id}/messages
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
路径参数	JSON 格式，包含以下字段：
字段: conversation_id
类型: Integer
描述: 新创建的会话 ID
响应格式	JSON 格式，包含以下字段：
字段: messages
类型: Array
描述: 消息列表，包含每条消息的角色和内容
错误处理	403-无权限
404-会话不存在
访问权限	该接口需要有效的 API 密钥，未提供密钥的请求将被拒绝。
备注	消息按时间顺序排列，最早的在前。











8.接口名称：create_message
该接口用于向指定会话中添加新消息。
表8-8接口create_message表
字段	描述
请求方式	 POST
URL	http://30de5fdf.r6.cpolar.cn/conversations/{conversation_id}/messages
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
路径参数	JSON 格式，包含以下字段：
字段:  role 
类型: String
必填: 是
描述: 消息角色（user 或 assistant）
字段: content
类型: String 
必填: 是
描述: 消息内容
响应格式	JSON 格式，包含以下字段：
字段: message_id
类型: Integer
描述: 新消息的 ID
错误处理	400-角色无效
403-无权限
访问权限	需要有效的 API 密钥，且用户必须是会话的所有者。
备注	消息一旦发送，将存储在会话中。

9.接口名称：update_conversation
该接口用于更新会话的标题。
表8-9接口update_conversation表
字段	描述
请求方式	PATCH
URL	http://30de5fdf.r6.cpolar.cn/conversations/{conversation_id}
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
路径参数	JSON 格式，包含以下字段：
字段: conversation_id
类型: Integer
描述: 新创建的会话 ID
请求参数	JSON 格式，包含以下字段：
字段: title 
类型: String
必填: 是
描述: 新的会话标题
响应格式	JSON 格式，包含以下字段：
字段: status
类型: String
描述: 请求状态（success/error）
字段: message
类型: String
描述: 错误信息（如果状态为 error）
错误处理	403-无权限
404-会话不存在
访问权限	需要有效的 API 密钥，且用户必须是会话的所有者。
备注	更新标题不会影响会话中的消息内容。

10.接口名称：delete_conversation
该接口用于删除指定的会话及其所有相关消息。
表8-10接口delete_conversation表
字段	描述
请求方式	DELETE
URL	http://30de5fdf.r6.cpolar.cn/conversations/{conversation_id}
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
路径参数	JSON 格式，包含以下字段：
字段: conversation_id
类型: Integer
描述: 新创建的会话 ID
响应格式	JSON 格式，包含以下字段：
字段: status
类型: String
描述: 请求状态（success/error）
字段: message
类型: String
描述: 错误信息（如果状态为 error）
错误处理	403-无权限
404-会话不存在
访问权限	需要有效的 API 密钥，且用户必须是会话的所有者
备注	删除操作是不可逆的，会话及其所有消息将被永久删除。


11.接口名称：manage_api_keys
该接口用于管理用户的 API 密钥，包括创建新密钥和撤销现有密钥。
表8-11接口manage_api_keys表
字段	描述
请求方式	DELETE
URL	http://30de5fdf.r6.cpolar.cn/conversations/{conversation_id}
请求头	Authorization: Bearer Token，用于身份验证
Content-Type: application/json
请求参数（POST）	JSON 格式，包含以下字段：
字段: action
类型: String
必填: 是
描述: 操作类型（create 或 revoke）
字段:  key
类型: String
必填: 否（仅在 revoke 时需要）
描述: 要撤销的密钥
响应格式	JSON 格式（GET），包含以下字段：
字段: data
类型: Array
描述: 用户的所有 API 密钥列表，包含密钥、创建时间和最后使用时间
JSON 格式（POST），包含以下字段：
字段: status 
类型: String
描述: 操作状态（success 或 error）
字段: message
类型: String
描述: 操作结果描述
字段: data
类型: Object（仅 create 时返回）
描述: 新创建的密钥信息
错误处理	400-无效操作
401-认证失败
访问权限	需要有效的 API 密钥
备注	创建的密钥需妥善保管，一旦泄露可能导致账户安全问题。






12.接口名称：reference_files
该接口用于检索与特定问题相关的参考文件。用户通过提供一个问题 ID，可以获取与该问题相关的文档、文件或其他资源。这对于用户查阅额外信息或支持材料非常有用。
表8-12接口reference_files表
字段	描述
请求方式	GET
URL	http://30de5fdf.r6.cpolar.cn/v1/reference_files
请求头	Authorization: Bearer Token，用于身份验证
请求参数	查询参数:
字段: question_id
类型: String
必填: 是
描述: 查询相关的问题ID
字段: query
类型: String
必填: 否
描述: 查询文本（可选）
示例请求	GET /reference_files?question_id=123
响应格式	JSON 格式，包含以下字段：
字段: reference_files
类型: Array
描述: 匹配的参考文件列表，包含文件名、路径、类型、相似度等信息
字段: source
类型: String
描述: 文件来源（local_knowledge_base）
错误处理	401-认证失败
500-检索失败
访问权限	需要有效的 API 密钥。
备注	确保提供有效的 question_id，以便系统能够返回相关的参考文件。











13.接口名称：download_file
该接口用于下载指定的参考文件。
表8-13接口download_file表
字段	描述
请求方式	GET
URL	http://30de5fdf.r6.cpolar.cn/api/download
请求头	Authorization: Bearer Token，用于身份验证
查询参数	字段: file_path
类型: String
必填: 是
描述: 文件路径
响应格式	文件流，包含以下头部：
头部：Content-Disposition
描述: 指定文件名和下载方式
错误处理	404-文件不存在
403-无权限
访问权限	需要有效的 API 密钥。
备注	文件内容直接返回给客户端，需确保路径合法且文件存在。

14.接口名称：save_question
该接口用于保存用户的问题，并返回唯一的问题 ID。问题可以与会话关联。
表8-14接口save_question表
字段	描述
请求方式	 POST
URL	http://30de5fdf.r6.cpolar.cn/v1/questions
请求头	Authorization: Bearer Token，用于身份验证
请求参数	JSON 格式，包含以下字段：
字段:  content 
类型: String
必填： 是
描述: 问题内容
字段: conversation_id
类型: Integer
比填： 否
描述: 会话 ID
响应格式	JSON 格式，包含以下字段：
字段: status 
类型: String
描述: 请求状态（success）
字段: question_id
类型: String
描述:  问题的唯一 ID
错误处理	400-内容过短
500-保存失败
访问权限	需要有效的 API 密钥。
备注	保存的问题将用于后续的搜索和推荐。

15.接口名称：get_user_document
该接口用于获取用户上传的文档内容。
表8-15接口get_user_document表
字段	描述
请求方式	GET
URL	http://30de5fdf.r6.cpolar.cn/user-knowledge/get/{filename}
请求头	Authorization: Bearer Token，用于身份验证
路径参数	字段: filename
类型:  String
描述: 文件名
响应格式	字段: status 
类型: String
描述: 请求状态（success）
字段: content 
类型: String
描述: 文件内容
错误处理	404-文件不存在
403-无权限
访问权限	需要有效的 API 密钥。
备注	仅支持文本文件类型（如 txt、json 等）。















16.接口名称：list_user_documents
该接口用于列出用户上传的所有文档。
表8-16接口list_user_documents表
字段	描述
请求方式	GET
URL	http://30de5fdf.r6.cpolar.cn/user-knowledge/list
请求头	Authorization: Bearer Token，用于身份验证
查询参数	字段: page
类型:  Integer
描述: 页码（默认 1）
字段: page_size
类型: Integer
描述: 每页大小（默认 10，最大 100）
响应格式	字段: status 
类型: String
描述: 请求状态（success）
字段: data
类型: Object
描述: 包含文档列表、总数量、页码和每页大小
错误处理	404-文件不存在
403-无权限
访问权限	需要有效的 API 密钥。
备注	文档按上传时间排序，最近的在前。

17.接口名称：update_user_document
该接口用于更新用户上传的文档内容。
表8-17接口update_user_document表
字段	描述
请求方式	PATCH
URL	http://30de5fdf.r6.cpolar.cn/user-knowledge/get/{filename}
请求头	Authorization: Bearer Token，用于身份验证
路径参数	字段: filename
类型: String
必填:  是
描述: 文件名
字段: content 
类型: String
描述: 文件内容
响应格式	字段: status 
类型: String
描述: 请求状态（success）
字段: message
类型: String
描述: 操作结果描述
错误处理	400-文件类型不可编辑
500-更新失败
访问权限	需要有效的 API 密钥。
备注	仅支持直接编辑的文件类型（如 txt、json 等）。

18.接口名称：delete_user_document
该接口用于删除用户上传的文档内容。
表8-18接口delete_user_document表
字段	描述
请求方式	DELETE
URL	http://30de5fdf.r6.cpolar.cn/user-knowledgedelete/{doc_id}
请求头	Authorization: Bearer Token，用于身份验证
路径参数	字段:  doc_id
类型: Integer
必填:  是
描述: 文档 ID
响应格式	字段: status 
类型: String
描述: 请求状态（success）
字段: message
类型: String
描述: 操作结果描述
错误处理	404-文档不存在
403-无权限
访问权限	需要有效的 API 密钥。
备注	 删除操作是不可逆的，文档将被永久移除。











19.接口名称：download_user_document
该接口用于下载用户上传的文档。
表8-19接口download_user_document表
字段	描述
请求方式	GET
URL	user-knowledge/download/{filename}
请求头	Authorization: Bearer Token，用于身份验证
路径参数	字段: filename
类型: String
必填:  是
描述: 文件名
字段: content 
类型: String
描述: 文件内容
响应格式	文件流，包含以下头部：
头部: Content-Type
描述: 文件类型
头部: Content-Disposition
描述: 指定文件名和下载方式
错误处理	404-文档不存在
403-无权限
访问权限	需要有效的 API 密钥。
备注	 文件内容直接返回给客户端，需确保文件存在。
