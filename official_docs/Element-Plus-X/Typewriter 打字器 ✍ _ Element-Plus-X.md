---
title: "Typewriter 打字器 ✍ | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/typewriter/"
author:
published: 2025-07-20
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## Typewriter 打字器 ✍

📌 Warning

**`XMarkdown 组件`** 已经推出，可以和 `Typewriter 组件` 组合使用，请升级到 `beta 1.2.2` 版本。

💌 Info

`v1.2.0 版本` 提供解决 **样式覆盖** 、 **渲染图表** 以及 **自定义代码高亮样式、自定义插件** 简单方案

一、我们在组件库新增了 `prismjs` 官方的 css 样式文件，可以在项目直接引入，解决 **md 代码块高亮** 问题。

二、我们在组件库新增了 `Mermaid.js` 。用于解决 `mermaid 格式` 简单的 **图表** 渲染问题。

三、我们把 `markdown-it` 内置的 **代码高亮方法** 和 **插件** 暴露出来。方便开发者更好的集成第三方生态的 **样式** 和 **插件**

🐵 此温馨提示更新时间： `2025-07-06`

## 介绍

`Typewriter` 是一个可高度定制化开发的 `打字器组件` ，灵感来自 `ant-design-x` 官方 `气泡组件` 案例，将打字方法剥离出来。支持 Markdown 渲染 和 动态打字效果。

## 代码演示

### 基本使用

content 属性设置打字器内容

[基本](https://element-plus-x.com/zh/components/typewriter/#zh-components-typewriter-demos-content)

基础用法。

### Markdown 渲染

#### 标题

这是一个 Markdown 示例。

- 列表项 1
- 列表项 2 **粗体文本** 和 *斜体文本*
```javascript
console.log('Hello, world!');
```

[支持 Markdown 内容渲染](https://element-plus-x.com/zh/components/typewriter/#zh-components-typewriter-demos-isMarkdown)

通过 `isMarkdown` 属性控制是否启用 Markdown 渲染模式。

### MD-代码块高亮（v1.2.0 新增）

提供一个内置的样式

#### 标题

这是一个 Markdown 示例。

- 列表项 1
- 列表项 2 **粗体文本** 和 *斜体文本*
```js
console.log('Hello, world!');
```

[内置 prism 样式文件](https://element-plus-x.com/zh/components/typewriter/#zh-components-typewriter-demos-newMarkDown)

### MD-插件模式（v1.2.0 新增）

如果你觉得内置的样式不好看或者内置的插件不能满足你的需求，可以通过插件模式自定定义 **样式** 和 **插件** 。

#### 标题

这是一个 Markdown 示例。

- 列表项 1
- 列表项 2 **粗体文本** 和 *斜体文本*
```javascript
console.log('Hello, world!');
```
```javascript
79%17%3%Pets adopted by volunteersDogsCatsRats
```
```javascript
Sales Revenuejanfebmaraprmayjunjulaugsepoctnovdec110001050010000950090008500800075007000650060005500500045004000Revenue (in $)
```

[内置 markdown-it-mermaid 插件 渲染简单的图表](https://element-plus-x.com/zh/components/typewriter/#zh-components-typewriter-demos-mermaid)

你也可以自定在 `markdown-it` 社区中寻找自定义插件，以实现更多自定义功能。 通过 `md-plugins` 属性，传入 `markdown-it` 插件数组，即可在 `markdown-it` 中使用自定义插件。 通过 `highlight` 函数，传入 Prism 的高亮函数，或者其他高亮库，作用在 `markdown-it` 中使用 Prism 的高亮功能。

详细 Mermaid 格式 参见： [Mermaid.js](https://mermaid.js.org/syntax/pie.html)

### 开启打字效果

typing 属性开启打字效果

typing 属性也

### 🐒 is-markdown

[支持 开启/关闭 打字模式](https://element-plus-x.com/zh/components/typewriter/#zh-components-typewriter-demos-typing)

通过 `typing` 属性控制是否启用 打字渲染模式。 `typing` 也可以是一个对象，设置 step 属性，控制打字每次吐字，interval 属性控制打字间隔，suffix 属性控制打字添加的后缀。

📌 Warning

`suffix` 属性只能设置字符串，且在 `isMarkdown` 为 `true` 时失效，因为后缀会受 `markdown` 渲染影响，始终会另起一行进行展示，这一点在 `ant-design-x` 中也会出现。所以我们先暂时决定在 `isMarkdown` 为 `true` 时，不展示后缀，让打字器尽可能美观。

### 打字器雾化效果

#### 标题

这是一个 Markdown 示例。

- 列表项 1
- 列表项

[支持雾化效果](https://element-plus-x.com/zh/components/typewriter/#zh-components-typewriter-demos-isFog)

通过 `isFog` 属性控制是否启用雾化效果。注意，该属性在 `isTyping` 为 `true` 时才生效。切回覆盖默认的 `typing` 后缀属性。

### 动态更新内容

🥰 感谢使用 Element-Plus-X! 你的支持，是我们开源的最强动力 ~

[🐵 支持 动态更新 content 内容。](https://element-plus-x.com/zh/components/typewriter/#zh-components-typewriter-demos-updates)

🐒 当使用 `typing` 属性时，更新 `content` 如果是之前的子集，则会继续输出，否则会重新输出。

### 控制打字

34%

## 🔥 Typewriter 实例方法-事件

😄 使你的打字器可高度定制化。

- 更方便的控制打字

[🐵 支持控制组件 播放、中断/继续、 销毁。支持监听组件状态。](https://element-plus-x.com/zh/components/typewriter/#zh-components-typewriter-demos-customized)

💩 更好的控制中断输出、继续打字和销毁等操作 你可以通过组件的 `ref` 实例获取以下方法和属性：

- `interrupt` 中断打字过程 `typerRef.interrupt()`
- `continue` 继续未完成的打字 `typerRef.continue()`
- `restart` 重新开始打字 `typerRef.restart()`
- `destroy` 销毁组件（清理资源） `typerRef.destroy()`
- `renderedContent` 获取当前渲染的内容。 `typerRef.renderedContent.value`
- `isTyping` 获取当前是否正在打字。 `typerRef.isTyping.value`
- `progress` 获取当前进度百分比。 `typerRef.progress.value`

💡 Tip

你还可以设置组件的监听事件，获取组件的状态。

- `@start` 打字开始时触发
- `@finish` 打字结束时触发
- `@writing` 打字时触发

三个方法，默认参数返回组件实例。

## 属性

| 属性名 | 类型 | 是否必填 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `content` | String | 否 | `''` | 要展示的文本内容，支持纯文本或 Markdown 格式。 |
| `isMarkdown` | Boolean | 否 | `false` | 是否启用 Markdown 渲染模式。 |
| `typing` | Boolean \| `{ step?: number, interval?: number, suffix?: string }` | 否 | `false` | 是否启用打字机效果。 |
| `typing.step` | Number | 否 | `2` | 每次打字吐多少字符。 |
| `typing.interval` | Number | 否 | `50` | 每次打字的间隔时间 单位( `ms` )。 |
| `typing.suffix` | String | 否 | `'\|'` | 打字器后缀光标字符（仅在非 Markdown 模式下生效）。 |
| `isFog` | Boolean \| `{ bgColor?: string, width?: string }` | 否 | `false` | 是否启用雾化效果，可以设置背景色和宽度。 |

## 事件

| 事件名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `@start` | `ref` 实例 | Function | 当打字效果开始时触发 |
| `@finish` | `ref` 实例 | Function | 当打字效果完成时触发 |
| `@writing` | `ref` 实例 | Function | 当打字效果进行中不断触发 |

## Ref 实例方法

| 属性名 | 类型 | 描述 |
| --- | --- | --- |
| `interrupt` | Function | 中断打字。 |
| `continue` | Function | 继续未完成的打字。 |
| `restart` | Function | 重新开始打字。 |
| `destroy` | Function | 主动销毁打字组件。 |
| `renderedContent` | String | 获取打字组件渲染的内容。 |
| `isTyping` | Boolean | 是否正在打字。 |
| `progress` | Number | 打字进度，取值范围 0 - 100。 |

## 功能特性

1. **Markdown 支持** ：支持渲染 Markdown 格式的文本，并应用 GitHub 风格的样式。
2. **动态打字效果** ：可以模拟打字机的效果，逐步显示文本内容。
3. **代码高亮** ：内置 Prism.js，支持代码块的语法高亮。
4. **XSS 安全** ：使用 DOMPurify 对 HTML 内容进行过滤，防止 XSS 攻击。
5. **灵活配置** ：支持自定义打字速度、光标字符、后缀等参数。
6. **定制化开发** ：支持更据组件打字的状态做定制化开发。