---
title: "Attachments 附件上传组件 📪️ | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/attachments/"
author:
published: 2025-07-30
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## Attachments 附件上传组件 📪️

## 介绍

`Attachments` 组件是一个功能丰富的附件管理组件，支持文件列表展示、上传、拖拽交互、滚动浏览等功能，适用于需要处理多文件上传和展示的场景（如表单附件、文件管理界面）。组件内置文件上传按钮、拖拽提示区域，并提供灵活的自定义插槽和样式配置

## 代码演示

### 基本使用

[基础用法](https://element-plus-x.com/zh/components/attachments/#zh-components-attachments-demos-base)

基础文件列表展示与上传功能，支持自动生成文件卡片。

### 滚动模式

scrollX

scrollY

wrap

[滚动模式](https://element-plus-x.com/zh/components/attachments/#zh-components-attachments-demos-scroll-mode)

支持横向滚动（ `scrollX` ）、纵向滚动（ `scrollY` ）和自动换行（ `wrap` ）三种布局模式。默认横向

### 自定义文件列表

[自定义文件列表](https://element-plus-x.com/zh/components/attachments/#zh-components-attachments-demos-custom-list)

通过插槽自定义文件列表展示内容（覆盖默认的 `FilesCard` 组件）。

### 拖拽上传

设置全屏拖拽上传： 

在此处拖拽文件上传

[拖拽上传](https://element-plus-x.com/zh/components/attachments/#zh-components-attachments-demos-drag-upload)

`drag` 属性，开启拖拽上传功能，支持自定义拖拽目标区域和视觉反馈。

`dragTarget` 属性 可以是一个 id 选择器字符串，可以是一个 Ref 实例，也可以是 HTMLElement dom 。不设置就默认拖拽范围为当前列表。

如果想整个页面拖拽上传，请将 `drag` 设置为 `true` ，并设置 `drag-target` 为 `'document.body'` 。

### 自定义滚动按钮

[自定义滚动按钮](https://element-plus-x.com/zh/components/attachments/#zh-components-attachments-demos-custom-scroll-buttons)

覆盖默认的左右滚动按钮样式和交互。

## 属性

| 属性名 | 类型 | 是否必填 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `items` | `FilesCardProps[]` | 否 | `[]` | 文件列表数据（包含文件基础信息，如名称、类型、状态等） |
| `overflow` | `'scrollX' \| 'scrollY' \| 'wrap'` | 否 | `'scrollX'` | 滚动布局模式（横向滚动/纵向滚动/自动换行） |
| `listStyle` | `CSSProperties` | 否 | `{}` | 列表容器自定义样式 |
| `uploadIconSize` | `string` | 否 | `'64px'` | 上传按钮图标尺寸 |
| `dragTarget` | `string \| Ref<HTMLElement> \| null` | 否 | `null` | 拖拽目标元素（支持选择器字符串或 DOM 引用，默认使用组件自身） |
| `hideUpload` | `boolean` | 否 | `false` | 是否隐藏默认上传按钮 |
| `limit` | `number` | 否 | `undefined` | 文件数量限制（超过时隐藏上传按钮） |
| `beforeUpload` | `(file: File) => boolean` | 否 | `undefined` | 上传前校验函数（返回 `false` 可阻止上传） |
| `httpRequest` | `(options: { file: File }) => Promise<void>` | 否 | `undefined` | 自定义上传请求函数（需返回 Promise） |

## 插槽

| 插槽名 | 插槽参数 | 描述 |
| --- | --- | --- |
| `#file-list` | `{ items: FilesCardProps[] }` | 自定义文件列表内容（覆盖默认的 `FilesCard` 展示） |
| `#prev-button` | `{ show: boolean, onScrollLeft: () => void }` | 自定义左侧滚动按钮（ `scrollX` 模式生效）， `show` 控制按钮显示状态 |
| `#next-button` | `{ show: boolean, onScrollRight: () => void }` | 自定义右侧滚动按钮（ `scrollX` 模式生效）， `show` 控制按钮显示状态 |
| `#empty-upload` | `-` | 空文件列表时的上传区域自定义（默认显示带加号的上传按钮） |
| `#no-empty-upload` | `-` | 非空文件列表时的上传占位符自定义（默认显示带加号的上传按钮） |
| `#drop-area` | `-` | 拖拽上传时的遮罩层内容自定义（默认显示上传提示图标和文本） |

## 事件

| 事件名 | 回调参数 | 描述 |
| --- | --- | --- |
| `uploadChange` | `(file: File, fileList: FileListProps)` | 文件选择变化时触发（包含选中文件和当前文件列表） |
| `uploadSuccess` | `(response: any, file: File, fileList: FileListProps)` | 文件上传成功时触发（返回接口响应、当前文件及文件列表） |
| `uploadError` | `(error: any, file: File, fileList: FileListProps)` | 文件上传失败时触发（返回错误信息、当前文件及文件列表） |
| `uploadDrop` | `(files: File[], props: FileListProps)` | 拖拽文件释放时触发（包含拖拽文件数组和组件属性） |
| `deleteCard` | `(item: FilesCardProps, index: number)` | 文件卡片删除按钮点击时触发（返回被删除文件信息及索引） |

## 支持 el-upload 属性

组件内部使用了 **elementplus** `el-upload` 组件，因此支持其大部分上传属性，如： `httpRequest` 、 `beforeUpload` 等。 详情请参考： [element-plus/upload](https://element-plus.org/zh-CN/component/upload.html)

## 功能特性

1. **多布局模式** 支持 `scrollX` （横向滚动）、 `scrollY` （纵向滚动）、 `wrap` （自动换行）三种布局，适配不同屏幕空间和文件数量。
2. **拖拽上传交互** 内置拖拽目标区域（可自定义 `dragTarget` ），拖拽时显示半透明遮罩层提示，支持文件夹过滤和文件类型校验。
3. **高度可定制化** 通过 `#file-list` 插槽完全自定义文件列表展示（如替换为自定义卡片组件），支持自定义滚动按钮、上传按钮样式。
4. **文件状态管理** 配合 `FilesCard` 组件，支持文件上传中（进度条）、完成、失败等状态可视化，自动同步文件列表更新。