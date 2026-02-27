# XMarkdown 代码块渲染 CSP 错误修复

**日期**: 2026-02-27
**问题类型**: Bug 修复
**状态**: ✅ 已解决

## 问题描述

在实现 YAML frontmatter 功能后，测试 XMarkdown 渲染包含代码块的 Markdown 文件时出现错误。

### 错误现象

```
Uncaught (in promise) CompileError: WebAssembly.instantiate(): 
Compiling or instantiating WebAssembly module violates the following 
Content Security Policy directive because 'unsafe-eval' is not an 
allowed source of script
```

### 触发场景

1. 打开包含代码块（```js ... ```）的 Markdown 文件
2. XMarkdown 使用 Shiki 进行代码高亮
3. Shiki 尝试编译 WebAssembly 模块
4. CSP 策略阻止，报错

## 问题根因

### Content Security Policy (CSP) 配置问题

在 `app/index.html` 第 8 行：

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; ...">
```

缺少 `'wasm-unsafe-eval'` 策略，导致：
- Shiki 代码高亮依赖 WebAssembly 模块
- `WebAssembly.instantiate()` 被 CSP 阻止
- 代码块无法正常渲染

### 时间线

此问题与 YAML frontmatter 功能**无关**，只是恰好在同一时间测试时发现：

1. 之前可能只测试了无代码块的 Markdown 文件
2. 实现 frontmatter 后进行完整测试时才触发此问题

## 修复方案

### 只添加 'wasm-unsafe-eval'（不添加 'unsafe-eval'）

测试发现：
- ❌ 添加 `'unsafe-eval'`：可以工作，但安全风险较高
- ✅ **只添加 `'wasm-unsafe-eval'`：可以工作，安全风险较低**

### 修复后的 CSP 配置

```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval';
  style-src 'self' 'unsafe-inline';
  media-src 'self' local-file:;
  connect-src 'self' http://soct.top:3000 local-file:;
">
```

## 安全风险分析

### 策略对比

| 策略 | 风险等级 | 说明 |
|------|---------|------|
| `'unsafe-inline'` | 🟡 中 | 已存在，Vue 开发模式需要 |
| `'wasm-unsafe-eval'` | 🟡 中 | 新增，仅用于 WebAssembly 编译 |
| `'unsafe-eval'` | 🟠 中高 | 未添加，避免 `eval()` 风险 |

### Electron 环境的安全保障

项目已有安全配置降低风险：
- ✅ `contextIsolation: true` - 上下文隔离
- ✅ `nodeIntegration: false` - Node.js 集成禁用
- ✅ `sandbox`（默认）- 沙箱环境

### 风险等级（总体）

🟡 **中等** - 本地知识库应用，用户数据来源可控，风险可接受。

## 修改文件列表

| 文件 | 修改内容 |
|------|---------|
| `app/index.html` | 在 `script-src` 中添加 `'wasm-unsafe-eval'` |

## 关键代码变更

### index.html:8

**修改前：**
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; media-src 'self' local-file:; connect-src 'self' http://soct.top:3000 local-file:">
```

**修改后：**
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; media-src 'self' local-file:; connect-src 'self' http://soct.top:3000 local-file:">
```

## 测试建议

1. 打开包含 JavaScript 代码块的 Markdown 文件
2. 验证代码高亮正常显示
3. 检查浏览器控制台（F12）确认无 CSP 错误
4. 测试多种语言代码块（js, python, java 等）

## 后续优化建议

1. **长期：研究替代方案** - 评估是否可以用不需要 WebAssembly 的代码高亮库（如 Prism.js、Highlight.js）
2. **CSP 报告模式** - 启用 `report-uri` 收集违规报告
3. **环境差异化** - 开发环境用宽松策略，生产环境用严格策略
4. **Shiki 升级** - 关注 Shiki 未来版本是否提供无 WASM 选项

## 参考资料

- [MDN - Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Shiki 文档 - WebAssembly 要求](https://shiki.style/)
- [Electron 安全最佳实践](https://www.electronjs.org/docs/tutorial/security)
