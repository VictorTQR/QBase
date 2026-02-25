---
title: "Welcome 欢迎 🌹 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/welcome/"
author:
published: 2025-07-20
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## Welcome 欢迎 🌹

## 介绍

`Welcome` 这个组件可以清晰传达给用户可实现的意图范围和预期功能。使用合适的欢迎推荐组件，可以有效降低用户学习成本，让用户快速了解并顺利开始。

## 代码演示

### 基本使用

欢迎来到 Element Plus X 🦋

欢迎使用 Element Plus X 💖

这是描述信息 ~

FAILED

欢迎使用 Element Plus X 💖

这是描述信息 ~

FAILED

欢迎使用 Element Plus X 💖

副标题

这是描述信息 ~

[基础用法](https://element-plus-x.com/zh/components/welcome/#zh-components-welcome-demos-base)

快速创建一个 欢迎卡片

### 样式变体

欢迎来到 Element Plus X 🦋

欢迎使用 Element Plus X 💖

这是描述信息 ~

FAILED

欢迎使用 Element Plus X 💖

这是描述信息 ~

FAILED

欢迎使用 Element Plus X 💖

副标题

这是描述信息 ~

[variant 属性](https://element-plus-x.com/zh/components/welcome/#zh-components-welcome-demos-variant)

快速切换多种样式，目前只有两种， `filled` 和 `borderless` 。默认为 `filled` 。

### 背景颜色

切换布局： 

欢迎来到 Element Plus X 🦋

欢迎使用 Element Plus X 💖

这是描述信息 ~

FAILED

欢迎使用 Element Plus X 💖

这是描述信息 ~

FAILED

欢迎使用 Element Plus X 💖

副标题

这是描述信息 ~

欢迎来到 Element Plus X 🦋

欢迎使用 Element Plus X 💖

这是描述信息 ~

FAILED

欢迎使用 Element Plus X 💖

这是描述信息 ~

FAILED

欢迎使用 Element Plus X 💖

副标题

这是描述信息 ~

[direction 属性](https://element-plus-x.com/zh/components/welcome/#zh-components-welcome-demos-bg)

设置 布局方法 `ltr` 从左到右 和 `rtl` 从右到左，更多属性，控制样式，详情可查看 属性 列表。

### 自定义图片

![](https://element-plus-x.com/logo.png)

欢迎使用 Element Plus X 💖

用 vue3 对 ant-design-x 的复刻。后续将会集成 AI 工作流编排组件 和 md 多功能渲染组件，给 Vue 开发社区 一个好用的 AI 组件库

[image 插槽](https://element-plus-x.com/zh/components/welcome/#zh-components-welcome-demos-image)

方便更换自定义的 图片

### 自定义副标题

![](https://element-plus-x.com/logo.png)

欢迎使用 Element Plus X 💖

用 vue3 对 ant-design-x 的复刻。后续将会集成 AI 工作流编排组件 和 md 多功能渲染组件，给 Vue 开发社区 一个好用的 AI 组件库

[extra 插槽](https://element-plus-x.com/zh/components/welcome/#zh-components-welcome-demos-extra)

方便自己定义 副标题内容

## 属性

| 属性名 | 类型 | 是否必填 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `variant` | string | 否 | filled | 组件样式变体（filled/borderless） |
| `direction` | string | 否 | ltr | 文本方向（ltr/rtl） |
| `icon` | string | 否 | \- | 图标URL地址 |
| `title` | string | 否 | \- | 主标题文本内容 |
| `extra` | string | 否 | \- | 副标题文本内容 |
| `description` | string | 否 | \- | 描述文本内容 |
| `className` | string | 否 | \- | 容器外层自定义类名 |
| `rootClassName` | string | 否 | \- | 根节点自定义类名 |
| `classNames` | object | 否 | \- | 各部分自定义类名（{ icon, title, extra, description }） |
| `style` | object | 否 | \- | 容器外层自定义样式 |
| `styles` | object | 否 | \- | 各部分自定义样式（{ icon, title, extra, description }） |
| `prefixCls` | string | 否 | welcome | 组件类名前缀 |

## 插槽

| 插槽名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `#image` | \- | Slot | 自定义欢迎图片内容 |
| `#extra` | \- | Slot | 自定义副标题内容 |

## 功能特性

1. 通过 `variant` 属性目前暂时支持 `filled` （填充）和 `borderless` （无边框）两种视觉风格
2. 支持 `direction` 属性控制文本方向
3. 可通过 `classNames` 和 `styles` 细粒度控制样式
4. 支持 `image` 、 `extra` 插槽扩展自定义内容