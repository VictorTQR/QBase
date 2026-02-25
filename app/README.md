# QBase App

QBase 桌面应用 - 本地知识库管理系统

## 开发命令

```bash
npm install          # 安装依赖
npm run dev          # 启动 Vite 开发服务器
npm run ele          # 启动 Electron
npm run start        # 同时启动 Vite 和 Electron
npm run build        # 构建生产版本
npm run test:unit    # 运行测试
npm run lint         # 运行 lint
npm run format       # 格式化代码
```

## 当前版本: v0.1

### 已实现功能

- ✅ Element Plus + Element-Plus-X 配置
- ✅ Workspace Store（工作区管理）
- ✅ Document Store（文档加载）
- ✅ Electron API（文件选择、读取、遍历）
- ✅ 主布局（三栏布局）
- ✅ 左侧文件夹树导航
- ✅ 中间 Markdown 预览（XMarkdown）
- ✅ 右侧 AI 助手占位面板
- ✅ 路由配置

### 目录结构

```
src/
├── components/
│   ├── Layout/
│   │   ├── MainLayout.vue      # 主布局
│   │   ├── Sidebar.vue         # 左侧文件夹树
│   │   ├── ContentPane.vue     # 中间内容区
│   │   └── AgentPanel.vue      # 右侧 AI 面板
│   └── MarkdownViewer.vue      # Markdown 渲染
├── stores/
│   ├── workspace.js            # 工作区状态
│   └── document.js             # 文档状态
├── views/
│   └── Home.vue                # 首页
├── router/
│   └── index.js                # 路由配置
└── main.js                     # 应用入口
```

## 技术栈

- Vue 3 (Composition API)
- Pinia
- Vue Router
- Element Plus
- Element-Plus-X
- Electron
- Vite
- Vitest

## 原模板说明

This template should help get you started developing with Vue 3 in Vite.

### Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

### Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

### Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).
