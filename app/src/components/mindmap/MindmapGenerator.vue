<script setup>
import { ref } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { useDocumentStore } from '@/stores/document'

const agentStore = useAgentStore()
const documentStore = useDocumentStore()

const isGenerating = ref(false)
const error = ref(null)
const mindmapResult = ref(null)

async function generateMindmap() {
  if (!documentStore.currentFile || !documentStore.content) {
    error.value = '请先打开一个 Markdown 文档'
    return
  }

  isGenerating.value = true
  error.value = null
  mindmapResult.value = null

  try {
    const result = await agentStore.generateMindmap(documentStore.content)
    if (result.success) {
      mindmapResult.value = result.mindmap
    } else {
      error.value = result.error
    }
  } catch (err) {
    error.value = err.message
  } finally {
    isGenerating.value = false
  }
}

function getNodePosition(nodeId) {
  const positions = {
    root: { x: 400, y: 50 },
    node1: { x: 200, y: 150 },
    node2: { x: 600, y: 150 },
    node3: { x: 100, y: 250 },
    node4: { x: 300, y: 250 },
    node5: { x: 500, y: 250 },
    node6: { x: 700, y: 250 },
  }

  return positions[nodeId] || { x: 400, y: 350 }
}
</script>

<template>
  <div class="mindmap-generator">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>思维导图生成</span>
        </div>
      </template>

      <div class="content">
        <el-button
          type="primary"
          :loading="isGenerating"
          @click="generateMindmap"
          style="width: 100%"
        >
          {{ isGenerating ? '生成中...' : '生成思维导图' }}
        </el-button>

        <el-alert v-if="error" type="error" :closable="false" style="margin-top: 16px">
          {{ error }}
        </el-alert>

        <div v-if="mindmapResult" class="result-panel">
          <h3>{{ mindmapResult.title }}</h3>
          <div class="mindmap-container">
            <div class="mindmap-svg-container">
              <svg width="100%" height="100%" viewBox="0 0 800 600">
                <template v-for="node in mindmapResult.nodes" :key="node.id">
                  <g v-if="node.parent">
                    <line
                      :x1="getNodePosition(node.parent).x"
                      :y1="getNodePosition(node.parent).y"
                      :x2="getNodePosition(node.id).x"
                      :y2="getNodePosition(node.id).y"
                      stroke="#409eff"
                      stroke-width="2"
                    />
                  </g>
                </template>

                <template v-for="node in mindmapResult.nodes" :key="node.id">
                  <g>
                    <rect
                      :x="getNodePosition(node.id).x - 80"
                      :y="getNodePosition(node.id).y - 20"
                      width="160"
                      height="40"
                      :fill="node.parent ? '#f0f9eb' : '#e6f7ff'"
                      :stroke="node.parent ? '#67c23a' : '#409eff'"
                      stroke-width="2"
                      rx="4"
                    />
                    <text
                      :x="getNodePosition(node.id).x"
                      :y="getNodePosition(node.id).y + 5"
                      text-anchor="middle"
                      fill="#303133"
                      font-size="14"
                    >
                      {{ node.text }}
                    </text>
                  </g>
                </template>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.mindmap-generator {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-panel {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #f9f9f9;
}

.result-panel h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.mindmap-container {
  position: relative;
  height: 400px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fff;
  overflow: auto;
}

.mindmap-svg-container {
  width: 100%;
  height: 100%;
}

.mindmap-svg-container svg {
  width: 100%;
  height: 100%;
}
</style>
