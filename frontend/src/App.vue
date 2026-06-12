<script setup lang="ts">
import { ref } from 'vue'
import { Moon, Sunny } from '@element-plus/icons-vue'
import HomeView from '@/views/HomeView.vue'
import { THEME_STORAGE_KEY } from '@/constants'

const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem(THEME_STORAGE_KEY, isDark.value ? 'dark' : 'light')
}
</script>

<template>
  <div class="app-layout">
    <header class="app-header">
      <h1 class="app-title">TG-Pulse 消息管理</h1>
      <el-tooltip :content="isDark ? '切换为浅色' : '切换为深色'" placement="bottom">
        <el-button circle @click="toggleTheme">
          <el-icon>
            <Sunny v-if="isDark" />
            <Moon v-else />
          </el-icon>
        </el-button>
      </el-tooltip>
    </header>
    <main class="app-main">
      <HomeView />
    </main>
  </div>
</template>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  width: 100%;
  min-height: 100%;
}

body {
  overflow-x: clip;
  background: var(--el-bg-color-page);
}

#app {
  min-height: 100vh;
}

.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: clip;
}

.app-header {
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 56px;
  padding: 0 24px;
  background: linear-gradient(135deg, #1e3a5f 0%, #2d6aa0 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.app-title {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 1px;
  white-space: nowrap;
}

.app-main {
  flex: 1;
  padding: 16px 24px 0;
  max-width: none;
  width: 100%;
  overflow-x: clip;
}
</style>
