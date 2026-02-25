---
title: "MentionSender 提及输入框 🦥 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/mentionSender/"
author:
published: 2025-08-11
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## MentionSender 提及输入框 🦥

## 介绍

`MentionSender` 是用于聊天的输入框组件。

📌 Warning

他和 `Sender` 组件的功能基本一样，唯一的区别就是 `指令的弹框` **相关的属性和方法** 不同。点击此处快速了解区别 👉 [**指令区别**](https://element-plus-x.com/components/mentionSender/#packages-vue-element-plus-x-src-mentionSender-demos-options)

我们暂时没有考虑将 `MentionSender` 和 `Sender` 两个 **指令功能** 放到一起，仅仅通过组件进行区分。

## 代码演示

### 基础用法

[基本使用](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-basic)

这是一个 `MentionSender` 输入框，最简单的使用例子。

### 提示语

[提示语](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-placeholder)

可以通过 `placeholder` 设置输入框的提示语。

### 双向绑定（未绑定，值不会变）

[受控组件](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-v-model)

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

[超长文字输入框](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-autosize)

可以通过 `autosize` 设置输入框的最小展示行数和最大展示行数。 `autosize` 是一个对象 默认值为 `{ minRows: 1, maxRows: 6 }` 。超出最大行数时，输入框会自动出现滚动条。

### 输入框组件各种状态

[组件状态](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-state)

可以通过简单属性是，实现组件的状态

💌 Info

- 通过 `loading` 属性，可以控制输入框是否加载中。
- 通过 `readOnly` 属性，可以控制输入框是否可编辑。
- 通过 `disabled` 属性，可以控制输入框是否禁用。
- 通过 `clearable` 属性，可以控制输入框是否出现删除按钮，实现清空。
- 通过 `inputWidth` 属性，可以控制输入框的宽度。默认为 `100%` 。

### 提交方式

[提交模式](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-submit-type)

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

[语音识别](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-allow-speech)

内置 `语音识别` 功能，通过 `allowSpeech` 属性开启即可。调用浏览器原生的语音识别 API，在 `谷歌浏览器` 中使用，需要在 `🪄魔法环境` 中才能正常使用。

💌 Info

如果你不想使用内置的 `语音识别` 功能，可以通过 `@recording-change` 事件来监听录音状态，自行实现语音识别功能。

你也可以通过组件 ref 实例对象进行调用

- `senderRef.value.startRecognition()` 触发开始录音
- `senderRef.value.stopRecognition()` 触发结束录音

### 变体-垂直样式

深度思考

左边是自定义 prefix 前缀 右边是自定义 操作列表

[变体](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-variant)

通过 `variant` 属性设置输入框的变体。默认 'default' | 上下结构 'updown'

这个属性，将左右结构的 输入框，变成 上下结构的 输入框。上面为 输入框，下面为 内置的 前缀和操作列表栏

### 自定义操作列表

[操作列表插槽](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-action-list)

通过 `#action-list` 插槽用于自定义输入框的操作列表内容。

💌 Info

当你使用 `#action-list` 插槽时，会隐藏内置的输入框的操作按钮。你可以通过和 `组件实例方法` 相结合，实现更丰富的操作。

### 自定义前缀

[前缀插槽](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-prefix)

通过 `#prefix` 插槽用于自定义输入框的前缀内容。

### 自定义头部

### 自定义底部

### 自定义输入框样式

深度思考

[自定义输入框样式](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-input-style)

通过 `input-style` 方便对输入框的样式透传

### 输入框聚焦控制

[聚焦失焦](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-focus)

通过 ref 选项控制聚焦。

💌 Info

通过组件实例控制

- `senderRef.value.focus('all')` 聚焦到整个文本 （默认）
- `senderRef.value.focus('start')` 聚焦到文本最前方
- `senderRef.value.focus('end')` 聚焦到文本最后方
- `senderRef.value.blur()` 失去焦点

## 提及指令使用介绍（区别Sender组件）

📌 Warning

下面展示和 `Sender` 组件 **不一样** 的指令相关 **属性方法** 。使用时请注意 **使用区别**

**💌 如果你需要在一段内容中间，触发一个列表的提及指令，可以使用这个组件。**

此温馨提示更新时间： `2025-04-16`

### 触发指令自定义数组

[options 提及选项列表](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-options)

- 通过 `options` 属性，可以传入一个数组，用于定义提及选项列表。
- 通过 `triggerStrings` 属性 触发字段的前缀。 这里和 `Sender` 组价不同，这里的字符串长度必须且只能为 1。

💌 Info

光设置 `options` 属性，不能开启提及功能。需要 `triggerStrings` 属性来开启提及功能。

### 自定义触发指令字符串

[triggerStrings 触发字段](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-trigger-strings)

通过 `triggerStrings` 属性 触发字段。这里和 `Sender` 组价不同，这里的字符串长度必须且只能为 1。类型是 `Array<string>` 。

如果需要通过 **多个字符串触发** ，可以搭配 `@search` 事件控制显示浮层内容。

💌 Info

光设置 `options` 属性，不能开启提及功能。需要 `triggerStrings` 属性来开启提及功能。

### 自定义触发指令分隔符

[trigger-split 指令分割符](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-trigger-split)

用于拆分提及的字符。 字符串长度必须且只能为 1，默认为 `' '` 。

### 触发指令加载中

### 自定义触发指令过滤

[filter-option 过滤筛选](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-filter-option)

通过 `filter-option` 定制筛选器选项逻辑，通过一个方法，返回为 `true` 或 `false` 来控制选项的过滤结果，你也可以理解为搜索的过滤逻辑。

类型是 `(pattern: string, option: MentionOption) => boolean`

### 整体删除

[whole 整体删除](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-whole)

- 将 `whole` 属性设置为 `true` ，当您按下退格键时，此处的 `mention` 区域将作为一个整体被删除。
- 设置 `check-is-whole` 属性来自定义检查逻辑。当你需要做多个条件时，你可以使用 `check-is-whole` 属性来自定义检查逻辑。
- check-is-whole 属性不是事件，类型为 (pattern: string, prefix: string) => boolean 返回 `true` 表示匹配成功要被整体删除，返回 `false` 表示匹配失败不会被整体删除。 默认为 `true`

### 触发指令弹框位置

[trigger-popover-placement 指令弹框弹出方向](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-trigger-popover-placement)

通过 `trigger-popover-placement` 设置 弹出方向。默认是 `'top'`, 可以设置为 `'bottom'` 。目前只支持 `'top'` 和 `'bottom'` 两种。

### 触发指令弹框偏移

[trigger-popover-offset 弹出距离窗口偏移](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-trigger-popover-offset)

通过 `triggerPopoverOffset` 属性可以设置浮层距离窗口的偏移量。默认值 20，表示为 20px。

### 提弹框 插槽

[solts 各种插槽](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-solts)

📌 Warning

💌 温馨提示：V1.3.1 开始，组件 ref 可以获取弹框打开状态属性 `popoverVisible` ，和弹框内置输入框的实例 `inputInstance` 。

意味着：

1. 可以通过弹框的是否打开装填进行一些判断处理。
2. 弹框将可以支持更丰富的自定义事件。

该温馨提示时间 2025-07-21

### 搜索事件

### 选择事件

[select 选择事件](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-select)

当用户选择选项时触发

### 黏贴文件

[黏贴文件](https://element-plus-x.com/zh/components/mentionSender/#zh-components-mentionSender-demos-pasteFile)

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
| `select` | 按下触发字段时触发 | `option: MentionOption` |
| `search` | 当用户选择选项时触发 | `searchValue: string, prefix: string` |
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
| `#trigger-label` | `#trigger-label={ item, index }` | Slot | 用于自定义触发弹框标签内容。 |
| `#trigger-loading` | \- | Slot | 用于自定义触发弹框加载状态内容。 |
| `#trigger-header` | \- | Slot | 用于自定义触发弹框头部内容。 |
| `#trigger-footer` | \- | Slot | 用于自定义触发弹框底部内容。 |

## 功能特性

1. **焦点控制** ：支持将焦点设置到文本最前方、最后方或选中整个文本，也可取消焦点。
2. **自定义内容** ：提供头部、前缀、操作列表等插槽，允许用户自定义这些部分的内容。
3. **提交功能** ：支持按 `Shift + Enter` 提交输入内容，提交后可执行自定义操作。
4. **加载状态** ：可显示加载状态，模拟提交处理过程。
5. **语音输入** ：支持语音输入功能，提升输入的便捷性。
6. **清空功能** ：输入框可清空内容，方便用户重新输入。