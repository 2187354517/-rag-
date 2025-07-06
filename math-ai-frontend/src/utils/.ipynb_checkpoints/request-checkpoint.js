import { BASE_URL } from '@/api/config';

export const apiRequest = async (url, method = 'GET', data) => {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
    };

    // 排除登录、注册及相关接口的认证头
    if (token && !url.startsWith('/auth') && !url.startsWith('/register')) {
        headers.Authorization = `Bearer ${token}`;
    }

    // 确保 method 不为 undefined，若为 undefined 则使用默认值 'GET'
    const validMethod = method? method.toUpperCase() : 'GET';

    const config = {
        method: validMethod,
        headers,
    };

    // 仅允许需要 Body 的方法添加数据
    if (['POST', 'PUT', 'PATCH'].includes(config.method)) {
        config.body = JSON.stringify(data);
    }

    const response = await fetch(`${BASE_URL}${url}`, config);

    if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch {
            errorData = { detail: response.statusText };
        }
        throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
    }

    // 处理无内容响应
    return response.status === 204? null : response.json();
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