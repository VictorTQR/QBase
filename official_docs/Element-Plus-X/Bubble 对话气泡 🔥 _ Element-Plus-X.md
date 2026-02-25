---
title: "Bubble 对话气泡 🔥 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/bubble/"
author:
published: 2025-07-20
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## Bubble 对话气泡 🔥

📌 Warning

`1.1.6 版本` 继承打字器雾化属性。请及时更新尝试

🐵 此温馨提示更新时间： `2025-04-13`

## 介绍

`Bubble` 是一个对话气泡组件，常用于聊天的时候。它可以展示对话内容，支持自定义头像、头部、内容、底部，并且具备打字效果和加载状态展示。该组件内置 `Typewriter` 打字器组件，能够实现文本的打字动画效果。

## 代码演示

### 基本使用

hello world!

[基础用法。](https://element-plus-x.com/zh/components/bubble/#zh-components-bubble-demos-content)

最简化的集成方式。

### 头像、位置

### 头部、底部

### 加载状态

### 打字器配置

🥰 感谢使用

[打字效果](https://element-plus-x.com/zh/components/bubble/#zh-components-bubble-demos-typing)

通过设置 `typing` 属性，开启打字效果。 更新 `content` 如果是之前的子集，则会继续输出，否则会重新输出。

💌 Info

🙊 当使用 `#content` 插槽，去自定义内容时。 `typing` 属性将失效。如果你想让你的内容字符串，重新实现打字效果，可以与 `Typewriter 打字器` 组件 结合使用。

💡 Tip

`typing` 属性接受一个对象，包含以下属性：

- `step`: 每次打字的吐字字符数，默认为 2
- `interval`: 打字间隔（毫秒），默认为 50
- `suffix`: 结尾字符，默认为 `|`

### 开启Markdown渲染

## 🔥Element-Plus-X

🥰 感谢使

[渲染 markdown 文本内容](https://element-plus-x.com/zh/components/bubble/#zh-components-bubble-demos-is-markdown)

通过设置 `is-markdown` 属性，开启 `markdown` 文本内容渲染模式。 更新 `content` 如果是之前的子集，则会继续输出，否则会重新输出。

### 继承打字器的图表和md样式

#### 标题

这是一个 Markdown 示例。

[渲染 markdown 文本内容](https://element-plus-x.com/zh/components/bubble/#zh-components-bubble-demos-cssAndMermaid)

通过设置 `is-markdown` 属性，开启 `markdown` 文本内容渲染模式。 更新 `content` 如果是之前的子集，则会继续输出，否则会重新输出。

### 雾化效果

## 🔥Element-Plus-X

🥰

[雾化效果](https://element-plus-x.com/zh/components/bubble/#zh-components-bubble-demos-is-fog)

开启打字器时，继承打字器雾化属性。通过设置 `is-fog` 属性，开启雾化打字器渲染模式。 兼容 Markdown 样式。注意，开启雾化后， `typing` 的后缀 `suffix` 属性将会失效。

`is-fog` 默认为 false，可以设置为 `true` 或者 `{ bgColor: '#f5f5f5', width: '80px' }` 。设置雾化背景颜色，可以更好的匹配自定义的样式。

### 自定义内容

😊 欢迎使用 element-plus-x，我是自定义气泡

🥤 长时间工作后如何有效休息？

💌 保持积极心态的秘诀是什么？

🔥 如何在巨大的压力下保持冷静？

[自定义 气泡内容](https://element-plus-x.com/zh/components/bubble/#zh-components-bubble-demos-content-customize)

通过 `#content` 插槽，自定义气泡内容。

💌 Info

`#content` 插槽 优先级更高， `content` 属性将失效。 `no-padding` 属性可以禁用气泡内容内边距。

### 变体和形状

filled

filled + round

filled + corner

borderless

borderless + round

borderless + corner

outlined

outlined + round

outlined + corner

shadow

shadow + round

shadow + corner

round

corner

placement end

[内置样式格式和形状](https://element-plus-x.com/zh/components/bubble/#zh-components-bubble-demos-variant-and-shape)

通过 `variant` 属性设置气泡的填内置样式格式。通过 `shape` 属性设置气泡的形状。当然你也可以两两结合，搭配使用

💌 Info

默认情况下， `variant` 为 `filled` ， `shape` 为 `round` 。

`shape` 为 `corner` 时， `placement="end"` 会自动将气泡翻转，使得右上角的 `弧度针` 指向用户。

### 控制打字

24%

## 🔥 Bubble 实例方法-事件

😄 使你的打字器可高度定制化。

[🐵 支持控制 Bubble 组件 播放、中断/继续、 销毁。支持监听组件状态。](https://element-plus-x.com/zh/components/bubble/#zh-components-bubble-demos-customized)

💩 更好的控制中断输出、继续打字和销毁等操作

💡 Tip

😸 内置 `Typewriter` 组件。将 `Typewriter` 组件内的所有属性方法挂载到 `Bubble` 组件上，方便在敏捷开发中使用。

💌 Info

🐒 如果你觉得内置的 `Typewriter` 组件，不能满足你的需求，还可以 使用 `#content` 插槽对 `Bubble` 组件进行定制化开发。 使用 `#content`, 内置的 `Typewriter` 组件将会失效。在插槽中，你也可以自行和 `Typewriter` 组合使用，也可以自定义 `流式请求` 、 `流式渲染` 等个性化操作。

## 属性

| 属性名 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `content` | String | '' | 气泡内要展示的文本内容 |
| `placement` | String | 'start' | 气泡的位置，可选值为 `'start'` 或 `'end'` ，分别表示左侧和右侧。 |
| `avatar` | String | '' | 气泡头像的图片地址 |
| `loading` | Boolean | false | 是否显示加载状态。为 `true` 时，气泡内会显示加载状态。 |
| `shape` | String | null | 气泡的形状，可选值为 `'round'` （圆角）或 `'corner'` （有角）。 |
| `variant` | String | 'filled' | 气泡的样式变体，可选值为 `'filled'` （填充）、 `'borderless'` （无边框）、 `'outlined'` （轮廓）、 `'shadow'` （阴影）。 |
| `noStyle` | Boolean | false | 是否去除样式，为 `true` 时，将去除气泡内置 `padding` 和 `背景色` |
| `isMarkdown` | Boolean | false | 是否将 `content` 内容作为 Markdown 格式处理。 |
| `typing` | Boolean \| Object | false | 是否开启打字效果。若为对象，可设置 `step` （每次渲染的字符数）和 `suffix` （打字光标后缀内容）。 `interval` 表示打字间隔时间，单位为 `ms` 。 |
| `maxWidth` | String | '500px' | 气泡内容的最大宽度。 |
| `avatar-size` | String | '' | 设置头像占位大小 |
| `avatar-gap` | String | '12px' | 设置头像和气泡之间的 `gap` 值 |
| `avatar-shape` | String | '' | 头像形状，可选值为 `'circle'` （圆形）或 `'square'` （方形）。 |
| `avatar-icon` | String | '' | 头像图标，优先级高于 `avatar` ，支持传入图标名称，如 `'user'` 。 |
| `avatar-src-set` | String | '' | 设置头像图片 srcset 属性 |
| `avatar-alt` | String | '' | 设置头像图片 alt 属性 |
| `avatar-fit` | String | 'cover' | 设置头像图片的 `object-fit` 属性,可选属性值： `'cover'` 、 `'contain'` 、 `'fill'` 、 `'none'` 、 `'scale-down'` |

## 事件

| 事件名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `@start` | `ref` 实例 | Function | 打字效果开始时触发 |
| `@finish` | `ref` 实例 | Function | 打字效果完成时触发 |
| `@writing` | `ref` 实例 | Function | 打字中实时触发 |
| `@avatarError` | `ref` 实例 | Function | 头像加载失败时触发 |

## Ref 实例方法

| 属性名 | 类型 | 描述 |
| --- | --- | --- |
| `interrupt` | Function | 中断打字。 |
| `continue` | Function | 继续未完成的打字。 |
| `restart` | Function | 重新开始打字。 |
| `destroy` | Function | 主动销毁 Bubble 组件。 |
| `renderedContent` | String | 获取打字组件渲染的内容。 |
| `isTyping` | Boolean | 是否正在打字。 |
| `progress` | Number | 打字进度，取值范围 0 - 100。 |

## 插槽

| 插槽名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `#avatar` | \- | Slot | 自定义头像展示内容 |
| `#header` | \- | Slot | 自定义气泡顶部展示内容 |
| `#content` | \- | Slot | 自定义气泡展示内容 |
| `#loading` | \- | Slot | 自定义气泡加载状态展示内容 |
| `#footer` | \- | Slot | 自定义气泡底部展示内容 |

## 功能特性

1. **布局方向** - 支持左对齐(`start`)和右对齐(`end`)
2. **内容类型** - 支持纯文本、Markdown、自定义插槽内容
3. **加载状态** - 内置加载动画，支持自定义加载内容
4. **视觉效果** - 提供多种形状和变体（圆角/直角、填充/描边/阴影等）
5. **打字动画** - 支持渐进式文字输出效果
6. **灵活插槽** - 提供头像、头部、内容、底部、加载状态等插槽