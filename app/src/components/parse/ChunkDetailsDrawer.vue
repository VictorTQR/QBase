<script setup>
import { computed } from 'vue'
import { useVectorStore } from '@/stores/vector'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  file: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:visible', 'close'])

const vectorStore = useVectorStore()

function handleClose() {
  emit('update:visible', false)
  emit('close')
}

const indexedFileInfo = computed(() => {
  if (!props.file) return null
  return vectorStore.indexedFilesList?.find((f) => f.file_path === props.file.file_path)
})

const chunks = computed(() => {
  // TODO: 未来需要从后端 API 获取真实分块数据
  return [
    { id: 1, preview: '第一章 引言 深度学习是机器学习的一个分支...', tokens: 384, status: 'done' },
    { id: 2, preview: '1.1 什么是神经网络 人工神经网络是受生物...', tokens: 412, status: 'done' },
    { id: 3, preview: '1.2 历史背景 深度学习的历史可以追溯到...', tokens: 356, status: 'running' },
    {
      id: 4,
      preview: '1.3 应用场景 深度学习在计算机视觉、自然...',
      tokens: 298,
      status: 'pending',
    },
    {
      id: 5,
      preview: '第二章 神经网络基础 本章介绍神经网络的基...',
      tokens: 421,
      status: 'pending',
    },
  ]
})

function getFileIconClass(file) {
  if (!file) return ''
  if (file.parser_type === 'audio') return 'audio'
  if (file.file_name?.endsWith('.md')) return 'md'
  return 'pdf'
}

function getFileIcon(file) {
  if (!file) return '📄'
  if (file.parser_type === 'audio') return '🎵'
  if (file.file_name?.endsWith('.md')) return '📝'
  return '📄'
}

function getParseStageClass(file) {
  if (!file) return 'pending'
  if (file.state === 'done') return 'success'
  if (file.state === 'running') return 'running'
  if (file.state === 'failed') return 'failed'
  return 'pending'
}

function getParseStageIcon(file) {
  if (!file) return '○'
  if (file.state === 'done') return '✓'
  if (file.state === 'running') return '●'
  if (file.state === 'failed') return '✕'
  return '○'
}

function getParseStageTime(file) {
  if (!file) return '-'
  if (file.state === 'done' || file.state === 'failed') {
    return formatDate(file.updated_at)
  }
  if (file.state === 'running') return '进行中...'
  return '-'
}

function getIndexStageClass(file) {
  if (!file || file.state !== 'done') return 'pending'
  if (vectorStore.isFileIndexed(file.file_path)) return 'success'
  return 'pending'
}

function getIndexStageIcon(file) {
  if (!file || file.state !== 'done') return '○'
  if (vectorStore.isFileIndexed(file.file_path)) return '✓'
  return '○'
}

function getIndexStageTime(file) {
  if (!file || file.state !== 'done') return '-'
  if (vectorStore.isFileIndexed(file.file_path)) return '14:34:00'
  return '-'
}

function isFileIndexed(file) {
  if (!file) return false
  return vectorStore.isFileIndexed(file.file_path)
}

function formatDate(timestamp) {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="(v) => emit('update:visible', v)"
    size="520px"
    @close="handleClose"
  >
    <template #header>
      <div class="drawer-header">
        <div class="drawer-title">
          <div class="drawer-file-icon" :class="getFileIconClass(file)">
            {{ getFileIcon(file) }}
          </div>
          <div class="drawer-file-info">
            <div class="drawer-file-name">{{ file?.file_name }}</div>
            <div class="drawer-file-meta">
              <span>{{ file?.file_size || '-' }}</span>
              <span>·</span>
              <span>{{ indexedFileInfo?.chunk_count || '-' }} 分块</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div class="drawer-content" v-if="file">
      <div v-if="file.state === 'failed'" class="error-section">
        <div class="error-header">
          <svg
            class="error-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span class="error-title">处理失败</span>
        </div>
        <div class="error-message">{{ file.error_msg || '未知错误' }}</div>
        <div class="error-suggestion">建议：检查文件格式是否正确，或尝试重新上传。</div>
        <div class="error-actions">
          <el-button type="primary" size="small">查看日志</el-button>
          <el-button size="small">忽略</el-button>
        </div>
      </div>

      <div class="drawer-pipeline">
        <div class="drawer-pipeline-title">处理时间轴</div>
        <div class="drawer-stepper">
          <div class="drawer-step">
            <div class="drawer-step-icon success">✓</div>
            <span class="drawer-step-label">上传</span>
            <span class="drawer-step-time">14:30:00</span>
          </div>
          <div class="drawer-step-connector completed"></div>
          <div class="drawer-step">
            <div class="drawer-step-icon" :class="getParseStageClass(file)">
              {{ getParseStageIcon(file) }}
            </div>
            <span class="drawer-step-label">解析</span>
            <span class="drawer-step-time">{{ getParseStageTime(file) }}</span>
          </div>
          <div class="drawer-step-connector" :class="{ completed: file.state === 'done' }"></div>
          <div class="drawer-step">
            <div class="drawer-step-icon" :class="getIndexStageClass(file)">
              {{ getIndexStageIcon(file) }}
            </div>
            <span class="drawer-step-label">索引</span>
            <span class="drawer-step-time">{{ getIndexStageTime(file) }}</span>
          </div>
          <div class="drawer-step-connector" :class="{ completed: isFileIndexed(file) }"></div>
          <div class="drawer-step">
            <div class="drawer-step-icon" :class="isFileIndexed(file) ? 'success' : 'pending'">
              {{ isFileIndexed(file) ? '✓' : '○' }}
            </div>
            <span class="drawer-step-label">完成</span>
            <span class="drawer-step-time">{{ isFileIndexed(file) ? '14:35:00' : '-' }}</span>
          </div>
        </div>
      </div>

      <div class="info-section">
        <div class="section-title">文件信息</div>
        <div class="info-grid">
          <div class="info-row">
            <div class="info-label">路径</div>
            <div class="info-value">{{ file.file_path || '未知' }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">大小</div>
            <div class="info-value">{{ file?.file_size || '-' }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">页数</div>
            <div class="info-value">{{ file?.page_count || '-' }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">解析时间</div>
            <div class="info-value">{{ formatDate(file.created_at) }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">分块数</div>
            <div class="info-value">{{ indexedFileInfo?.chunk_count || '-' }}</div>
          </div>
          <div class="info-row">
            <div class="info-label">Token 数</div>
            <div class="info-value">-</div>
          </div>
        </div>
      </div>

      <div class="info-section">
        <div class="section-title">操作</div>
        <div class="drawer-actions">
          <el-button>重新处理</el-button>
          <el-button type="primary">仅重新索引</el-button>
          <el-button type="danger">删除</el-button>
        </div>
        <div class="action-hint">快捷键: R-重试 P-暂停 D-删除</div>
      </div>

      <div class="info-section">
        <div class="section-title">分块列表</div>
        <div class="chunk-table-container">
          <el-table :data="chunks" style="width: 100%">
            <el-table-column label="#" width="50" />
            <el-table-column label="内容预览" />
            <el-table-column label="Token" width="80" />
            <el-table-column label="状态" width="90" />
            <el-table-column label="操作" width="70" />
          </el-table>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<style scoped>
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-title {
  display: flex;
  align-items: center;
  gap: 14px;
}

.drawer-file-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  background: var(--el-fill-color-lighter);
}

.drawer-file-icon.pdf {
  background: #fef2f2;
  color: #dc2626;
}

.drawer-file-icon.md {
  background: #f0f9ff;
  color: #0284c7;
}

.drawer-file-icon.audio {
  background: #f0fdf4;
  color: #16a34a;
}

.drawer-file-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.drawer-file-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.drawer-file-meta {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: flex;
  gap: 12px;
}

.drawer-content {
  padding: 0 24px 24px;
}

.error-section {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.error-icon {
  width: 24px;
  height: 24px;
  color: #ef4444;
}

.error-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.error-message {
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  line-height: 1.6;
}

.error-suggestion {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.error-actions {
  display: flex;
  gap: 10px;
}

.drawer-pipeline {
  background: var(--el-fill-color-lighter);
  border-radius: 10px;
  padding: 18px;
  margin-bottom: 20px;
}

.drawer-pipeline-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 14px;
}

.drawer-stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.drawer-step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
}

.drawer-step-icon.pending {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-placeholder);
  border: 2px solid var(--el-border-color-lighter);
}

.drawer-step-icon.running {
  background: #4f46e5;
  color: white;
  animation: pulse 2s infinite;
}

.drawer-step-icon.success {
  background: #10b981;
  color: white;
}

.drawer-step-icon.failed {
  background: #ef4444;
  color: white;
}

.drawer-step-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.drawer-step-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.drawer-step-connector {
  width: 40px;
  height: 2px;
  background: var(--el-border-color-lighter);
  margin-bottom: 20px;
}

.drawer-step-connector.completed {
  background: #10b981;
}

.info-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.info-grid {
  background: var(--el-fill-color-lighter);
  border-radius: 10px;
  padding: 16px;
}

.info-row {
  display: flex;
  padding: 10px 0;
}

.info-row:not(:last-child) {
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.info-label {
  width: 90px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.info-value {
  flex: 1;
  font-size: 13px;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.drawer-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 8px;
}

.chunk-table-container {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  overflow: hidden;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.4);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 6px rgba(79, 70, 229, 0);
  }
}
</style>
