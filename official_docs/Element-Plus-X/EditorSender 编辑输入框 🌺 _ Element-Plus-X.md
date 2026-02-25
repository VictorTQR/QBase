---
title: "EditorSender 编辑输入框 🌺 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/editorSender/"
author:
published: 2025-08-06
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## EditorSender 编辑输入框 🌺

## 介绍

**`EditorSender`** 重磅来袭 🙊 专为 **`多模态模型`** 、 **`自定义提示词场景`** 设计的输入框组件，解决 **标签插入，内容提及，自定义提示词输入** 等核心开发需求，更好的展现多模态功能的强大。

📌 Warning

`EditorSender` 组件 和 `Sender` 组件 有一定的开发上的差异，请根据实际情况选择使用。

![](https://element-plus-x.com/assets/image.BX3hvDyd.png)

## 代码演示

### 基础用法

  

请输入内容

[基本使用](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-basic)

这是一个 `EditorSender` 输入框，最简单的使用例子。

### 提示语

  

💌 欢迎使用 Element-Plus-X ~

[提示语](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-placeholder)

通过 `placeholder` 设置输入框的提示语。

### 自动聚焦

  

请输入内容

[自动聚焦](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-autoFocus)

通过 `auto-focus` 设置输入框自动聚焦。在输入框生成后自动聚焦

### 状态属性

  

加载中...

  

禁用

  

请输入内容

[组件状态](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-state)

可以通过简单属性是，实现组件的状态

💌 Info

- 通过 `loading` 属性，可以控制输入框内置按钮加载中。
- 通过 `disabled` 属性，可以控制输入框内置按钮是否禁用。
- 通过 `clearable` 属性，可以控制输入框是否出现删除按钮，实现清空。

### 变体-垂直样式

  

请输入内容

深度思考

  

请输入内容

[变体](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-variant)

通过 `variant` 属性设置输入框的变体。\[ 默认 'default' | 上下结构 'updown' \]

这个属性，将左右结构的 输入框，变成 上下结构的 输入框。上面为 输入框，下面为 内置的 前缀和操作列表栏

### 自定义操作列表

  

请输入内容

[操作列表插槽](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-action-list)

通过 `#action-list` 插槽用于自定义输入框的操作列表内容。可以和 组件Ref实例的 `getCurrentValue` 方法结合使用，获取当前输入框的值。

📌 Warning

`1.0.81 版本` 前，在自定义插槽的时候，会牺牲内置的操作按钮。我们在 `1.0.81 版本` 推出了流式请求的 hooks，可以让用户更好的控制流式请求，从而更好的自己定义 `#action-list` 插槽。详情请查看我们的项目模版中主推的一个请求库，对标 Axios [hook-fetch](https://www.npmjs.com/package/hook-fetch) 。

此温馨提示更新时间： `2025-08-06`

💌 Info

当你使用 `#action-list` 插槽时，会隐藏内置的输入框的操作按钮。你可以通过和 `组件实例方法` 相结合，实现更丰富的操作。

### 自定义前缀

  

请输入内容

[前缀插槽](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-prefix)

通过 `#prefix` 插槽用于自定义输入框的前缀内容。

### 自定义头部

  

请输入内容

### 自定义底部

### 自定义输入框样式

  

请输入内容

  

请输入内容

[自定义输入框样式](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-custom-style)

通过 `customStyle` 方便对输入框的样式控制，你可以设置 `maxHeight` 来限制输入框的高度。这样实现在一定的高度下出现滚动条。

### 限制最大输入长度

  

请输入内容

[限制最大输入长度](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-max-length)

通过 `maxLength` 限制输入框最大字数。

💔 Danger

该配置项性能开销较大 非必要情况请别设置（像豆包和文心一言都不对这块做限制，不应因小失大）

### 提交方式

  

请输入内容

[提交模式](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-submit-type)

通过 `submitType` 控制换行与提交模式。默认 `'enter'` 。即 回车提交， `'shift + Enter'` 换行。

💌 Info

- `submitType='enter'` 设置 回车提交， `'shift + Enter'` 换行。
- `submitType='shiftEnter'` 设置 `'shift + Enter'` 提交，回车换行。

## 高级用法

### 插入 text 内容

  

请输入内容

[插入 text 内容](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-insert-text)

使用组件 Ref 调用 `setText` 方法在光标位置插入 text 内容。

### 插入 html 内容

  

请输入内容

[插入 html 内容](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-insert-html)

使用组件 Ref 调用 `setHtml` 方法在光标位置插入 html 内容。

📌 Warning

插入的html标签必须是 行内 或 行内块元素，如果需要块级元素标签 请自行插入行内元素然后修改其css属性为块级元素

### 插入 选择标签

  

请输入内容

[插入 选择标签](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-insert-select-tag)

通过 `selectList` 属性配置选择标签配置数组。

使用组件 Ref 调用 `setSelectTag` 方法在光标位置插入 **选择标签** 内容，这个方法接受两个参数，第一个参数是选择标签的标识，第二个参数是选择标签的选项标识（默认值）。

💌 Info

你还可以从外部调用 `openSelectDialog` 方法打开选择标签弹窗，这个方法接受一个配置对象，配置对象的类型如下：

展开查看配置数组类型

### 插入 输入标签

  

请输入内容

[插入 输入标签](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-insert-input-tag)

通过 `selectList` 属性配置选择标签配置数组。 使用组件 Ref 调用 `setInputTag` 方法在光标位置插入 **输入标签** 内容。

这个方法接受三个参数，第一个参数是输入标签的标识（自己定义），第二个参数是输入标签的占位符，第三个参数是输入标签的默认值。

### 插入 用户标签

  

@ 符号触发用户选择

[插入 用户标签](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-insert-user-tag)

通过 `userList` 属性配置用户标签配置数组。 `@` 触发用户标签弹窗。

使用组件 Ref 调用 `setUserTag` 方法在光标位置插入 **用户标签** 内容，这个方法接受一个参数，用户标签的标识。如果你想支持拼音搜索，请为用户标签配置 `pinyin` 属性。

展开查看配置数组类型

### 插入 自定义标签

  

\# 符号触话题选择，/ 符号触发文件选择

[插入 自定义标签](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-insert-custom-tag)

通过 `customTrigger` 属性配置自定义标签配置数组。

使用组件 Ref 调用 `setCustomTag` 方法在光标位置插入 **自定义标签** 内容，这个方法接受两个参数，第一个参数为自定义标签的标识符前缀，第二个参数为插入的标签列表项的 `id` 。

展开查看配置数组类型

### 混合标签覆盖写入

  

请输入内容

[混合标签覆盖写入](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-mix-tag)

通过 组件 Ref 实例的 `setMixTags` 方法设置混合标签，混合标签会覆盖写入已有的内容。

### 前置提示标签

  

请输入内容

[前置提示标签](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-prefix-tag)

通过 组件 Ref 实例的 `openTipTag` 和 `closeTipTag` 方法打开和关闭前置提示标签。

### 异步加载 @成员

  

@ 符号触发用户选择

[异步加载 @成员示例](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-async-user-tag)

通过 `asyncMatchFun` 属性配置异步匹配函数。 `@` 触发用户标签弹窗。

### 自定义提及弹框

  

这里是自定义弹窗，你可以试着输入@，!，#这些触发符号

[异步加载 @成员示例](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-custom-mention)

通过 `asyncMatchFun` 属性配置异步匹配函数。 `@` 触发用户标签弹窗。

### 设备类型 pc/h5

  

这里是自定义弹窗，你可以 在 h5 环境中，试着输入@触发人员选择弹窗

[设备类型](https://element-plus-x.com/zh/components/editorSender/#zh-components-editorSender-demos-device)

使用 `device` 属性，设置设备类型，默认是 `pc`

📌 Warning

传入 `h5` 时，弹出选择功能的交互，需要注意参考自定义弹出选择功能实现交互

## 属性

| 属性名 | 类型 | 是否必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `placeholder` | String | 否 | '请输入内容' | 输入框的提示语文本 |
| `device` | 'pc' \| 'h5' | 否 | 'pc' | 使用编辑器的设备类型，PC端内置丰富的弹出选择功能，H5端需参考自定义弹窗实现 |
| `autoFocus` | Boolean | 否 | false | 是否在组件挂载后自动聚焦到输入框 |
| `variant` | 'default' \| 'updown' | 否 | 'default' | 输入框的变体类型，default为水平布局，updown为垂直布局 |
| `userList` | UserInfo\[\] | 否 | \[\] | @提及功能的用户列表 |
| `customTrigger` | CustomTag\[\] | 否 | \[\] | 扩展自定义弹窗的触发配置列表 |
| `selectList` | SelectTag\[\] | 否 | \[\] | 配置标签下拉选择的选项列表 |
| `maxLength` | Number | 否 | undefined | 限制输入框的最大字数，性能开销较大，非必要不建议设置 |
| `submitType` | 'enter' \| 'shiftEnter' | 否 | 'enter' | 控制换行与提交模式：'enter'为Enter提交、Shift+Enter换行；'shiftEnter'为Shift+Enter提交、Enter换行 |
| `customStyle` | Record | 否 | {} | 用于修改输入框的样式 |
| `loading` | Boolean | 否 | false | 发送按钮的加载状态，为true时显示加载动画 |
| `disabled` | Boolean | 否 | false | 是否禁用输入框，禁用后无法输入和操作 |
| `clearable` | Boolean | 否 | false | 是否显示清空按钮 |
| `headerAnimationTimer` | Number | 否 | 300 | 头部展开/收起动画的时长，单位为ms |
| `asyncMatchFun` | (searchVal: string) => Promise | 否 | undefined | 异步加载群成员的方法，用于@提及功能的远程搜索 |
| `customDialog` | Boolean | 否 | false | 是否启用自定义弹窗，开启后内部弹窗将不会创建，需自行实现弹窗逻辑 |

## 事件

| 事件名 | 说明 | 回调参数 |
| --- | --- | --- |
| `submit` | 提交内容时触发 | `payload: SubmitResult` - 包含提交的各类内容 |
| `change` | 输入内容发生变化时触发 | 无 |
| `cancel` | 取消加载状态时触发 | 无 |
| `showAtDialog` | 显示@用户弹窗时触发 | 无 |
| `showSelectDialog` | 显示选择标签弹窗时触发 | `key: string` - 标签键名, `elm: HTMLElement` - 触发元素 |
| `showTagDialog` | 显示自定义标签弹窗时触发 | `prefix: string` - 标签前缀 |

## Ref 实例方法

| 方法名 | 类型 | 描述 |
| --- | --- | --- |
| `getCurrentValue` | () => SubmitResult | 获取当前输入框的内容，包括文本、HTML和各类标签信息 |
| `focusToStart` | () => void | 将光标聚焦到文本最前方 |
| `focusToEnd` | () => void | 将光标聚焦到文本最后方 |
| `blur` | () => void | 移除输入框的焦点 |
| `selectAll` | () => void | 全选输入框内容 |
| `clear` | (txt?: string) => void | 清空输入框内容，可选参数txt为清空后插入的文本 |
| `setSelectTag` | (key: string, tagId: string) => void | 插入一个选择标签 |
| `setInputTag` | (key: string, placeholder: string, defaultValue?: string) => void | 插入一个输入标签 |
| `setUserTag` | (userId: string) => void | 插入一个@提及标签 |
| `setCustomTag` | (prefix: string, id: string) => void | 插入一个自定义触发符标签 |
| `setMixTags` | (tags: MixTag\[\]\[\]) => void | 混合式插入多种标签 |
| `setHtml` | (html: string) => void | 在当前光标处插入HTML片段（建议使用行内或行内块元素） |
| `setText` | (txt: string) => void | 在当前光标处插入文本 |
| `openSelectDialog` | (option: SelectDialogOption) => void | 外部调用唤起标签选择弹窗 |
| `customSetUser` | (user: UserInfo) => void | 自定义弹窗中写入@提及标签（私有API，会自动截取触发符） |
| `customSetTag` | (prefix: string, tag: TagInfo) => void | 自定义弹窗中写入自定义触发符号标签（私有API，会自动截取触发符） |
| `updateSelectTag` | (elm: HTMLElement, tag: TagInfo) => void | 更新选择标签内容 |
| `openTipTag` | (options: TipOptions) => void | 打开前置提示标签 |
| `closeTipTag` | () => void | 关闭前置提示标签 |
| `chat` | ChatArea 实例 | 暴露的chat实例对象 |
| `opNode` | ChatOperateNode 实例 | 暴露的ChatNode操作对象 |
| `chatState` | ChatState 对象 | 暴露的组件状态对象 |

## 插槽

| 插槽名 | 参数 | 描述 |
| --- | --- | --- |
| `#header` | \- | 用于自定义输入框的头部内容 |
| `#prefix` | \- | 用于自定义输入框的前缀内容 |
| `#action-list` | \- | 用于自定义输入框的操作列表内容 |
| `#footer` | \- | 用于自定义输入框的底部内容 |

## 功能特性

1. **全类型标签引擎** ：无缝支持@用户、选择标签、自定义标签等多类型标记，标签插入/更新/管理一键搞定，满足复杂内容标记需求。
2. **跨设备自适应交互** ：PC端内置弹窗系统，H5端支持自定义弹窗，自动适配不同设备操作习惯，兼顾原生体验与定制自由。