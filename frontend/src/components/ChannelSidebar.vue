<script setup lang="ts">
import { computed, ref } from 'vue'
import { Expand, Fold, Search } from '@element-plus/icons-vue'
import type { Channel } from '@/types'

const props = defineProps<{
  channels: Channel[]
  loading?: boolean
  selected_channel_id?: number
  collapsed?: boolean
}>()

const emit = defineEmits<{
  select: [channel_id?: number]
  'update:collapsed': [collapsed: boolean]
}>()

const keyword = ref('')

const filtered_channels = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  if (!text) {
    return props.channels
  }
  return props.channels.filter((channel) => {
    const name = channel.name.toLowerCase()
    const username = channel.username?.toLowerCase() || ''
    return name.includes(text) || username.includes(text) || String(channel.id).includes(text)
  })
})

function channelLabel(channel: Channel) {
  return channel.username ? `${channel.name} (@${channel.username})` : channel.name
}

function toggleCollapsed() {
  emit('update:collapsed', !props.collapsed)
}
</script>

<template>
  <aside class="channel-sidebar" :class="{ collapsed: props.collapsed }">
    <div class="sidebar-header">
      <template v-if="!props.collapsed">
        <el-input v-model="keyword" clearable placeholder="搜索频道" class="channel-search">
          <template #prefix>
            <el-icon>
              <Search />
            </el-icon>
          </template>
        </el-input>
      </template>
      <el-tooltip :content="props.collapsed ? '展开频道栏' : '收起频道栏'" placement="right">
        <el-button class="collapse-button" text @click="toggleCollapsed">
          <el-icon>
            <Expand v-if="props.collapsed" />
            <Fold v-else />
          </el-icon>
        </el-button>
      </el-tooltip>
    </div>

    <div v-if="props.collapsed" class="collapsed-body">
      <span class="collapsed-text">频道</span>
    </div>

    <div v-else v-loading="props.loading" class="channel-list">
      <button
        class="channel-item"
        :class="{ active: props.selected_channel_id === undefined }"
        type="button"
        @click="emit('select', undefined)"
      >
        <span class="channel-name">全部频道</span>
        <span class="channel-count">{{ props.channels.length }}</span>
      </button>

      <button
        v-for="channel in filtered_channels"
        :key="channel.id"
        class="channel-item"
        :class="{ active: props.selected_channel_id === channel.id }"
        type="button"
        @click="emit('select', channel.id)"
      >
        <span class="channel-name">{{ channelLabel(channel) }}</span>
      </button>

      <el-empty
        v-if="!props.loading && !filtered_channels.length"
        description="暂无频道"
        :image-size="56"
      />
    </div>
  </aside>
</template>

<style scoped>
.channel-sidebar {
  position: sticky;
  top: 72px;
  flex: 0 0 244px;
  width: 244px;
  height: calc(100vh - 88px);
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  transition:
    width 0.18s ease,
    flex-basis 0.18s ease;
}

.channel-sidebar.collapsed {
  flex-basis: 44px;
  width: 44px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 44px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}

.channel-search {
  flex: 1;
}

.channel-search :deep(.el-input__inner) {
  font-size: 13px;
}

.collapse-button {
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  padding: 0;
}

.channel-list {
  height: calc(100% - 44px);
  overflow-y: auto;
  padding: 6px;
  font-size: 13px;
}

.channel-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 28px;
  padding: 0 8px;
  border: 0;
  border-left: 3px solid transparent;
  border-radius: 3px;
  background: transparent;
  color: var(--el-text-color-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.channel-item:hover {
  background: var(--el-fill-color-light);
}

.channel-item.active {
  border-left-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.channel-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.channel-count {
  flex: 0 0 auto;
  margin-left: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.collapsed-body {
  display: flex;
  justify-content: center;
  height: calc(100% - 44px);
  padding-top: 12px;
}

.collapsed-text {
  writing-mode: vertical-rl;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  letter-spacing: 2px;
}
</style>
