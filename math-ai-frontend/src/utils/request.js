import { BASE_URL } from '@/api/config';

// export const apiRequest = async (url, method = 'GET', data) => {
//     const token = localStorage.getItem('token');
//     const headers = {
//         'Content-Type': 'application/json',
//     };

//     // 处理对象形式的参数
//     let requestUrl = url;
//     let requestMethod = method;
//     let requestData = data;

//     // 如果 url 是对象，则解构参数
//     if (typeof url === 'object' && url !== null) {
//         requestUrl = url.url;
//         requestMethod = url.method || 'GET';
//         requestData = url.data || null;
//     }

//     // 排除登录、注册及相关接口的认证头
//     //if (token && !url.startsWith('/auth') && !url.startsWith('/register')) {
//     if (token && typeof requestUrl === 'string' && !requestUrl.startsWith('/auth') && !requestUrl.startsWith('/register')) {
//         headers.Authorization = `Bearer ${token}`;
//     }

//     // 确保 method 不为 undefined，若为 undefined 则使用默认值 'GET'
//     //const validMethod = method? method.toUpperCase() : 'GET';
//     const validMethod = requestMethod? requestMethod.toUpperCase() : 'GET';

//     const config = {
//         method: validMethod,
//         headers,
//     };

//     // 处理GET/DELETE方法的参数
//     if (['GET', 'DELETE'].includes(config.method) && data) {
//       const params = new URLSearchParams(data).toString();
//       requestUrl += (requestUrl.includes('?') ? '&' : '?') + params;
//     }
    
//     // 仅允许需要 Body 的方法添加数据
//     if (['POST', 'PUT', 'PATCH'].includes(config.method)) {
//         //config.body = JSON.stringify(data);
//         config.body = JSON.stringify(requestData);
//     }

//     //const response = await fetch(`${BASE_URL}${url}`, config);
//     const response = await fetch(`${BASE_URL}${requestUrl}`, config);

//     if (!response.ok) {
//         let errorData;
//         try {
//             errorData = await response.json();
//         } catch {
//             errorData = { detail: response.statusText };
//         }
//         throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
//     }

//     // 处理无内容响应
//     return response.status === 204? null : response.json();
// };

export const apiRequest = async (url, method = 'GET', data, options = {}) => {
  const token = localStorage.getItem('token');
  // 合并传入的headers和默认headers
  const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}) // 合并传入的headers
  };

  // 处理对象形式的url参数（如果存在）
  let requestUrl = url;
  let requestMethod = method;
  let requestData = data;
  if (typeof url === 'object' && url !== null) {
      requestUrl = url.url;
      requestMethod = url.method || 'GET';
      requestData = url.data || null;
  }

  // 处理认证头
  if (token && typeof requestUrl === 'string' 
      && !requestUrl.startsWith('/auth') 
      && !requestUrl.startsWith('/register')) {
      headers.Authorization = `Bearer ${token}`;
  }

  const validMethod = requestMethod ? requestMethod.toUpperCase() : 'GET';
  const config = {
      method: validMethod,
      headers: headers,
      ...options // 合并其他配置项如signal等
  };

  // 处理GET/DELETE参数
  if (['GET', 'DELETE'].includes(validMethod) && requestData) {
      const params = new URLSearchParams(requestData).toString();
      requestUrl += (requestUrl.includes('?') ? '&' : '?') + params;
  }

  // 处理POST/PUT/PATCH的Body
  if (['POST', 'PUT', 'PATCH'].includes(validMethod)) {
      if (requestData instanceof FormData) {
          // FormData时，让浏览器自动设置Content-Type
          delete headers['Content-Type']; // 删除手动设置的Content-Type
          config.body = requestData; // 直接使用FormData对象
      } else {
          // 其他数据使用JSON
          config.body = JSON.stringify(requestData);
      }
  }

  // 发送请求
  const response = await fetch(`${BASE_URL}${requestUrl}`, config);

  if (!response.ok) {
      // 错误处理保持不变
  }

  return response.status === 204 ? null : response.json();
};


// 修改streamingRequest工具函数（添加onComplete参数）
export const streamingRequest = async (
  url, 
  method, 
  data, 
  onDataReceived,
  onComplete,
  signal = null
) => {
  const token = localStorage.getItem('token');
  let fullContent = '';

  try {
    const response = await fetch(`${BASE_URL}${url}`, {
      method: method.toUpperCase(),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({ ...data, stream: true }),
      signal
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    // eslint-disable-next-line no-constant-condition
    while (true) {
      if (signal?.aborted) {
        throw new DOMException('Aborted', 'AbortError');
      }

      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        if (!part.startsWith('data: ')) continue;
        
        const payload = part.substring(6).trim();
        if (payload === '[DONE]') continue;

        try {
          const parsed = JSON.parse(payload);
          const content = parsed.choices?.[0]?.delta?.content || '';
          
          if (content) {
            fullContent += content;
            onDataReceived(content, false);
          }
        } catch (e) {
          console.error('JSON解析失败:', e);
        }
      }
    }
    
    onDataReceived('', true);
    if (typeof onComplete === 'function') {
      await onComplete(fullContent);
    }

  } catch (err) {
    if (err.name === 'AbortError') {
      onDataReceived('', true);
      if (typeof onComplete === 'function') {
        await onComplete(fullContent);
      }
      return;
    }
    
    console.error('流式请求失败:', err);
    onDataReceived(`[错误] ${err.message}`, true);
    throw err;
  }
};


// 新增文件上传专用方法
export const fileUploadRequest = async (
  url,
  file,
  headers, // 新增headers参数
  onDataReceived,
  onComplete,
  signal = null
) => {
  const token = localStorage.getItem('token');

  const formData = new FormData();
  formData.append('file', file);

  try {
      const response = await fetch(`${BASE_URL}${url}`, {
          method: 'POST',
          headers: headers || { // 使用传入的headers
              'Authorization': token ? `Bearer ${token}` : '',
          },
          body: formData,
          signal
      });

      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      onDataReceived && onDataReceived(data.message, true);
      onComplete && onComplete(data);

  } catch (err) {
      onDataReceived && onDataReceived(`[错误] ${err.message}`, true);
      throw err;
  }
};