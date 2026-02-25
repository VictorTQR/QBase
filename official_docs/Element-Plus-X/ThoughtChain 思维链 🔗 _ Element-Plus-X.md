---
title: "ThoughtChain 思维链 🔗 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/thoughtChain/"
author:
published: 2025-07-23
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## ThoughtChain 思维链 🔗

## 介绍

`ThoughtChain` 是一个用于展示AI思考过程的时间轴组件，支持 **状态管理** 、 **内容展开/收起** 和 **动态样式配置** 。通过可视化的思考步骤序列，帮助用户直观理解复杂逻辑流程。组件内置多种状态反馈、过渡动画和扩展插槽，适用于智能对话、数据分析、流程引导等场景。

## 代码示例

### 基础用法

- 思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字
- 思考内容标题
- 思考内容标题
- 思考内容标题
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字

[thinkingItems 基础使用](https://element-plus-x.com/zh/components/thoughtChain/#zh-components-thoughtChain-demos-base)

通过 `thinkingItems` 传入一个数组控制渲染。

💌 Info

`id` 为必传字段。你还可以通过 `rowKey` 设置唯一标识的名称，默认为 `id` 。

### 尺寸大小控制

- 思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字
- 思考内容标题
- 思考内容标题
- 隐藏主标题，思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字

- 思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字
- 思考内容标题
- 思考内容标题
- 隐藏主标题，思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字

[dotSize 属性](https://element-plus-x.com/zh/components/thoughtChain/#zh-components-thoughtChain-demos-dot-size)

默认值是 `default` ，可选值有 `small` 、 `default` 、 `large` 。

### 最大宽度控制

- 思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字

[maxWidth 属性](https://element-plus-x.com/zh/components/thoughtChain/#zh-components-thoughtChain-demos-max-width)

设置 思维链的最大宽度，默认 '500px'。字符串类型，意味着你可以传入百分比，如 '50%'。或其他单位，甚至 css 计算宽度，如 'calc(100% - 200px)'。

### 自定义标题和内容

- 思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字
- 思考内容标题
- 思考内容标题
- 思考内容标题
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字

[titleKey、thinkTitleKey、thinkContentKey 属性](https://element-plus-x.com/zh/components/thoughtChain/#zh-components-thoughtChain-demos-key-label)

通过 `titleKey` 、 `thinkTitleKey` 、 `thinkContentKey` 属性，可以自定义节点的：标题、思考内容标题、思考内容 的 key 名称。

### 扩展插槽

- 思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字
- 思考内容标题
- 思考内容标题
- 思考内容标题
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字

通过 `#icon` 插槽，可以自定义 不同状态的 图标。 通过 `#icon={item}` 可以获取到当前状态。

### 手动控制展开状态

- 思考内容标题-默认展开
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字
- 思考内容标题
- 思考内容标题
- 思考内容标题
	进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字进行搜索文字

[handleExpand 事件](https://element-plus-x.com/zh/components/thoughtChain/#zh-components-thoughtChain-demos-handle-expand)

通过 handleExpand 事件，可以获取到当前展开的节点数据。

## 属性

- **组件属性**

| 参数名 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `thinkingItems` | `Array<ThoughtChainItemBase>` | \[\] | 思考项数组 |
| `dotSize` | 'small'/'default'/'large' | 'default' | 时间轴点大小 |
| `maxWidth` | string | '600px' | 最大宽度 |
| `lineGradient` | boolean | false | 是否启用线条颜色渐变 |
| `rowKey` | string | 'id' | 数据项唯一标识字段 |
| `titleKey` | string | 'title' | 标题字段名 |
| `thinkTitleKey` | string | 'thinkTitle' | 思考标题字段名 |
| `thinkContentKey` | string | 'thinkContent' | 思考内容字段名 |

- **ThoughtChainItemBase** 数组子项的类型定义

| 参数名 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `id` | `string \| number` | **必填** | 节点唯一标识 |
| `title` | `string` | `undefined` | 主标题 |
| `thinkTitle` | `string` | `undefined` | 折叠面板标题（思考标题） |
| `thinkContent` | `string` | `undefined` | 展开时显示的详细内容 |
| `status` | `'loading' \| 'error' \| 'success'` | `undefined` | 节点状态标识（影响图标和颜色） |
| `isCanExpand` | `boolean` | `undefined` | 是否允许展开节点内容 |
| `isDefaultExpand` | `boolean` | `undefined` | 是否默认展开节点内容 |
| `isMarkdown` | `boolean` | `undefined` | 是否启用Markdown格式渲染 |
| `typing` | `TypingConfig` | `undefined` | 打字机效果配置（同打字器组件） |

## 事件

| 事件名 | 参数类型 | 说明 |
| --- | --- | --- |
| `handleExpand` | `item: ThoughtChainItemProps<T>` | 展开状态变化时触发 |

## 插槽

| 插槽名 | 作用域参数 | 说明 |
| --- | --- | --- |
| `#icon` | { item } | 自定义时间轴点图标 |

## 核心特性

1. **多状态可视化**
	- 支持 `loading` / `success` / `error`
	- 自动切换加载动画、图标和颜色反馈
2. **动态内容管理**
	- 支持内容折叠展开（可配置默认展开项）
	- 内置打字机效果（Typewriter组件）
	- 支持Markdown格式渲染
3. **灵活样式配置**
	- 自定义时间轴宽度、点大小
	- 动态颜色渐变线条
	- CSS变量主题覆盖
4. **响应式交互**
	- 平滑的过渡动画
	- 支持动态增删思考项
	- 展开状态双向绑定