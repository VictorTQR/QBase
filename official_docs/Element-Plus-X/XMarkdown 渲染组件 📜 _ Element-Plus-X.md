---
title: "XMarkdown 渲染组件 📜 | Element-Plus-X"
source: "https://element-plus-x.com/zh/components/xmarkdown/"
author:
published: 2025-08-08
created: 2026-02-01
description: "A Vue3 + Element-Plus AI Experience Component Library"
tags:
  - "clippings"
---
## XMarkdown 渲染组件 📜

## 介绍

`XMarkdown` 这个组件内置了 **行内代码** 、 **代码块** 、 **数学公式函数（行/块）** 、 **mermaid 图表** 等基础样式。

💌 Info

⚠️ 在这个开发文档中，有一些样式的演示可能不是很好，但是应该不会影响集成的使用。如果有集成或一些使用问题，可以进 👉 [交流群](https://element-plus-x.com/en/introduce.html#%F0%9F%91%A5-%E7%A4%BE%E5%8C%BA%E6%94%AF%E6%8C%81) 获取最新的技术支持。

📌 Warning

文档中所有 demo 案例中 `h函数` 的演示，意味着你可以使用 `h` 函数进行组件的渲染，也可以使用 `自定义Vue组件` 渲染。

**比如说：**

**🙊 其实是可以写成 自定义的组件：**

**💟 在你自定的组件中可以这样获取到 props：**

## 代码演示

### 基本使用

控制台查看增量渲染

## 一级标题

## 二级标题

### 三级标题

#### 四级标题

##### 五级标题

###### 六级标题

**这是粗体文本**  
**这也是粗体文本**

*这是斜体文本*  
*这也是斜体文本*

***这是粗斜体文本***

~~这是带删除线的文本~~

- 无序列表项1
- 无序列表项2
	- 子列表项2.1
	- 子列表项2.2
1. 有序列表项1
2. 有序列表项2
3. 子列表项2.1
4. 子列表项2.2

[Element-Plus-X](https://element-plus-x.com/ "Element-Plus-X")

![示例图片](https://element-plus-x.com/logo.png "一张示例图")

> 这是一段引用文本
> 
> > 这是嵌套的引用文本

---

| 姓名 | 年龄 | 职业 |
| --- | --- | --- |
| 张三 | 25 | 工程师 |
| 李四 | 30 | 设计师 |

### 行内代码

用 ElmentPlusX 表示 行内块代码用 \`\` 语句

### 代码块

```javascript
javascriptconst code = "Element-Plus-X";
```

### 行内公式

$e^{i\pi} + 1 = 0$

### 块级公式

$$
F(\omega) = \int_{-\infty}^{\infty} f(t) e^{-i\omega t} dt
$$

### mermaid 饼状图

```javascript
35%15%15%12%10%8%5%传媒及文化相关游戏开发其他影视动画与特效互联网产品设计广告与市场营销VR/AR开发
```

[基础用法](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-base)

快速渲染一个 Markdown 基础的文本。内置了行内代码、代码块、数学公式函数（行/块）、mermaid 图表等基础样式。

📌 Warning

支持增量更新，可以在控制台查看节点的更新变化。以下代码示例为展示增量更新效果，模拟流式接收字符的逻辑。

### 设置默认 高亮/暗黑

```js
jsconsole.log('hello world');
```

[default-theme-mode 属性](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-default-theme-mode)

通过 `default-theme-mode` 属性，设置代码块高亮，默认是高亮主题还是默认是暗黑主题。

💌 Info

这里文档中演示可能会受 vitePress 的样式影响，请自行查看效果。如果在项目中，使用属性无效，可以加入👉 [交流群](https://element-plus-x.com/en/introduce.html#%F0%9F%91%A5-%E7%A4%BE%E5%8C%BA%E6%94%AF%E6%8C%81) 。反馈一下

### 内置 shiki 主题

代码块高亮内置了多套主题供选择。

```js
jsconsole.log('hello world');
```

[themes 属性](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-shiki-style)

通过 `themes` 属性，对代码块进行主题设置。这个属性是一个对象，高亮和暗黑主题属性，值为内置的一套 `主题ID` 。

我们内置了一下 shiki 样式，你可以在 [shiki-theme](https://shiki.style/themes) 中查看。

📌 Warning

重新设置主题后，可能需要刷新页面才会生效。以下列举了所有内置的 `shiki` 样式所对应的 `主题ID` 。如果你是 ts 项目，开发中应该可以获取到内置的样式主题的类型推断提示。

![](https://cdn.element-plus-x.com/shiki-style.png) 💝查看所有 主题ID 对照表

| 名称（Name） | 中文翻译 | 对应值（ `主题ID` ） |
| --- | --- | --- |
| Andromeeda | 仙女座 | andromeeda |
| Aurora X | 极光X | aurora-x |
| Ayu Dark | Ayu暗色 | ayu-dark |
| Catppuccin Frappé | 卡布奇诺冰沙 | catppuccin-frappe |
| Catppuccin Latte | 卡布奇诺拿铁 | catppuccin-latte |
| Catppuccin Macchiato | 卡布奇诺玛奇朵 | catppuccin-macchiato |
| Catppuccin Mocha | 卡布奇诺摩卡 | catppuccin-mocha |
| Dark Plus | 深色增强 | dark-plus |
| Dracula Theme | 德古拉主题 | dracula |
| Dracula Theme Soft | 德古拉柔和主题 | dracula-soft |
| Everforest Dark | 常绿森林暗色 | everforest-dark |
| Everforest Light | 常绿森林亮色 | everforest-light |
| GitHub Dark | GitHub暗色 | github-dark |
| GitHub Dark Default | GitHub暗色默认 | github-dark-default |
| GitHub Dark Dimmed | GitHub暗色低饱和 | github-dark-dimmed |
| GitHub Dark High Contrast | GitHub暗色高对比 | github-dark-high-contrast |
| GitHub Light | GitHub亮色 | github-light |
| GitHub Light Default | GitHub亮色默认 | github-light-default |
| GitHub Light High Contrast | GitHub亮色高对比 | github-light-high-contrast |
| Gruvbox Dark Hard | Gruvbox暗色高饱和 | gruvbox-dark-hard |
| Gruvbox Dark Medium | Gruvbox暗色中饱和 | gruvbox-dark-medium |
| Gruvbox Dark Soft | Gruvbox暗色低饱和 | gruvbox-dark-soft |
| Gruvbox Light Hard | Gruvbox亮色高饱和 | gruvbox-light-hard |
| Gruvbox Light Medium | Gruvbox亮色中饱和 | gruvbox-light-medium |
| Gruvbox Light Soft | Gruvbox亮色低饱和 | gruvbox-light-soft |
| Houston | 休斯顿 | houston |
| Kanagawa Dragon | 神奈川龙 | kanagawa-dragon |
| Kanagawa Lotus | 神奈川莲 | kanagawa-lotus |
| Kanagawa Wave | 神奈川浪 | kanagawa-wave |
| LaserWave | 激光波 | laserwave |
| Light Plus | 亮色增强 | light-plus |
| Material Theme | Material主题 | material-theme |
| Material Theme Darker | Material主题深色增强 | material-theme-darker |
| Material Theme Lighter | Material主题浅色增强 | material-theme-lighter |
| Material Theme Ocean | Material主题海洋风 | material-theme-ocean |
| Material Theme Palenight | Material主题夜樱色 | material-theme-palenight |
| Min Dark | 极简暗色 | min-dark |
| Min Light | 极简亮色 | min-light |
| Monokai | 莫奈凯 | monokai |
| Night Owl | 夜枭 | night-owl |
| Nord | 诺德 | nord |
| One Dark Pro | One深色专业版 | one-dark-pro |
| One Light | One亮色 | one-light |
| Plastic | 塑料风 | plastic |
| Poimandres | 波伊曼德尔斯 | poimandres |
| Red | 红色主题 | red |
| Rosé Pine | 玫瑰松木 | rose-pine |
| Rosé Pine Dawn | 玫瑰松木黎明 | rose-pine-dawn |
| Rosé Pine Moon | 玫瑰松木月夜 | rose-pine-moon |
| Slack Dark | Slack暗色 | slack-dark |
| Slack Ochin | Slack淡茶 | slack-ochin |
| Snazzy Light | 时尚亮色 | snazzy-light |
| Solarized Dark | 日光暗色 | solarized-dark |
| Solarized Light | 日光亮色 | solarized-light |
| Synthwave '84 | 84年合成波 | synthwave-84 |
| Tokyo Night | 东京之夜 | tokyo-night |
| Vesper | Vesper（黄昏星） | vesper |
| Vitesse Black | 极速黑 | vitesse-black |
| Vitesse Dark | 极速暗色 | vitesse-dark |
| Vitesse Light | 极速亮色 | vitesse-light |

### 单独定义代码块高亮样式

```js
jsconsole.log('hello world');
```

```js
jsconsole.log('hello world');
```

[color-replacements 属性](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-color-replacements)

通过 `color-replacements` 属性，可以单独控制某个主题下的代码颜色。

📌 Warning

注意: 颜色键必须以 `#` 开头，并且为小写格式，否则不生效。

主题ID 会有对应的颜色变量，这个可以在控制台查看，我们可以对内置的颜色变量进行颜色替换。

### 统一覆盖样式

## 一级标题

## 二级标题

### 三级标题

[覆盖样式](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-base-style)

如果你集成该组件时，发现组件内置的样式变的奇怪。可能是你项目的内置全局样式，和这个组件的一些基础样式有冲突。那么你可以通过覆盖样式的方式来解决这个问题。

💌 Info

创建一个样式文件，例如： `self-markdown.css` ，并添加一些自定义样式内容：

将这个文件引入到你的项目，例如：

如果没有覆盖，大概率是因为你设置层级不够，可以尝试样式穿透

下面使用 `github` 样式文件统一覆盖样式做一个示例

### github 样式

## 一级标题

## 二级标题

### 三级标题

[github 样式](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-github-style)

市场上也有很多优秀的作者，开源了他们的 markdown 样式，这里演示一个集成使用 github 样式的案例。

你可以直接下载 [github-markdown.css](https://cdn.jsdelivr.net/npm/github-markdown-css@latest/github-markdown.min.css) 这个文件，或者把样式代码复制到自己的 css 文件中。然后在项目中引用。

📌 Warning

不过值得注意的是，一般这种文件样式，都是被 `markdown-body` 类名包住的。光引入样式文件，是不行的。你可能还需要给 `XMarkdown` 添加一个类名，来让样式生效。这个类名和引入的样式文件中的最外层的类名，应该保持一致。

如果你想单独控制代码块高亮的样式，可以这样：

### allowHtml

<div style="color: red;">这是一个 html 标签测试。</div>

[是否开启 html 标签渲染](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-allow-html)

支持 html 标签渲染，使用 `allowHtml` 属性开启，默认关闭。

### enableLatex

### 行内公式

$e^{i\pi} + 1 = 0$

### 块级公式

$$
F(\omega) = \int_{-\infty}^{\infty} f(t) e^{-i\omega t} dt
$$

[是否开启对 latex 数学公式渲染](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-enable-latex)

支持 latex 数学公式渲染，使用 `enableLatex` 属性开启，默认开启。

### enableBreaks

Mars is  
the fourth planet

[是否开启 breaks 渲染](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-enable-breaks)

支持 remark-breaks 渲染，使用 `enableBreaks` 属性开启，默认开启。

支持硬中断而不需要空格或转义符（将回车符变成 `<br>` ）。让你的内容渲染更加还原。

### 预览 html 代码块

是否显示 html 预览按钮  是否开启安全预览  开启安全预览后，尝试点击加入购物车按钮，不会触发 script 标签中的事件

```html
html<div class="product-card">  <div class="badge">新品</div>  <img src="https://picsum.photos/300/200?product" alt="产品图片">  <div class="content">    <h3>无线蓝牙耳机 Pro</h3>    <p class="description">主动降噪技术，30小时续航，IPX5防水等级</p>    <div class="rating">      <span>★★★★☆</span>      <span class="reviews">(124条评价)</span>    </div>    <div class="price-container">      <span class="price">¥499</span>      <span class="original-price">¥699</span>      <span class="discount">7折</span>    </div>    <div class="actions">      <button class="cart-btn" onclick="addToCart(this)">加入购物车</button>      <button class="fav-btn">❤️</button>    </div>    <div class="meta">      <span>✓ 次日达</span>      <span>✓ 7天无理由</span>    </div>  </div></div><script>  function addToCart(button) {    // 防止重复点击    if (button.disabled) return;        // 禁用按钮    button.disabled = true;    button.innerHTML = '加入中...';        // 模拟添加到购物车的API请求    setTimeout(() => {      // 显示成功消息      button.innerHTML = '✓ 已加入';      button.classList.add('success');            // 3秒后恢复按钮状态      setTimeout(() => {        button.innerHTML = '加入购物车';        button.disabled = false;        button.classList.remove('success');      }, 3000);    }, 800);  };</script><style>  .product-card {  width: 280px;  border-radius: 12px;  overflow: hidden;  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);  position: relative;  background: white;  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}.badge {  position: absolute;  top: 12px;  left: 12px;  background: #ff6b6b;  color: white;  padding: 4px 10px;  border-radius: 4px;  font-weight: bold;  font-size: 12px;  z-index: 2;}img {  width: 100%;  height: 180px;  object-fit: cover;  display: block;}.content {  padding: 16px;}h3 {  margin: 8px 0;  font-size: 18px;  color: #333;}.description {  color: #666;  font-size: 14px;  margin: 8px 0 12px;  line-height: 1.4;}.rating {  display: flex;  align-items: center;  margin: 10px 0;  color: #ffb300;}.reviews {  font-size: 13px;  color: #888;  margin-left: 8px;}.price-container {  display: flex;  align-items: center;  gap: 8px;  margin: 12px 0;}.price {  font-size: 22px;  font-weight: bold;  color: #ff4757;}.original-price {  font-size: 14px;  color: #999;  text-decoration: line-through;}.discount {  background: #fff200;  padding: 2px 6px;  border-radius: 4px;  font-size: 12px;}.actions {  display: flex;  gap: 8px;  margin: 16px 0 12px;}.cart-btn {  flex: 1;  background: #5352ed;  color: white;  border: none;  padding: 10px;  border-radius: 6px;  font-weight: bold;  cursor: pointer;  transition: background 0.2s;}.cart-btn:hover {  background: #3742fa;}.cart-btn.disabled {  background: #a4b0be;  cursor: not-allowed;}.cart-btn.success {  background: #2ed573;}.fav-btn {  width: 42px;  background: white;  border: 1px solid #ddd;  border-radius: 6px;  font-size: 18px;  cursor: pointer;  transition: all 0.2s;}.fav-btn:hover {  border-color: #ff6b6b;  color: #ff6b6b;}.meta {  display: flex;  gap: 15px;  font-size: 13px;  color: #2ed573;  margin-top: 8px;}</style>
```

[预览 HTML 代码块](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-view-html)

支持预览 HTML 代码块。

- 如果你不需要，可以通过 `need-view-code-btn` 属性，设置 `false` 来隐藏按钮。默认为 `true` 。
- 你还可以使用 `secure-view-code` 属性，设置 `true` 来开启 `html` 安全模式。默认为 `false` 。如果开启，则不会渲染 `script` 标签。点击加入购物车
- 你还可以通过 `viewCodeModalOptions` 属性对弹框进行配置。

| 属性 | 值 | 说明 |
| --- | --- | --- |
| mode | 'drawer' | 模态框展示形式为抽屉式 |
| customClass | '' | 未添加自定义样式类 |
| dialogOptions | \- | 对话框模式配置（当前未启用） |
| \- closeOnClickModal | true | 点击对话框外部区域可关闭（仅dialog模式生效） |
| \- closeOnPressEscape | true | 按ESC键可关闭对话框（仅dialog模式生效） |
| drawerOptions | \- | 抽屉模式配置（当前启用） |
| \- closeOnClickModal | true | 点击抽屉外部区域可关闭 |
| \- closeOnPressEscape | true | 按ESC键可关闭抽屉 |

📌 Warning

同时也可以通过自定义顶部代码块，控制顶部预览按钮的样式。

或者，完全走自定义渲染，详情请往下查看 **`自定义代码块顶部渲染`** 。

### 自定义代码块渲染

```javascript
const a = 1;
```
```javascript
这是我自己定义的 echarts 组件
```

[codeXRender 代码块自定义渲染](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-code-x-render)

使用 `codeXRender` 属性，自定义代码块的渲染。这个属性接受一个对象，对象中的 key 为代码块的语言，value 为一个函数，函数的参数为代码块的属性，返回值为一个 VNode。意味着你可以用 Vue 的模板语法来渲染代码块。

📌 Warning

这个功能会拦截你设置的代码块，你可以和后端商量好码块的语言，然后根据语言返回一个对应的 VNode。

后续我们会打造一个基于这个组件的组件库广场，如果你对此感兴趣，欢迎加入🥰 [交流群](https://element-plus-x.com/en/introduce.html#%F0%9F%91%A5-%E7%A4%BE%E5%8C%BA%E6%94%AF%E6%8C%81) ，或者添加作者联系方式，一同打造这个广场项目。🥳敬请期待

实例代码中引入的 echarts 组件。源码放在这里方便大家理解。如何自定义组件，这里 echarts 组件实现仅供示例。实际使用中，请请更据自己的后端数据和需求进行封装。

💝查看 `echarts` 组件 代码示例
```
vue<!-- echarts.vue -->

<script setup lang="ts">
import * as echarts from 'echarts';

// 保留原有props.code逻辑，同时添加可选配置
const props = defineProps<{
  code: string; // 原始JSON字符串配置
  width?: string; // 可选：图表宽度
  height?: string; // 可选：图表高度
  theme?: string; // 可选：图表主题
}>();

const refEle = ref<HTMLElement>();
let myChart: echarts.ECharts | null = null; // 图表实例引用

function parseEChartsOption(str: string): any {
  try {
    let cleanedStr = str.replace(/^option\s*=\s*/, '').replace(/;\s*$/, '');
    cleanedStr = cleanedStr.replace(/'/g, '"');
    cleanedStr = cleanedStr.replace(/(\w+)\s*:/g, '"$1":');
    return JSON.parse(cleanedStr);
  } catch (error) {
    console.error('Failed to parse ECharts option:', error);
    return null;
  }
}

// 核心渲染逻辑（保留原始解析流程）
function renderChart() {
  if (!refEle.value) return;

  try {
    // 解析JSON配置（保留原有逻辑）
    const cleanedStr = parseEChartsOption(props.code);

    // 初始化/更新图表
    if (!myChart) {
      myChart = echarts.init(refEle.value, props.theme);
    }
    myChart.setOption(cleanedStr);
  } catch (error) {
    console.error('图表配置解析失败:', error);
  }
}

// 窗口resize处理
function handleResize() {
  myChart?.resize();
}

// 销毁逻辑
function destroyChart() {
  if (myChart) {
    myChart.dispose(); // 释放ECharts实例
    myChart = null;
  }
  window.removeEventListener('resize', handleResize);
}

// 初始化渲染
onMounted(() => {
  renderChart();
  window.addEventListener('resize', handleResize); // 添加resize监听
});

// 监听code变化自动更新（关键优化）
watch(
  () => props.code,
  () => {
    renderChart(); // 配置变化时重新渲染
  }
);

// 卸载时清理资源
onUnmounted(() => {
  destroyChart();
});
</script>

<template>
  <div class="echarts-wrap">
    <span class="echarts-titlt">这是我自己定义的 echarts 组件</span>
    <div
      ref="refEle"
      :style="{
        height: height || '400px', // 可选高度，默认400px
        width: width || '100%' // 可选宽度，默认100%
      }"
    />
  </div>
</template>

<style scoped lang="less">
.echarts-wrap {
  position: relative;

  .echarts-titlt {
    position: absolute;
    width: fit-content;
    margin-left: 20px;
    color: blue;
    font-size: 20px;
    font-weight: bold;
  }
}
</style>
```

### 自定义代码块顶部渲染

如果你仅仅想修改我们内置的代码块顶部的内容，你可以使用 `codeXSlot` 。并且我们暴露出来了内置的 `折叠` 、 `主题切换` 、 `复制` 方法。你可以在仅改变样式的同时，保留默认功能。

```javascript
这是自定义头部，点击切换折叠状态const a = 1;
```

```javascript
自定义代码块左侧语言标识符const a = 1;
```

```javascript
javascript自定义代码块右侧控制按钮const a = 1;
```

```javascript
🎨Custom Mermaid📊 图表35%15%15%12%10%8%5%传媒及文化相关游戏开发其他影视动画与特效互联网产品设计广告与市场营销VR/AR开发
```

[codeXSlot 代码块顶部插槽自定义渲染](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-code-x-slot)

使用 `codeXSlot` 属性，自定义代码块顶部插槽的渲染。这个属性接受一个对象，对象中的 key 为 CodeBlockHeaderExpose 这个类型的固定的属性，value 为一个函数，函数的参数为代码块的属性，返回值为一个 VNode，意味着你可以用 Vue 的模板语法来渲染代码块的顶部。

你可以在自定义的模版中获取到 props, 并且 props 中有以下属性 （具体属性可以在项目中自行打印查看）：

- `isExpand`: props.isExpand 是否展开代码块。
- `toggleExpand`: props.toggleExpand 展开代码块。
- `isDark`: props.isDark.value 获取当前代码块主题。
- `toggleTheme`: props.toggleTheme 切换代码块主题。
- `renderLines`: props.renderLines 获取这个代码块的内容，你可以用它来传给复制函数。
- `copyCode`: props.copyCode(props.renderLines) 复制代码块(需要传参)。
- `viewCode`: props.viewCode(props.renderLines) 触发内置预览 HTML 代码块弹框(需要传参)。
- `value`: props.value 获取这个代码块类型是 '代码' | '预览'。
- `changeSelectValue`: props.changeSelectValue('代码' | '预览') 切换代码块类型(需要传参)。
- `changeSelectValue`: props.changeSelectValue('代码' | '预览') 切换代码块类型(需要传参)。
- `content`: props.content 获取这个代码块内容。
- `close`: props.close() 关闭内置预览 HTML 弹框(不需要传参)。

以下是 mermaid 的代码块头部自定义组件 props 中有可以获取的内置属性：

- `zoomIn`: props.zoomIn 放大。
- `zoomOut`: props.zoomOut 缩小。
- `reset`: props.reset 回到初始位置。
- `toggleCode`: props.toggleCode 切换显示代码。
- `download`: props.download 下载图片。
- `fullscreen`: props.fullscreen 进入全屏。
- `copyCode`: props.copyCode 复制代码。

### 自定义属性

<a href="https://element-plus-x.com/">element-plus-x</a>

<h1>标题1</h1> <h2>标题2</h2>

<self-btn>给自定义标签添加 el-button 类名</self-btn>

[customAttrs 自定义属性](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-custom-attrs)

使用 `customAttrs` 属性，接收一个对象，对象中的属性为标签名，值为标签的属性。匹配一个标签，就会给该标签添加相应的属性。

### mermaid 操作栏配置

```
🎨Custom Mermaid📊 图表35%15%15%12%10%8%5%传媒及文化相关游戏开发其他影视动画与特效互联网产品设计广告与市场营销VR/AR开发
```

```
35%15%15%12%10%8%5%传媒及文化相关游戏开发其他影视动画与特效互联网产品设计广告与市场营销VR/AR开发
```

[mermaidConfig mermaid 配置](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-mermaid-config)

使用 `mermaidConfig` 属性，自定义mermaid 顶部的 ToolbarConfig 。这个属性接受一个MermaidToolbarConfig 对象, 可以控制顶部控件的隐藏展示，一些类名的添加，还有悬停颜色的控制。

### 插槽 标签拦截

<img src="https://avatars.githubusercontent.com/u/76239030?v=4" alt="">

<self-btn>自定义标签</self-btn>

[插槽](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-slot)

你可以拦截一些标签，也可以是自定义的标签，然后自定义去渲染这些标签。如果是想自定义渲染图片或者视频，说不定会很方便

### 内置的代码块语言

```js
jsconsole.log('hello world');
```
```ts
tsimport 'self-markdown.css'
```

[内置一些代码块语言的匹配](https://element-plus-x.com/zh/components/xmarkdown/#zh-components-xmarkdown-demos-lang)

我们内置了一些常用的编程、开发语言的匹配，用于渲染对应的代码块内容。

📌 Warning

其中一些语言我们可以去匹配他的简写，比如 `javascript` 可以使用 `js` 去匹配

💝 查看所有语言的支持

| 语言名称 | 语言匹配ID | 语言匹配简写 |
| --- | --- | --- |
| ABAP | abap |  |
| ActionScript | actionscript-3 |  |
| Ada | ada |  |
| Angular HTML | angular-html |  |
| Angular TypeScript | angular-ts |  |
| Apache Conf | apache |  |
| Apex | apex |  |
| APL | apl |  |
| AppleScript | applescript |  |
| Ara | ara |  |
| AsciiDoc | asciidoc | adoc |
| Assembly | asm |  |
| Astro | astro |  |
| AWK | awk |  |
| Ballerina | ballerina |  |
| Batch File | bat | batch |
| Beancount | beancount |  |
| Berry | berry | be |
| BibTeX | bibtex |  |
| Bicep | bicep |  |
| Blade | blade |  |
| 1C (Enterprise) | bsl | 1c |
| C | c |  |
| Cadence | cadence | cdc |
| Cairo | cairo |  |
| Clarity | clarity |  |
| Clojure | clojure | clj |
| CMake | cmake |  |
| COBOL | cobol |  |
| CODEOWNERS | codeowners |  |
| CodeQL | codeql | ql |
| CoffeeScript | coffee | coffeescript |
| Common Lisp | common-lisp | lisp |
| Coq | coq |  |
| C++ | cpp | c++ |
| Crystal | crystal |  |
| C# | csharp | c#cs |
| CSS | css |  |
| CSV | csv |  |
| CUE | cue |  |
| Cypher | cypher | cql |
| D | d |  |
| Dart | dart |  |
| DAX | dax |  |
| Desktop | desktop |  |
| Diff | diff |  |
| Dockerfile | docker | dockerfile |
| dotEnv | dotenv |  |
| Dream Maker | dream-maker |  |
| Edge | edge |  |
| Elixir | elixir |  |
| Elm | elm |  |
| Emacs Lisp | emacs-lisp | elisp |
| ERB | erb |  |
| Erlang | erlang | erl |
| Fennel | fennel |  |
| Fish | fish |  |
| Fluent | fluent | ftl |
| Fortran (Fixed Form) | fortran-fixed-form | fforf77 |
| Fortran (Free Form) | fortran-free-form | f90f95f03f08f18 |
| F# | fsharp | f#fs |
| GDResource | gdresource |  |
| GDScript | gdscript |  |
| GDShader | gdshader |  |
| Genie | genie |  |
| Gherkin | gherkin |  |
| Git Commit Message | git-commit |  |
| Git Rebase Message | git-rebase |  |
| Gleam | gleam |  |
| Glimmer JS | glimmer-js | gjs |
| Glimmer TS | glimmer-ts | gts |
| GLSL | glsl |  |
| Gnuplot | gnuplot |  |
| Go | go |  |
| GraphQL | graphql | gql |
| Groovy | groovy |  |
| Hack | hack |  |
| Ruby Haml | haml |  |
| Handlebars | handlebars | hbs |
| Haskell | haskell | hs |
| Haxe | haxe |  |
| HashiCorp HCL | hcl |  |
| Hjson | hjson |  |
| HLSL | hlsl |  |
| HTML | html |  |
| HTML (Derivative) | html-derivative |  |
| HTTP | http |  |
| HXML | hxml |  |
| Hy | hy |  |
| Imba | imba |  |
| INI | ini | properties |
| Java | java |  |
| JavaScript | javascript | js |
| Jinja | jinja |  |
| Jison | jison |  |
| JSON | json |  |
| JSON5 | json5 |  |
| JSON with Comments | jsonc |  |
| JSON Lines | jsonl |  |
| Jsonnet | jsonnet |  |
| JSSM | jssm | fsl |
| JSX | jsx |  |
| Julia | julia | jl |
| Kotlin | kotlin | ktkts |
| Kusto | kusto | kql |
| LaTeX | latex |  |
| Lean 4 | lean | lean4 |
| Less | less |  |
| Liquid | liquid |  |
| LLVM IR | llvm |  |
| Log file | log |  |
| Logo | logo |  |
| Lua | lua |  |
| Luau | luau |  |
| Makefile | make | makefile |
| Markdown | markdown | md |
| Marko | marko |  |
| MATLAB | matlab |  |
| MDC | mdc |  |
| MDX | mdx |  |
| Mermaid | mermaid | mmd |
| MIPS Assembly | mipsasm | mips |
| Mojo | mojo |  |
| Move | move |  |
| Narrat Language | narrat | nar |
| Nextflow | nextflow | nf |
| Nginx | nginx |  |
| Nim | nim |  |
| Nix | nix |  |
| nushell | nushell | nu |
| Objective-C | objective-c | objc |
| Objective-C++ | objective-cpp |  |
| OCaml | ocaml |  |
| Pascal | pascal |  |
| Perl | perl |  |
| PHP | php |  |
| PL/SQL | plsql |  |
| Gettext PO | po | potpotx |
| Polar | polar |  |
| PostCSS | postcss |  |
| PowerQuery | powerquery |  |
| PowerShell | powershell | psps1 |
| Prisma | prisma |  |
| Prolog | prolog |  |
| Protocol Buffer 3 | proto | protobuf |
| Pug | pug | jade |
| Puppet | puppet |  |
| PureScript | purescript |  |
| Python | python | py |
| QML | qml |  |
| QML Directory | qmldir |  |
| Qt Style Sheets | qss |  |
| R | r |  |
| Racket | racket |  |
| Raku | raku | perl6 |
| ASP.NET Razor | razor |  |
| Windows Registry Script | reg |  |
| RegExp | regexp | regex |
| Rel | rel |  |
| RISC-V | riscv |  |
| reStructuredText | rst |  |
| Ruby | ruby | rb |
| Rust | rust | rs |
| SAS | sas |  |
| Sass | sass |  |
| Scala | scala |  |
| Scheme | scheme |  |
| SCSS | scss |  |
| 1C (Query) | sdbl | 1c-query |
| ShaderLab | shaderlab | shader |
| Shell | shellscript | bashshshellzsh |
| Shell Session | shellsession | console |
| Smalltalk | smalltalk |  |
| Solidity | solidity |  |
| Closure Templates | soy | closure-templates |
| SPARQL | sparql |  |
| Splunk Query Language | splunk | spl |
| SQL | sql |  |
| SSH Config | ssh-config |  |
| Stata | stata |  |
| Stylus | stylus | styl |
| Svelte | svelte |  |
| Swift | swift |  |
| SystemVerilog | system-verilog |  |
| Systemd Units | systemd |  |
| TalonScript | talonscript | talon |
| Tasl | tasl |  |
| Tcl | tcl |  |
| Templ | templ |  |
| Terraform | terraform | tftfvars |
| TeX | tex |  |
| TOML | toml |  |
| TypeScript with Tags | ts-tags | lit |
| TSV | tsv |  |
| TSX | tsx |  |
| Turtle | turtle |  |
| Twig | twig |  |
| TypeScript | typescript | ts |
| TypeSpec | typespec | tsp |
| Typst | typst | typ |
| V | v |  |
| Vala | vala |  |
| Visual Basic | vb | cmd |
| Verilog | verilog |  |
| VHDL | vhdl |  |
| Vim Script | viml | vimvimscript |
| Vue | vue |  |
| Vue HTML | vue-html |  |
| Vyper | vyper | vy |
| WebAssembly | wasm |  |
| Wenyan | wenyan | 文言 |
| WGSL | wgsl |  |
| Wikitext | wikitext | mediawikiwiki |
| WebAssembly Interface Types | wit |  |
| Wolfram | wolfram | wl |
| XML | xml |  |
| XSL | xsl |  |
| YAML | yaml | yml |
| ZenScript | zenscript |  |
| Zig | zig |  |

## 属性

| 属性名 | 类型 | 是否必填 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `markdown` | string | 是 | '' | markdown 内容 |
| `allowHtml` | bool | 否 | `false` | 是否渲染 html |
| `enableLatex` | bool | 否 | `true` | 是否渲染 latex |
| `enableBreaks` | bool | 否 | `true` | 是否渲染 breaks |
| `codeXRender` | Object | 否 | `()=>{}` | 自定义代码块渲染 |
| `codeXSlot` | Object | 否 | `()=>{}` | 自定义代码块顶部插槽渲染 |
| `customAttrs` | Object | 否 | `()=>{}` | 自定义属性 |
| `mermaidConfig` | Object | 否 | `()=>{}` | mermaid 配置 |

## 功能特性

- 支持增量渲染，极致的性能
- 支持自定义插槽，可以是 h 函数的组件，也可以是 template 模版组件。上手更简单
- 内置丰富的基础样式数学公式，mermaid图表，减少开发者负担
- 支持多种拦截，和自定义渲染，上限拉满