<script setup>
</script>

<template>
  <div class="placeholder-module">
    <el-empty description="闪卡模块开发中...">
      <template #image>
        <el-icon :size="60"><Tickets /></el-icon>
      </template>
    </el-empty>
  </div>
</template>

<script>
import { Tickets } from '@element-plus/icons-vue'
export default {
  components: { Tickets }
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
