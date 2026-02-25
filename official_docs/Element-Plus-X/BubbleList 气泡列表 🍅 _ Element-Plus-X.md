---
title: "BubbleList 气泡列表 🍅 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/bubbleList/"
author:
published: 2025-07-22
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## BubbleList 气泡列表 🍅

📌 Warning

`1.1.6 版本` 继承打字器 **雾化** 效果。新增 **滚动底部按钮，仿 `豆包` 🔥** 。新增 **鼠标悬停展示滚动条** ，增强交互体验。请及时更新尝试

🐵 此温馨提示更新时间： `2025-04-13`

💡 Tip

另: 新版本的自动滚动，在 `list` 长度变化时，自动滚动。但是 向上滚动滚动条后，需要手动调用 `scrollToBottom` 方法，以再次实现自动滚动。或者 滚动条滚动到底部后，会重新触发自动滚动。

和原来逻辑一样, 升级无需任何心理负担。

## 介绍

`BubbleList` 依赖于 `Bubble` 组件，用于展示一组对话气泡列表。该组件支持设置 `列表最大高度` ，具备 `自动滚动` 功能。同时，它还提供了多种 `控制滚动` 的方法， `使用者` 可以轻松调用，性能强大，无需任何开发心理负担。

## 代码演示

### 基本使用

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你

[基础使用](https://element-plus-x.com/zh/components/bubbleList/#zh-components-bubbleList-demos-list)

预设样式的气泡列表，通过一个消息简单的 `Array` ，可以快速创建一个聊天记录。

📌 Warning

可以通过 **`item`** 属性来透传给组件内置的 **`Bubble`** 组件。设置每一个气泡的属性。更灵活的使用方式。具体属性可以访问 [Bubble](https://element-plus-x.com/components/bubble) 组件的文档。

我们所有的消息操作，只需要维护这个数组就行了。

包括 **`流式消息`** 的设置。这里没有使用接口流式操作。在我们的模版项目中，走了实战。可以当做一个参考。

👉 [模版项目预览地址](https://chat.element-plus-x.com/chat)

👉 [模版项目源码地址](https://github.com/element-plus-x/ruoyi-element-ai) 欢迎star🥰

你还可以通过属性 `max-height` 来控制列表的最大高度。

### 自定义列表

动态设置内容  自定义 loading 

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

🧁 用户

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

🧁 用户

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

### 自动滚动、指定滚动位置

### 返回顶部按钮

滚动条显示：

 鼠标悬停展示

底部按钮加载状态：

 true

底部按钮颜色： 底部按钮位 距离底部： 距离左边： 底部按钮尺寸：

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

哈哈哈，让我试试

💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~💖 感谢使用 Element Plus X! 你的支持，是我们开源的最强动力 ~

哈哈哈，让我试试

[回到底部按钮 + 滚动条体验](https://element-plus-x.com/zh/components/bubbleList/#zh-components-bubbleList-demos-back-button)

- 内置回到底部按钮，仿 `豆包` 。
- 鼠标悬停时，会出现滚动条
- 和内置自动滚动不冲突，请放心使用

💌 Info

滚动条控制属性

- `alwaysShowScrollbar` 属性控制是否一直显示滚动条，默认为 `false` 。

底部按钮定制化属性

- 你可以通过 `backButtonThreshold` 属性来设置回到底部按钮的阈值，默认为 `80` ，即当滚动条滚动到距离底部 `80px` 时，才会出现回到底部按钮。
- `showBackButton` 属性控制是否显示回到底部按钮，默认为 `true` 。
- `btnLoading` 属性控制是否显示加载中的状态，默认为 `true` 。
- `btnColor` 属性控制回到底部按钮的颜色，默认为 `#409EFF` 。
- `backButtonPosition` 属性控制回到底部按钮的位置，默认为 `{ bottom: '20px', left: 'calc(50% - 19px)' }` 可以用 `%` 来控制，如 `{ bottom: '10%', left: 'calc(50% - 19px)' }` 。
- `btnIconSize` 属性控制回到底部按钮的图标大小，默认为 `24` 。

### 滚动完成事件

📌 Warning

极特殊情况才用的到，在流式输出中不适用，会快速触发打字结束事件。

trigger-indices:

[complete 事件 和 trigger-indices 属性](https://element-plus-x.com/zh/components/bubbleList/#zh-components-bubbleList-demos-on-complete)

🍉该属性使用场景很少，请酌情使用，更细致的控制你的气泡在列表中的 `完成事件` 。

你可以通过 `@complete` 事件，触发列表，每一个打字中的 `Bubble` 气泡组件的 `完成打字` 的回调事件。 `@complete` 返回两个参数， `instance` 是 打字器组件实例 和 `index` 是 `BubbleListItem` 的索引。

💡 Tip

- `@complete` 事件仅会触发 `typing` 属性为 `true` 的 `Bubble 组件` 回调事件。
- 如果你给列表配置了多个气泡的 `typing` 属性，列表默认只处理最后一个 `typing` 为 `true` 的气泡的 `@complete` 事件。

💌 Info

- 如果你需要处理多个 `typing` 为 `true` 的气泡完成回调事件，你可以通过 `triggerIndices` 属性来指定需要处理的气泡的索引。它是一个 `'only-last' | 'all' | number[]` 类型。
- 默认为 `'only-last'` ，只执行 最后一个 `typing` 为 `true` 的气泡的 `@complete` 事件。
- `'all'` 表示执行所有 `typing` 为 `true` 的气泡的 `@complete` 事件。 `@complete` 将会被执行多次。
- `number[]` 设置你想要监听的 `BubbleListItem` 的索引。组件会自动过滤 `无效的索引` ，并输出 `console.warn`

## 属性

| 属性名 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `list` | Array | 是 | 无 | 包含气泡信息的数组，每个元素为一个对象，包含 `content` 、 `placement` 、 `loading` 、 `shape` 、 `variant` 、 `isMarkdown` 、 `typing` 等 `Bubble` 属性，用于配置每个气泡的显示内容和样式。 |
| `maxHeight` | String | 否 | '500px' | 气泡列表容器的最大高度，超过该高度会出现垂直滚动条。 |
| `alwaysShowScrollbar` | Boolean | 否 | false | 是否一直显示滚动条，默认为 `false` 。 |
| `backButtonThreshold` | Number | 否 | 80 | 滚动条显示阈值，当滚动条距离底部小于该值时，会显示滚动条。 |
| `showBackButton` | Boolean | 否 | true | 是否显示返回顶部按钮，默认为 `true` 。 |
| `backButtonPosition` | `{ bottom: '20px', left: 'calc(50% - 19px)' }` | 否 | `{ bottom: '20px', left: 'calc(50% - 19px)' }` | 返回顶部按钮的位置, 默认底部居中展示。 |
| `btnLoading` | Boolean | 否 | true | 是否开启返回顶部按钮 loading 状态，默认为 `true` 。 |
| `btnColor` | String | 否 | '#409EFF' | 返回顶部按钮的颜色，默认为 `'#409EFF'` 。 |
| `btnIconSize` | Number | 否 | 24 | 返回顶部按钮的图标大小，默认为 24px。 |
| `triggerIndices` | 'only-last' \| 'all' \| number\[\] | 否 | 'only-last' | 触发 `complete` 事件的气泡 `索引数组` ，默认为 `'only-last'` 。 |

## 事件

| 事件名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `@complete` | (instance, index) | Function | 当某个气泡的打字效果完成时触发的事件。 |

## Ref 实例方法

| 属性名 | 类型 | 描述 |
| --- | --- | --- |
| `scrollToTop` | Function | 滚动到顶部。 |
| `scrollToBottom` | Function | 滚动到底部。 |
| `scrollToBubble` | Function | 滚动到指定气泡索引位置。 |

## 插槽

| 插槽名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `#avatar` | \- | Slot | 自定义头像展示内容 |
| `#header` | \- | Slot | 自定义气泡顶部展示内容 |
| `#content` | \- | Slot | 自定义气泡展示内容 |
| `#loading` | \- | Slot | 自定义气泡加载状态展示内容 |
| `#footer` | \- | Slot | 自定义气泡底部内容 |

## 功能特性

1. **智能滚动** - 自动跟踪最新消息位置
2. **深度定制** - 完整的气泡组件插槽透传
3. **多种滚动方式** - 滚动到顶部、底部、指定位置
4. **打字效果** - 支持打字效果
5. **多种样式** - 支持多种样式，如圆形、方形等