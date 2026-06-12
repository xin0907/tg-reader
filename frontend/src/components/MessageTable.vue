<script setup lang="ts">
import { computed } from 'vue'
import { Check, Link, RefreshLeft } from '@element-plus/icons-vue'
import type { Channel, Item } from '@/types'

const IMAGE_BASE = import.meta.env.VITE_IMAGE_BASE ?? 'http://localhost:8000'

const props = defineProps<{
  data: Item[]
  loading?: boolean
  total: number
  page: number
  page_size: number
  channels: Channel[]
  show_channel?: boolean
}>()

const emit = defineEmits<{
  'update:page': [page: number]
  'update:page_size': [page_size: number]
  toggleRead: [item: Item]
}>()

const PAGE_SIZES = [10, 20, 50, 100]

const channel_map = computed(() => new Map(props.channels.map((channel) => [channel.id, channel])))

const headerCellStyle = {
  background: 'var(--el-fill-color-light)',
  color: 'var(--el-text-color-primary)',
  fontWeight: 600,
  fontSize: '13px',
}

function toImageUrl(path: string): string {
  if (/^https?:\/\//.test(path)) {
    return path
  }
  return `${IMAGE_BASE}${path}`
}

function formatTime(date: string): string {
  const d = new Date(date)
  return Number.isNaN(d.getTime()) ? date : d.toLocaleString()
}

function toPreviewText(content: string): string {
  return content
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .trim()
}

function channelLabel(channel_id: number): string {
  const channel = channel_map.value.get(channel_id)
  if (!channel) {
    return '未知频道'
  }
  return channel.username ? `${channel.name} (@${channel.username})` : channel.name
}

function onPageChange(nextPage: number) {
  emit('update:page', nextPage)
}

function onPageSizeChange(nextSize: number) {
  emit('update:page_size', nextSize)
}

function openTelegramLink(link?: string | null) {
  if (!link) {
    return
  }
  window.open(link, '_blank', 'noopener,noreferrer')
}
</script>

<template>
  <div class="message-table">
    <el-table
      v-loading="props.loading"
      :data="props.data"
      stripe
      border
      :header-cell-style="headerCellStyle"
      empty-text="暂无数据"
    >
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_read ? 'info' : 'danger'" size="small" effect="dark">
            {{ row.is_read ? '已读' : '未读' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column v-if="props.show_channel" label="频道" width="190">
        <template #default="{ row }">
          <span class="channel-cell">{{ channelLabel(row.channel_id) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="内容" min-width="320">
        <template #default="{ row }">
          <el-popover placement="right-start" :width="420" trigger="hover" :show-after="400">
            <template #default>
              <div class="content-preview" v-html="row.content" />
            </template>
            <template #reference>
              <span class="content-cell">{{ toPreviewText(row.content) }}</span>
            </template>
          </el-popover>
        </template>
      </el-table-column>

      <el-table-column label="图片" width="140" align="center">
        <template #default="{ row }">
          <div v-if="row.images.length" class="image-thumbs">
            <el-image
              v-for="(img, idx) in row.images.slice(0, 3)"
              :key="`${row.channel_id}-${row.message_id}-${idx}`"
              :src="toImageUrl(img)"
              fit="cover"
              class="thumb-img"
              preview-teleported
              :preview-src-list="row.images.map(toImageUrl)"
            />
            <span v-if="row.images.length > 3" class="more-badge">+{{ row.images.length - 3 }}</span>
          </div>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>

      <el-table-column label="发送时间" width="170">
        <template #default="{ row }">
          <span class="time-cell">{{ formatTime(row.sent_at) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="统计" width="160">
        <template #default="{ row }">
          <span class="stats-cell">
            阅 {{ row.stats.views }} / 转 {{ row.stats.forwards }} / 评 {{ row.stats.replies }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="类型" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.media_type" size="small">{{ row.media_type }}</el-tag>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>

      <el-table-column prop="message_id" label="消息 ID" width="100" align="center" />

      <el-table-column label="操作" width="108" fixed="right" align="center">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-tooltip :content="row.is_read ? '标记未读' : '标记已读'" placement="top">
              <el-button
                class="action-button"
                :type="row.is_read ? 'info' : 'primary'"
                size="small"
                plain
                :aria-label="row.is_read ? '标记未读' : '标记已读'"
                @click="emit('toggleRead', row)"
              >
                <el-icon>
                  <RefreshLeft v-if="row.is_read" />
                  <Check v-else />
                </el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="打开 Telegram" placement="top">
              <el-button
                class="action-button"
                type="primary"
                size="small"
                plain
                :disabled="!row.link"
                aria-label="打开 Telegram"
                @click="openTelegramLink(row.link)"
              >
                <el-icon>
                  <Link />
                </el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div class="table-footer">
      <span class="total-info">共 {{ props.total }} 条</span>
      <el-pagination
        background
        layout="sizes, prev, pager, next, jumper"
        :total="props.total"
        :current-page="props.page"
        :page-size="props.page_size"
        :page-sizes="PAGE_SIZES"
        @update:current-page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </div>
  </div>
</template>

<style scoped>
.message-table {
  width: 100%;
  overflow-x: auto;
}

.content-preview {
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.6;
}

.content-cell {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  cursor: default;
}

.channel-cell {
  display: block;
  overflow: hidden;
  color: var(--el-text-color-regular);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-thumbs {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.thumb-img {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  cursor: zoom-in;
}

.more-badge {
  font-size: 11px;
  color: var(--el-color-primary);
  white-space: nowrap;
}

.time-cell {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.stats-cell {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.text-muted {
  color: var(--el-text-color-placeholder);
}

.action-buttons {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 72px;
}

.action-button {
  width: 28px;
  height: 28px;
  padding: 0;
}

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--el-fill-color-lighter);
  border-top: 1px solid var(--el-border-color-lighter);
}

.total-info {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
