---
title: "最佳实践 | Hook-Fetch"
source: "https://jsonlee12138.github.io/hook-fetch/docs/best-practices/"
author:
  - "[[JsonLee12138]]"
published: 2025-11-07
created: 2026-02-01
description: "本文档总结了使用 Hook-Fetch 的最佳实践，帮助您构建高效、可维护的应用程序。"
tags:
  - "clippings"
---
本文档总结了使用 Hook-Fetch 的最佳实践，帮助您构建高效、可维护的应用程序。

## 项目结构

### 推荐的项目结构

```markdown
src/
├── api/
│   ├── index.ts          # API 实例配置
│   ├── endpoints.ts      # 端点定义
│   ├── types.ts          # 类型定义
│   └── plugins/          # 自定义插件
│       ├── auth.ts
│       ├── logger.ts
│       └── retry.ts
├── hooks/
│   ├── useApi.ts         # 通用 API Hook
│   ├── useAuth.ts        # 认证相关 Hook
│   └── useStream.ts      # 流式数据 Hook
└── utils/
    ├── constants.ts      # 常量定义
    └── helpers.ts        # 辅助函数
```

### API 实例配置

### 端点定义

### 类型定义

```typescript
// src/api/types.ts
export interface User {
  id: string;
  name: string;
  email: string;
  createdAt: string;
  updatedAt: string;
}

export interface ApiResponse<T = any> {
  data: T;
  message: string;
  success: boolean;
  code: number;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface StreamMessage {
  id: string;
  content: string;
  timestamp: number;
  type: 'user' | 'assistant' | 'system';
}
```

## 错误处理

### 全局错误处理

### 组件级错误处理

```typescript
// src/hooks/useApi.ts
import { useHookFetch } from 'hook-fetch/react';
import { api } from '../api';

export function useApi() {
  const { request, loading, cancel } = useHookFetch({
    request: api.request,
    onError: (error) => {
      // 组件级错误处理
      if (error.response?.status === 422) {
        // 表单验证错误
        return error.response.json().then((data) => {
          showValidationErrors(data.errors);
        });
      }
    }
  });

  return {
    request,
    loading,
    cancel,
    // 封装常用方法
    get: (url: string, params?: any) =>
      request(url, { method: 'GET', params }).json(),
    post: (url: string, data?: any) =>
      request(url, { method: 'POST', data }).json(),
    put: (url: string, data?: any) =>
      request(url, { method: 'PUT', data }).json(),
    delete: (url: string) =>
      request(url, { method: 'DELETE' }).json()
  };
}
```

## 性能优化

### 请求缓存

```typescript
// src/api/plugins/cache.ts
export function cachePlugin(options = {}) {
  const defaultOptions = {
    ttl: 5 * 60 * 1000, // 5分钟
    maxSize: 100,
    excludeMethods: ['POST', 'PUT', 'PATCH', 'DELETE']
  };

  const config = { ...defaultOptions, ...options };
  const cache = new Map();

  const getRequestKey = (url: string, method: string, params: any, data: any) => {
    return \`${url}::${method}::${JSON.stringify(params)}::${JSON.stringify(data)}\`;
  };

  return {
    name: 'cache',
    async beforeRequest(requestConfig) {
      if (config.excludeMethods.includes(requestConfig.method)) {
        return requestConfig;
      }

      const key = getRequestKey(
        requestConfig.url,
        requestConfig.method,
        requestConfig.params,
        requestConfig.data
      );
      const cached = cache.get(key);

      if (cached) {
        // 检查缓存是否过期
        if (cached.timestamp + config.ttl > Date.now()) {
          // 返回缓存数据，使用 resolve 属性
          return {
            ...requestConfig,
            resolve: () => new Response(JSON.stringify(cached.data), {
              status: 200,
              headers: { 'Content-Type': 'application/json' }
            })
          };
        }
        else {
          // 缓存已过期，删除缓存
          cache.delete(key);
        }
      }

      return requestConfig;
    },
    async afterResponse(context, requestConfig) {
      if (config.excludeMethods.includes(requestConfig.method)) {
        return context;
      }

      const key = getRequestKey(
        requestConfig.url,
        requestConfig.method,
        requestConfig.params,
        requestConfig.data
      );

      // 限制缓存大小
      if (cache.size >= config.maxSize) {
        const firstKey = cache.keys().next().value;
        cache.delete(firstKey);
      }

      // 缓存响应
      cache.set(key, {
        data: context.result,
        timestamp: Date.now()
      });

      return context;
    }
  };
}
```

### 请求去重

```typescript
// 使用官方去重插件
import { dedupePlugin, isDedupeError } from 'hook-fetch/plugins/dedupe';

const api = hookFetch.create({
  baseURL: 'https://api.example.com',
  plugins: [dedupePlugin()]
});

// 并发相同请求会被去重
try {
  const promises = [
    api.get('/users/1').json(),
    api.get('/users/1').json(), // 会被去重
  ];

  const results = await Promise.allSettled(promises);
  results.forEach((result, index) => {
    if (result.status === 'rejected' && isDedupeError(result.reason)) {
      console.log(\`请求 ${index + 1} 被去重\`);
    }
    else if (result.status === 'fulfilled') {
      console.log(\`请求 ${index + 1} 成功:\`, result.value);
    }
  });
}
catch (error) {
  if (isDedupeError(error)) {
    console.log('检测到重复请求');
  }
}

// 禁用特定请求的去重
const response = await api.get('/users/1', {}, {
  extra: { dedupeAble: false }
}).json();
```

**更好的替代方案：**

```typescript
// 推荐：使用防抖避免重复提交
import { debounce } from 'lodash-es';

const handleSubmit = debounce(async (data) => {
  await api.post('/users', data).json();
}, 300);

// 推荐：使用按钮禁用状态
function UserForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (data) => {
    if (isSubmitting) return;

    setIsSubmitting(true);
    try {
      await api.post('/users', data).json();
    }
    finally {
      setIsSubmitting(false);
    }
  };

  return (
    <button disabled={isSubmitting} onClick={handleSubmit}>
      {isSubmitting ? '提交中...' : '提交'}
    </button>
  );
}
```

### 批量请求

```typescript
// src/utils/batch.ts
export class BatchRequestManager {
  private batchQueue: Array<{
    url: string;
    params: any;
    resolve: (data: any) => void;
    reject: (error: any) => void;
  }> = [];

  private batchTimeout: NodeJS.Timeout | null = null;

  constructor(
    private api: any,
    private batchSize = 10,
    private delay = 100
  ) {}

  async request(url: string, params: any): Promise<any> {
    return new Promise((resolve, reject) => {
      this.batchQueue.push({ url, params, resolve, reject });

      if (this.batchQueue.length >= this.batchSize) {
        this.processBatch();
      }
      else if (!this.batchTimeout) {
        this.batchTimeout = setTimeout(() => {
          this.processBatch();
        }, this.delay);
      }
    });
  }

  private async processBatch() {
    if (this.batchTimeout) {
      clearTimeout(this.batchTimeout);
      this.batchTimeout = null;
    }

    const currentBatch = this.batchQueue.splice(0, this.batchSize);

    try {
      const batchRequest = {
        requests: currentBatch.map(({ url, params }) => ({ url, params }))
      };

      const response = await this.api.post('/batch', batchRequest);

      response.results.forEach((result: any, index: number) => {
        const { resolve, reject } = currentBatch[index];
        if (result.success) {
          resolve(result.data);
        }
        else {
          reject(new Error(result.error));
        }
      });
    }
    catch (error) {
      currentBatch.forEach(({ reject }) => reject(error));
    }
  }
}
```

## 流式数据处理

### 流式数据管理

```typescript
import { useHookFetch } from 'hook-fetch/react';
// src/hooks/useStream.ts
import { useCallback, useRef } from 'react';

export function useStream<T = any>(requestFn: (...args: any[]) => any) {
  const dataRef = useRef<T[]>([]);
  const listenersRef = useRef<Set<(data: T[]) => void>>(new Set());

  const { stream, loading, cancel } = useHookFetch({
    request: requestFn,
    onError: (error) => {
      console.error('Stream error:', error);
    }
  });

  const subscribe = useCallback((listener: (data: T[]) => void) => {
    listenersRef.current.add(listener);

    return () => {
      listenersRef.current.delete(listener);
    };
  }, []);

  const startStream = useCallback(async (...args: any[]) => {
    dataRef.current = [];

    try {
      for await (const chunk of stream(...args)) {
        if (chunk.result) {
          dataRef.current.push(chunk.result);

          // 通知所有监听者
          listenersRef.current.forEach((listener) => {
            listener([...dataRef.current]);
          });
        }
      }
    }
    catch (error) {
      console.error('Stream processing error:', error);
    }
  }, [stream]);

  const clear = useCallback(() => {
    dataRef.current = [];
    listenersRef.current.forEach((listener) => {
      listener([]);
    });
  }, []);

  return {
    startStream,
    subscribe,
    clear,
    cancel,
    loading,
    data: dataRef.current
  };
}
```

### 流式数据缓冲

```typescript
// src/utils/streamBuffer.ts
export class StreamBuffer<T> {
  private buffer: T[] = [];
  private flushTimeout: NodeJS.Timeout | null = null;

  constructor(
    private onFlush: (items: T[]) => void,
    private bufferSize = 10,
    private flushInterval = 1000
  ) {}

  add(item: T) {
    this.buffer.push(item);

    if (this.buffer.length >= this.bufferSize) {
      this.flush();
    }
    else if (!this.flushTimeout) {
      this.flushTimeout = setTimeout(() => {
        this.flush();
      }, this.flushInterval);
    }
  }

  flush() {
    if (this.flushTimeout) {
      clearTimeout(this.flushTimeout);
      this.flushTimeout = null;
    }

    if (this.buffer.length > 0) {
      this.onFlush([...this.buffer]);
      this.buffer = [];
    }
  }

  clear() {
    this.buffer = [];
    if (this.flushTimeout) {
      clearTimeout(this.flushTimeout);
      this.flushTimeout = null;
    }
  }
}
```

## 测试

### 单元测试

```typescript
// src/api/__tests__/api.test.ts
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../index';

// 模拟 fetch
global.fetch = vi.fn();

describe('API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should make GET request', async () => {
    const mockResponse = { data: { id: 1, name: 'John' } };

    (fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });

    const result = await api.get('/users/1').json();

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/users/1'),
      expect.objectContaining({
        method: 'GET'
      })
    );

    expect(result).toEqual(mockResponse);
  });

  it('should handle errors', async () => {
    (fetch as any).mockRejectedValueOnce(new Error('Network error'));

    await expect(api.get('/users/1').json()).rejects.toThrow('Network error');
  });
});
```

### 集成测试

```typescript
// src/hooks/__tests__/useApi.test.ts
import { act, renderHook } from '@testing-library/react';
import { useApi } from '../useApi';

describe('useApi', () => {
  it('should handle loading state', async () => {
    const { result } = renderHook(() => useApi());

    expect(result.current.loading).toBe(false);

    act(() => {
      result.current.get('/users');
    });

    expect(result.current.loading).toBe(true);
  });
});
```

## 安全性

### 认证和授权

### 请求签名

## 监控和调试

### 性能监控

```typescript
// src/api/plugins/performance.ts
export function performancePlugin() {
  return {
    name: 'performance',
    async beforeRequest(config) {
      config.extra = {
        ...config.extra,
        startTime: performance.now()
      };
      return config;
    },
    async afterResponse(context, config) {
      const endTime = performance.now();
      const duration = endTime - (config.extra?.startTime || 0);

      // 记录性能指标
      console.log(\`[Performance] ${config.method} ${config.url}: ${duration.toFixed(2)}ms\`);

      // 发送到监控系统
      if (duration > 5000) { // 超过5秒的请求
        sendToMonitoring({
          type: 'slow_request',
          url: config.url,
          method: config.method,
          duration
        });
      }

      return context;
    }
  };
}
```

### 调试工具

```typescript
// src/utils/debug.ts
export function createDebugger(namespace: string) {
  const isDebugEnabled = process.env.NODE_ENV === 'development'
    || localStorage.getItem('debug') === 'true';

  return {
    log: (...args: any[]) => {
      if (isDebugEnabled) {
        console.log(\`[${namespace}]\`, ...args);
      }
    },
    warn: (...args: any[]) => {
      if (isDebugEnabled) {
        console.warn(\`[${namespace}]\`, ...args);
      }
    },
    error: (...args: any[]) => {
      if (isDebugEnabled) {
        console.error(\`[${namespace}]\`, ...args);
      }
    }
  };
}
```

## 部署和生产环境

### 环境配置

```typescript
// src/config/index.ts
export const config = {
  apiUrl: process.env.REACT_APP_API_URL || 'https://api.example.com',
  streamUrl: process.env.REACT_APP_STREAM_URL || 'https://stream.example.com',
  timeout: Number.parseInt(process.env.REACT_APP_TIMEOUT || '10000'),
  retryAttempts: Number.parseInt(process.env.REACT_APP_RETRY_ATTEMPTS || '3'),
  debug: process.env.NODE_ENV === 'development'
};
```

### 生产环境优化

```typescript
// src/api/production.ts
import { config } from '../config';

export const productionApi = hookFetch.create({
  baseURL: config.apiUrl,
  timeout: config.timeout,
  plugins: [
    // 生产环境插件
    authPlugin(),
    retryPlugin({ maxRetries: config.retryAttempts }),
    cachePlugin({ ttl: 10 * 60 * 1000 }), // 10分钟缓存
    // 注意：去重插件不推荐在生产环境使用，建议在应用层面处理
    // dedupePlugin(), // 不推荐
    errorHandlerPlugin(),
    ...(config.debug ? [loggerPlugin()] : []) // 只在调试模式下启用日志
  ]
});
```

通过遵循这些最佳实践，您可以构建出高性能、可维护且安全的应用程序。