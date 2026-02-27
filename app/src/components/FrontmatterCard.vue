<template>
  <div class="frontmatter-card" v-if="hasData">
    <h1 v-if="data.title" class="frontmatter-title">{{ data.title }}</h1>

    <div v-if="hasMeta" class="frontmatter-meta">
      <span v-if="data.date" class="meta-item">
        <el-icon><Calendar /></el-icon>
        {{ formatDate(data.date) }}
      </span>
      <span v-if="data.author" class="meta-item">
        <el-icon><User /></el-icon>
        {{ data.author }}
      </span>
    </div>

    <div v-if="hasTags" class="frontmatter-tags">
      <el-tag v-for="tag in tags" :key="tag" class="tag-item" size="small">
        {{ tag }}
      </el-tag>
    </div>

    <p v-if="data.description" class="frontmatter-description">
      {{ data.description }}
    </p>

    <dl v-if="hasExtraFields" class="frontmatter-extra">
      <template v-for="(value, key) in extraFields" :key="key">
        <dt class="extra-key">{{ key }}</dt>
        <dd class="extra-value">{{ formatValue(value) }}</dd>
      </template>
    </dl>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Calendar, User } from '@element-plus/icons-vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
})

const COMMON_FIELDS = ['title', 'date', 'author', 'tags', 'description']

const hasData = computed(() => Object.keys(props.data).length > 0)

const hasMeta = computed(() => props.data.date || props.data.author)

const hasTags = computed(
  () => props.data.tags && Array.isArray(props.data.tags) && props.data.tags.length > 0,
)

const tags = computed(() => {
  if (!props.data.tags) return []
  if (Array.isArray(props.data.tags)) return props.data.tags
  return [props.data.tags]
})

const extraFields = computed(() => {
  const result = {}
  for (const key of Object.keys(props.data)) {
    if (!COMMON_FIELDS.includes(key)) {
      result[key] = props.data[key]
    }
  }
  return result
})

const hasExtraFields = computed(() => Object.keys(extraFields.value).length > 0)

function formatDate(date) {
  if (!date) return ''
  const d = new Date(date)
  if (isNaN(d.getTime())) return String(date)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function formatValue(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
</script>

<style scoped>
.frontmatter-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid #e0e6ed;
}

.frontmatter-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1d2939;
  margin: 0 0 16px 0;
  line-height: 1.3;
}

.frontmatter-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #667085;
  font-size: 0.9rem;
}

.frontmatter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tag-item {
  background: #eef2ff;
  color: #4f46e5;
  border: none;
}

.frontmatter-description {
  color: #475467;
  font-size: 1rem;
  line-height: 1.6;
  margin: 0 0 16px 0;
}

.frontmatter-extra {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 16px;
  margin: 0;
  padding-top: 16px;
  border-top: 1px solid #d0d5dd;
}

.extra-key {
  font-weight: 600;
  color: #344054;
  margin: 0;
  font-size: 0.9rem;
}

.extra-value {
  color: #475467;
  margin: 0;
  font-size: 0.9rem;
  word-break: break-word;
}
</style>
