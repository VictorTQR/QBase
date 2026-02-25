<template>
  <div class="pdf-viewer">
    <div v-if="error" class="error">
      <el-icon><Warning /></el-icon>
      <span>{{ error }}</span>
    </div>
    <div v-else-if="isLoading" class="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div v-else class="pdf-container">
      <div class="toolbar">
        <el-button-group>
          <el-button size="small" :disabled="currentPage <= 1" @click="prevPage">
            <el-icon><DArrowLeft /></el-icon>
          </el-button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <el-button size="small" :disabled="currentPage >= totalPages" @click="nextPage">
            <el-icon><DArrowRight /></el-icon>
          </el-button>
        </el-button-group>
        <el-button-group style="margin-left: 16px">
          <el-button size="small" :disabled="scale <= 0.5" @click="zoomOut">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <span class="scale-info">{{ Math.round(scale * 100) }}%</span>
          <el-button size="small" :disabled="scale >= 3" @click="zoomIn">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
        </el-button-group>
      </div>
      <div class="canvas-wrapper" ref="canvasWrapper">
        <canvas ref="pdfCanvas" :style="{ transform: `scale(${scale})` }" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import {
  Warning, Loading, DArrowLeft, DArrowRight, ZoomIn, ZoomOut } from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker

const props = defineProps({
  base64Data: {
    type: String,
    default: '',
  },
})

const pdfCanvas = ref(null)
const canvasWrapper = ref(null)
const isLoading = ref(true)
const error = ref(null)
const pdfDoc = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1)
const currentRenderTask = ref(null)

async function loadPdf() {
  if (!props.base64Data) {
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const binaryData = atob(props.base64Data)
    const uint8Array = new Uint8Array(binaryData.length)
    for (let i = 0; i < binaryData.length; i++) {
      uint8Array[i] = binaryData.charCodeAt(i)
    }

    const loadingTask = pdfjsLib.getDocument({ data: uint8Array })
    pdfDoc.value = await loadingTask.promise
    totalPages.value = pdfDoc.value.numPages
    currentPage.value = 1
    await renderPage(currentPage.value)
  } catch (err) {
    error.value = `加载 PDF 失败：${err.message}`
  } finally {
    isLoading.value = false
  }
}

async function renderPage(pageNum) {
  if (!pdfDoc.value) {
    return
  }

  if (currentRenderTask.value) {
    currentRenderTask.value.cancel()
  }

  try {
    const page = await pdfDoc.value.getPage(pageNum)
    const canvas = pdfCanvas.value
    const context = canvas.getContext('2d')

    const viewport = page.getViewport({ scale: 1 })
    const containerWidth = canvasWrapper.value?.clientWidth || 800
    const desiredScale = containerWidth / viewport.width
    const scaledViewport = page.getViewport({ scale: desiredScale * scale.value })

    canvas.width = scaledViewport.width
    canvas.height = scaledViewport.height

    const renderContext = {
      canvasContext: context,
      viewport: scaledViewport,
    }

    currentRenderTask.value = page.render(renderContext)
    await currentRenderTask.value.promise
    currentRenderTask.value = null
  } catch (err) {
    console.error('渲染页面失败：', err)
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    renderPage(currentPage.value)
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    renderPage(currentPage.value)
  }
}

function zoomIn() {
  scale.value = Math.min(3, scale.value + 0.25)
  renderPage(currentPage.value)
}

function zoomOut() {
  scale.value = Math.max(0.5, scale.value - 0.25)
  renderPage(currentPage.value)
}

watch(() => props.base64Data, () => {
  if (props.base64Data) {
    loadPdf()
  }
}, { immediate: true })

onUnmounted(() => {
  if (currentRenderTask.value) {
    currentRenderTask.value.cancel()
  }
})
</script>

<style scoped>
.pdf-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #525659;
}

.error,
.loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--el-text-color-secondary);
}

.pdf-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background-color: #323639;
  border-bottom: 1px solid #424649;
}

.page-info,
.scale-info {
  padding: 0 12px;
  color: #fff;
  font-size: 13px;
  min-width: 60px;
  text-align: center;
}

.canvas-wrapper {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  padding: 20px;
}

.pdf-canvas {
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  transform-origin: top center;
}
</style>
