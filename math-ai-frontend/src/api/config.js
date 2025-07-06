export const API = {
    GENERATE: '/v1/chat/completions',
    RELATED_QUESTIONS: '/v1/related_questions',
    REFERENCE_FILES: '/v1/reference_files',
    AUTH: '/auth',     
    REGISTER: '/register' ,
    API_KEYS: '/api-keys',
    CONVERSATIONS: '/conversations',
    // 添加新接口
    SAVE_QUESTION: '/v1/questions',
    DOWNLOAD: '/api/download',
    OCR: '/v1/ocr',
    }
    
//

// 修改前
export const BASE_URL = 'http://localhost:8000'

// 修改后（示例）
// export const BASE_URL = 'http://4b90738c.r6.cpolar.cn'  // 替换为你的穿透地址