---
title: "Sender 输入框 💭 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/sender/"
author:
published: 2025-07-23
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## Sender 输入框 💭

## 介绍

`Sender` 是用于聊天的输入框组件。具备丰富的交互功能和自定义特性。它支持语音输入、清空输入内容、多种提交方式，并且允许用户自定义头部、前缀和操作列表等内容。同时，组件提供了焦点控制、提交回调等功能，可满足多样化的输入场景需求。

## 代码演示

### 基础用法

[基本使用](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-basic)

这是一个 `Sender` 输入框，最简单的使用例子。

### 提示语

[提示语](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-placeholder)

可以通过 `placeholder` 设置输入框的提示语。

### 双向绑定（未绑定，值不会变）

[受控组件](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-v-model)

可以通过 `v-model` 绑定组件的 `value` 属性。

📌 Warning

- 在提交时，需要有内容，才会进行提交。
- 内容为空时，提交按钮会被禁用，且使用组件实例提交会失效。

💌 Info

- 通过 `v-model` 属性，可以自动绑定输入框的值。不用赋值数据到 `v-model` 中。
- 通过 `@submit` 事件，可以触发输入框的提交事件，回传一个 `value` 参数，你可以在此处理提交的数据。
- 通过 `@cancel` 事件，可以触发 `loading` 按钮的点击事件。在这里你可以中止提交的操作。

你也可以通过组件 ref 实例对象进行调用

- `senderRef.value.submit()` 触发提交
- `senderRef.value.cancel()` 触发取消
- `senderRef.value.clear()` 重置输入框的值

### 提交按钮禁用状态

### 自定义最大行数和最小行数

[超长文字输入框](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-autosize)

可以通过 `autosize` 设置输入框的最小展示行数和最大展示行数。 `autosize` 是一个对象 默认值为 `{ minRows: 1, maxRows: 6 }` 。超出最大行数时，输入框会自动出现滚动条。

### 输入框组件各种状态

[组件状态](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-state)

可以通过简单属性是，实现组件的状态

💌 Info

- 通过 `loading` 属性，可以控制输入框是否加载中。
- 通过 `readOnly` 属性，可以控制输入框是否可编辑。
- 通过 `disabled` 属性，可以控制输入框是否禁用。
- 通过 `clearable` 属性，可以控制输入框是否出现删除按钮，实现清空。
- 通过 `inputWidth` 属性，可以控制输入框的宽度。默认为 `100%` 。

### 提交方式

[提交模式](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-submit-type)

通过 `submitType` 控制换行与提交模式。默认 `'enter'` 。即 回车提交， `'shift + Enter'` 换行。

💌 Info

- `submitType='enter'` 设置 回车提交， `'shift + Enter'` 换行。
- `submitType='shiftEnter'` 设置 `'shift + Enter'` 提交，回车换行。
- `submitType='cmdOrCtrlEnter'` 设置 `'cmd + Enter'` 或 `'ctrl + Enter'` 提交，回车换行。
- `submitType='altEnter'` 设置 `'alt + Enter'` 提交，回车换行。

### 语音识别

📌 Warning

浏览器内置语音识别 API，可以使用组件库内置的 [`useRecord`](https://element-plus-x.com/components/useRecord/) **hooks** 更方便内置语音识别集成和控制

内置语音识别： 自定义语音识别：

[语音识别](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-allow-speech)

内置 `语音识别` 功能，通过 `allowSpeech` 属性开启即可。调用浏览器原生的语音识别 API，在 `谷歌浏览器` 中使用，需要在 `🪄魔法环境` 中才能正常使用。

💌 Info

如果你不想使用内置的 `语音识别` 功能，可以通过 `@recording-change` 事件来监听录音状态，自行实现语音识别功能。

你也可以通过组件 ref 实例对象进行调用

- `senderRef.value.startRecognition()` 触发开始录音
- `senderRef.value.stopRecognition()` 触发结束录音

### 变体-垂直样式

深度思考

左边是自定义 prefix 前缀 右边是自定义 操作列表

[变体](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-variant)

通过 `variant` 属性设置输入框的变体。默认 'default' | 上下结构 'updown'

这个属性，将左右结构的 输入框，变成 上下结构的 输入框。上面为 输入框，下面为 内置的 前缀和操作列表栏

### 自定义操作列表

[操作列表插槽](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-action-list)

📌 Warning

`1.0.81 版本` 前，在自定义插槽的时候，会牺牲内置的操作按钮。我们在 `1.0.81 版本` 推出了流式请求的 hooks，可以让用户更好的控制流式请求，从而更好的自己定义 `#action-list` 插槽。详情请查看我们的项目模版中主推的一个请求库，对标 Axios [hook-fetch](https://www.npmjs.com/package/hook-fetch) 。

此温馨提示更新时间： `2025-07-05`

通过 `#action-list` 插槽用于自定义输入框的操作列表内容。

💌 Info

当你使用 `#action-list` 插槽时，会隐藏内置的输入框的操作按钮。你可以通过和 `组件实例方法` 相结合，实现更丰富的操作。

### 自定义前缀

[前缀插槽](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-prefix)

通过 `#prefix` 插槽用于自定义输入框的前缀内容。

### 自定义头部

### 自定义底部

### 自定义输入框样式

深度思考

[自定义输入框样式](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-input-style)

通过 `input-style` 方便对输入框的样式透传

### 触发指令

[指令](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-trigger)

输入框，内置指令弹框，方便调用指令操作

💌 Info

- 通过 `triggerStrings` 属性，设置 指令触发字符，类型一个 字符数组 \['/', '@'\]
- 通过 v-model 绑定 `triggerPopoverVisible` 属性，控制指令弹框是否可见

`v-model:trigger-popover-visible="triggerVisible"`

- 通过 `triggerPopoverWidth` 属性，设置指令弹框宽度 默认 `'fit-content'`
- 通过 `triggerPopoverLeft` 属性，设置指令弹框距离左侧距离 默认 `'0px'`
- 通过 `triggerPopoverOffset` 属性，设置指令弹框和输入框的距离 默认 `8`
- 通过 `triggerPopoverPlacement` 属性，设置指令弹框弹出位置 同 el-popover 的 placement 属性一致，默认 `'top-start'`

取值 `'top'` | `'top-start'` | `'top-end'` | `'bottom'` | `'bottom-start'` | `'bottom-end'` | `'left'` | `'left-start'` | `'left-end'` | `'right'` | `'right-start'` | `'right-end'`

- `@trigger` 设置指令弹框显示隐藏发生改变的回调方法

💡 Tip

- `@trigger` 当你要在指令被触发的时候做某些事，但是不想要内置的弹框样式时，可以不用 v-model:trigger-popover-visible="triggerVisible"，这样 **内置弹框** 就不会出现

### 自定义指令弹框

[自定义弹框内容](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-trigger-popover)

💡 Tip

自定义弹框内容，如果你只是简单匹配开头某个字符，可以这个组件。

📌 Warning

💌 温馨提示：V1.3.1 开始，组件 ref 可以获取弹框打开状态属性 `popoverVisible` ，和弹框内置输入框的实例 `inputInstance` 。

意味着：

1. 可以通过弹框的是否打开装填进行一些判断处理。
2. 弹框将可以支持更丰富的自定义事件。

该温馨提示时间 2025-07-21

### 输入框聚焦控制

[聚焦失焦](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-focus)

通过 ref 选项控制聚焦。

💌 Info

通过组件实例控制

- `senderRef.value.focus('all')` 聚焦到整个文本 （默认）
- `senderRef.value.focus('start')` 聚焦到文本最前方
- `senderRef.value.focus('end')` 聚焦到文本最后方
- `senderRef.value.blur()` 失去焦点

### 黏贴文件

[黏贴文件](https://element-plus-x.com/zh/components/sender/#zh-components-sender-demos-pasteFile)

使用 `pasteFile` 获取黏贴的文件，配合 `Attachments` 进行文件上传展示。

## 属性

| 属性名 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `v-model` | String | 否 | '' | 输入框的绑定值，使用 `v-model` 进行双向绑定。 |
| `placeholder` | String | 否 | '' | 输入框的提示语文本。 |
| `auto-size` | Object | 否 | { minRows:1, maxRows:6 } | 设置输入框的最小展示行数和最大展示行数。 |
| `read-only` | Boolean | 否 | false | 输入框是否为只读状态。 |
| `disabled` | Boolean | 否 | false | 输入框是否为禁用状态。 |
| `submitBtnDisabled` | Boolean \| undefined | 否 | undefined | 内置发送按钮禁用状态。(注意使用场景) |
| `loading` | Boolean | 否 | false | 是否显示加载状态。为 `true` 时，输入框会显示加载动画。 |
| `clearable` | Boolean | 否 | false | 输入框是否可清空内容。展示默认清空按钮 |
| `allowSpeech` | Boolean | 否 | false | 是否允许语音输入。默认展示内置语音识别按钮,内置浏览器内置语音识别 API |
| `submitType` | String | 否 | 'enter' | 提交方式，支持 `'shiftEnter'` （按 `Shift + Enter` 提交）、 `'cmdOrCtrlEnter'` （按 `Command + Enter` 或 `Ctrl + Enter` 提交）、 `'altEnter'` （按 `Alt + Enter` 提交）。 |
| `headerAnimationTimer` | Number | 否 | 300 | 输入框的自定义头部显示时长，单位为 `ms` 。 |
| `inputWidth` | String | 否 | '100%' | 输入框的宽度。 |
| `variant` | String | 否 | 'default' | 输入框的变体类型，支持 `'default'` 、 `'updown'` 。 |
| `showUpdown` | Boolean | 否 | true | 当变体为 `updown` 时，是否展示内置样式。 |
| `inputStyle` | Object | 否 | {} | 输入框的样式。 |
| `triggerStrings` | string\[\] | 否 | \[\] | 触发指令的 `字符串数组` 。 |
| `triggerPopoverVisible` | Boolean | 否 | false | 触发指令的 `弹框` 是否可见。需要使用 `v-model:triggerPopoverVisible` 进行控制。 |
| `triggerPopoverWidth` | String | 否 | 'fit-content' | 触发指令的 `弹框` 的宽度。可使用百分比等css单位。 |
| `triggerPopoverLeft` | String | 否 | '0px' | 触发指令的 `弹框` 的左边距。可使用百分比等css单位。 |
| `triggerPopoverOffset` | Number | 否 | 8 | 触发指令的 `弹框` 的间距。只能是数字类型，单位px |
| `triggerPopoverPlacement` | String | 否 | 'top-start' | 触发指令的 `弹框` 的位置。取值： `'top'` \| `'top-start'` \| `'top-end'` \| `'bottom'` \| `'bottom-start'` \| `'bottom-end'` \| `'left'` \| `'left-start'` \| `'left-end'` \| `'right'` \| `'right-start'` \| `'right-end'` |

## 事件

| 事件名 | 说明 | 回调参数 |
| --- | --- | --- |
| `submit` | 内置 `提交按钮` 提交时触发的事件。 | 无 |
| `cancel` | 内置 `loading按钮` 点击时触发的事件。 | 无 |
| `recordingChange` | 内置语音识别状态变化时触发的事件。 | 无 |
| `trigger` | 指令弹框发生变化时触发的事件。 | `interface TriggerEvent{oldValue: string; newValue: string; isOpen: boolean; }` |
| `pasteFile` | 黏贴文件时触发的事件 | `interface PasteFileEvent{firstFile: File; fileList: FileList}` |

## Ref 实例方法

| 属性名 | 类型 | 描述 |
| --- | --- | --- |
| `openHeader` | Function | 打开输入框的自定义头部。 |
| `closeHeader` | Function | 关闭输入框的自定义头部。 |
| `clear` | Function | 清空输入框的内容。 |
| `blur` | Function | 移除输入框的焦点。 |
| `focus` | Function | 聚焦输入框。 默认 `focus('all')` 聚焦整个文本， `focus('start')` 聚焦文本最前方， `focus('end')` 聚焦文本最后方。 |
| `submit` | Function | 提交输入内容。 |
| `cancel` | Function | 取消加载状态。 |
| `startRecognition` | Function | 开始语音识别。 |
| `stopRecognition` | Function | 停止语音识别。 |
| `popoverVisible` | Boolean | 触发指令的 `弹框` 可见性。 |
| `inputInstance` | Object | 输入框实例。 |

## 插槽

| 插槽名 | 参数 | 类型 | 描述 |
| --- | --- | --- | --- |
| `#header` | \- | Slot | 用于自定义输入框的头部内容。 |
| `#prefix` | \- | Slot | 用于自定义输入框的前缀内容。 |
| `#action-list` | \- | Slot | 用于自定义输入框的操作列表内容。 |
| `#footer` | \- | Slot | 用于自定义输入框的尾部内容。 |

## 功能特性

1. **焦点控制** ：支持将焦点设置到文本最前方、最后方或选中整个文本，也可取消焦点。
2. **自定义内容** ：提供头部、前缀、操作列表等插槽，允许用户自定义这些部分的内容。
3. **提交功能** ：支持按 `Shift + Enter` 提交输入内容，提交后可执行自定义操作。
4. **加载状态** ：可显示加载状态，模拟提交处理过程。
5. **语音输入** ：支持语音输入功能，提升输入的便捷性。
6. **清空功能** ：输入框可清空内容，方便用户重新输入。