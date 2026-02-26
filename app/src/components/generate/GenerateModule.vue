<script setup>
</script>

<template>
  <div class="placeholder-module">
    <el-empty description="生成模块开发中...">
      <template #image>
        <el-icon :size="60"><MagicStick /></el-icon>
      </template>
    </el-empty>
  </div>
</template>

<script>
import { MagicStick } from '@element-plus/icons-vue'
export default {
  components: { MagicStick }
}
</script>

<style scoped>
.placeholder-module {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
