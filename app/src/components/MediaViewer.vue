<template>
  <div class="media-viewer">
    <div v-if="!base64Data" class="empty">
      <el-empty description="无媒体文件" />
    </div>
    <div v-else class="media-container">
      <audio
        v-if="mediaType === 'audio'"
        :src="mediaSrc"
        controls
        class="audio-player"
      />
      <video
        v-else-if="mediaType === 'video'"
        :src="mediaSrc"
        controls
        class="video-player"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  base64Data: {
    type: String,
    default: '',
  },
  mimeType: {
    type: String,
    default: 'application/octet-stream',
  },
  mediaType: {
    type: String,
    default: 'video',
    validator: (v) => ['audio', 'video'].includes(v),
  },
})

const mediaSrc = computed(() => {
  if (!props.base64Data) {
    return ''
  }
  return `data:${props.mimeType};base64,${props.base64Data}`
})
</script>

<style scoped>
.media-viewer {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-bg-color-page);
}

.empty {
  width: 100%;
}

.media-container {
  width: 100%;
  max-width: 900px;
  padding: 20px;
}

.audio-player {
  width: 100%;
}

.video-player {
  width: 100%;
  max-height: 600px;
  border-radius: 8px;
  background-color: #000;
}
</style>
