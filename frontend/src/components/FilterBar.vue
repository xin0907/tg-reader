<script setup lang="ts">
import { onBeforeUnmount, reactive, watch } from 'vue'
import type { SyncMode } from '@/types'

interface FilterForm {
  keyword: string
  unreadOnly: boolean
  page_size: number
  sync_mode: SyncMode
}

const props = defineProps<{
  selected_channel_id?: number
  syncing?: boolean
}>()

const emit = defineEmits<{
  search: [payload: { keyword?: string; unreadOnly: boolean; page_size: number }]
  sync: [payload: { mode: SyncMode; channel_id?: number }]
}>()

const form = reactive<FilterForm>({
  keyword: '',
  unreadOnly: true,
  page_size: 20,
  sync_mode: 'limit',
})
let searchTimer: number | undefined

function emitSearch() {
  emit('search', {
    keyword: form.keyword.trim() || undefined,
    unreadOnly: form.unreadOnly,
    page_size: form.page_size,
  })
}

function queueSearch() {
  if (searchTimer) {
    window.clearTimeout(searchTimer)
  }
  searchTimer = window.setTimeout(() => {
    emitSearch()
    searchTimer = undefined
  }, 300)
}

function onSync() {
  emit('sync', { mode: form.sync_mode, channel_id: props.selected_channel_id })
}

watch(
  () => [form.keyword, form.unreadOnly, form.page_size],
  () => queueSearch(),
)

onBeforeUnmount(() => {
  if (searchTimer) {
    window.clearTimeout(searchTimer)
  }
})
</script>

<template>
  <div class="filter-bar">
    <div class="filter-controls">
      <div class="filter-item">
        <span class="filter-label">关键词</span>
        <el-input v-model="form.keyword" clearable placeholder="搜索消息内容" class="inp-keyword" />
      </div>

      <div class="filter-item">
        <span class="filter-label">仅未读</span>
        <el-switch v-model="form.unreadOnly" />
      </div>

      <div class="filter-item">
        <span class="filter-label">每页条数</span>
        <el-select v-model="form.page_size" class="sel-page-size">
          <el-option :value="10" label="10" />
          <el-option :value="20" label="20" />
          <el-option :value="50" label="50" />
          <el-option :value="100" label="100" />
        </el-select>
      </div>
    </div>

    <div class="sync-controls">
      <el-select v-model="form.sync_mode" class="sel-sync-mode">
        <el-option value="limit" label="限量同步" />
        <el-option value="all" label="全量同步" />
      </el-select>
      <el-button type="primary" :loading="props.syncing" :disabled="props.syncing" @click="onSync">
        同步
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  white-space: nowrap;
}

.sync-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inp-keyword {
  width: 260px;
}

.sel-page-size {
  width: 100px;
}

.sel-sync-mode {
  width: 120px;
}
</style>
