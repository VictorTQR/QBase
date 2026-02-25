---
title: "Prompts 提示集组件 🎁 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/prompts/"
author:
published: 2025-07-20
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## Prompts 提示集组件 🎁

## 介绍

`Prompts` 用于显示一组与当前上下文相关的预定义的问题或建议。

## 代码演示

### 基本使用

🐵 提示集组件标题

###### 🐛 提示集组件标题

描述信息描述信息描述信息

###### 🐛 提示集组件标题

###### 🐛 提示集组件标题

###### 🐛 提示集组件标题

[基础用法](https://element-plus-x.com/zh/components/prompts/#zh-components-prompts-demos-base)

快速创建一组提示集列表。默认超出不会换行，且隐藏滚动条。

### 禁用状态

🐵 提示集组件标题

###### 🐛 提示集组件标题

描述信息描述信息描述信息

###### 🐛 我是被禁用的

###### 🐛 单个禁用控制更准确

###### 🐛 提示集组件标题

[禁用状态](https://element-plus-x.com/zh/components/prompts/#zh-components-prompts-demos-disabled)

通过 `disabled` 属性快速禁用提示集组件，点击事件将会失效。注意是控制单个提示集上，才生效。

### 垂直排列

🐵 提示集组件标题

###### 🐛 提示集组件标题

描述信息描述信息描述信息

###### 🐛 我是被禁用的

###### 🐛 单个禁用控制更准确

###### 🐛 提示集组件标题

[纵向展示](https://element-plus-x.com/zh/components/prompts/#zh-components-prompts-demos-vertical)

使用 `vertical` 属性，控制 `Prompts` 展示方向。注意这个是作用在整个 `Prompts` 组件上，而不是单个 `PromptsItem` 上。

### 可换行

🐵 提示集组件标题

###### 🐛 提示集组件标题

描述信息描述信息描述信息

###### 🐛 我是被禁用的

###### 🐛 单个禁用控制更准确

###### 🐛 提示集组件标题

[换行展示](https://element-plus-x.com/zh/components/prompts/#zh-components-prompts-demos-wrap)

使用 `wrap` 属性，控制 `Prompts` 超出区域长度时是否可以换行。

### 响应式宽度

🐵 提示集组件标题

###### 🐛 提示集组件标题

描述信息描述信息描述信息

###### 🐛 我是被禁用的

###### 🐛 单个禁用控制更准确

###### 🐛 提示集组件标题

[响应式宽度](https://element-plus-x.com/zh/components/prompts/#zh-components-prompts-demos-responsive)

配合 `wrap` 与 `styles` 固定宽度展示。 注意是作用在 `PromptsItem` 上结合使用才会生效。单独作用方便更定制化。

### 定制化样式

🐵 提示集组件标题

###### 🐛 提示集组件标题

描述信息描述信息描述信息

###### 🐛 我是被禁用的

###### 🐛 单个禁用控制更准确

###### 🐛 提示集组件标题

[定制化提示集的样式](https://element-plus-x.com/zh/components/prompts/#zh-components-prompts-demos-customized)

通过 `style` 属性来定制化提示集的样式。

通过 `itemStyle` 和 `itemHoverStyle` 还有 `itemActiveStyle` 属性来定制化单个提示集的样式。

### 嵌套组合

🐛 提示集组件标题

###### 🐠 主标题 0

描述 0

###### 🐛 子标题 0-1

描述 0

###### 🐛 孙子标题 0-1-1

描述 0

###### 🐛 孙子标题 0-1-1

描述 0

###### 🐛 孙子标题 0-1-1

描述 0

###### 🐛 子标题 0-2

描述 0

###### 🐛 子标题 0-3

描述 0

###### 🐠 主标题 1

描述 1

###### 🐛 子标题 1-1

描述 1

###### 🐛 孙子标题 1-1-1

描述 1

###### 🐛 孙子标题 1-1-1

描述 1

###### 🐛 孙子标题 1-1-1

描述 1

###### 🐛 子标题 1-2

描述 1

###### 🐛 子标题 1-3

描述 1

###### 🐠 主标题 2

描述 2

###### 🐛 子标题 2-1

描述 2

###### 🐛 孙子标题 2-1-1

描述 2

###### 🐛 孙子标题 2-1-1

描述 2

###### 🐛 孙子标题 2-1-1

描述 2

###### 🐛 子标题 2-2

描述 2

###### 🐛 子标题 2-3

描述 2

[基础用法](https://element-plus-x.com/zh/components/prompts/#zh-components-prompts-demos-nested)

快速创建一组提示集列表。默认超出不会换行，且隐藏滚动条。

## 属性

| 属性名 | 类型 | 是否必填 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `title` | `string` | 否 | `''` | 提示集的主标题文本内容 |
| `items` | `PromptsItemsProps[]` | 否 | `[]` | 提示项数组，每个元素包含标签、图标、描述等信息（具体结构见下方说明） |
| `wrap` | `boolean` | 否 | `false` | 是否允许提示项自动换行（仅水平排列时生效） |
| `vertical` | `boolean` | 否 | `false` | 是否垂直排列提示项（垂直模式下布局方向为列排列） |
| `style` | `CSSProperties` | 否 | `{}` | 组件容器的自定义样式（直接作用于最外层 `div.el-prompts` ） |

**`PromptsItemsProps` 结构说明** （单个提示项属性）：

## 事件

| 事件名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `@itemClick` | `(item: PromptsItemsProps)` | Function | 当某个提示集被点击时触发的事件。 |

## 插槽

| 插槽名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `#title` | \- | `Slot` | 自定义提示集标题内容（若同时设置 `title` 属性，插槽内容会覆盖属性文本） |
| `#icon` | `{ item: PromptsItemsProps }` | `Slot` | 自定义提示项的图标内容（接收当前提示项 `item` 参数，可覆盖 `item.icon` ） |
| `#label` | `{ item: PromptsItemsProps }` | `Slot` | 自定义提示项的标签内容（接收当前提示项 `item` 参数，可覆盖 `item.label` ） |
| `#description` | `{ item: PromptsItemsProps }` | `Slot` | 自定义提示项的描述内容（接收当前提示项 `item` 参数，可覆盖 `item.description` ） |

## 功能特性

1. **多维度内容展示** ：支持通过 `items` 属性配置标签、图标、描述等基础信息，同时提供 `label` / `icon` / `description` 插槽实现内容高度自定义。
2. **灵活布局控制** ：通过 `vertical` 属性切换垂直/水平排列模式， `wrap` 属性控制水平排列时的自动换行能力，适配不同场景布局需求。
3. **交互状态反馈** ：内置悬停（背景色变浅）和激活（背景色加深）状态样式，支持通过 `itemHoverStyle` / `itemActiveStyle` 自定义状态样式，提升交互体验。
4. **禁用状态支持** ：单个提示项可通过 `item.disabled` 属性禁用，禁用状态下不响应点击事件且背景色变灰，明确提示不可操作。
5. **嵌套层级展示** ：支持通过 `item.children` 配置子提示项，组件自动递归渲染嵌套结构，满足多级分类或关联提示的展示需求。6.**细粒度样式定制** ：支持通过 `style` 属性控制组件整体样式，通过 `itemStyle` 控制单个提示项基础样式，支持状态样式单独配置（ `itemHoverStyle` / `itemActiveStyle` ）。