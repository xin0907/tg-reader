<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ChannelSidebar from '@/components/ChannelSidebar.vue'
import FilterBar from '@/components/FilterBar.vue'
import MessageTable from '@/components/MessageTable.vue'
import { fetchChannels, fetchMessages, patchMessageRead, syncTelegram, syncTelegramAll } from '@/services/api'
import type { Channel, Item, SyncMode } from '@/types'

const data = ref<Item[]>([])
const channels = ref<Channel[]>([])
const loading = ref(false)
const channels_loading = ref(false)
const sidebar_collapsed = ref(false)
const syncing = ref(false)
const total = ref(0)
const page = ref(1)
const page_size = ref(20)

const filters = reactive<{
  channel_id?: number
  keyword?: string
  unreadOnly: boolean
}>({
  channel_id: undefined,
  keyword: undefined,
  unreadOnly: true,
})

async function load() {
  loading.value = true
  try {
    const resp = await fetchMessages({
      page: page.value,
      page_size: page_size.value,
      channel_id: filters.channel_id,
      keyword: filters.keyword,
      is_read: filters.unreadOnly ? false : undefined,
    })
    data.value = resp.items
    total.value = resp.total
  } catch (error) {
    data.value = []
    total.value = 0
    ElMessage.error(error instanceof Error ? error.message : '消息查询失败')
  } finally {
    loading.value = false
  }
}

async function loadChannels() {
  channels_loading.value = true
  try {
    channels.value = await fetchChannels()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '频道加载失败')
  } finally {
    channels_loading.value = false
  }
}

async function onSelectChannel(channel_id?: number) {
  filters.channel_id = channel_id
  page.value = 1
  await load()
}

async function onSearch(payload: {
  keyword?: string
  unreadOnly: boolean
  page_size: number
}) {
  filters.keyword = payload.keyword
  filters.unreadOnly = payload.unreadOnly
  page_size.value = payload.page_size
  page.value = 1
  await load()
}

async function onToggleReadStatus(item: Item) {
  try {
    await patchMessageRead(
      [{ channel_id: item.channel_id, message_id: item.message_id }],
      !item.is_read,
    )
    ElMessage.success(item.is_read ? '已标记为未读' : '已标记为已读')
    await load()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '更新已读状态失败')
  }
}

async function onSyncTelegram(payload: { mode: SyncMode; channel_id?: number }) {
  if (!payload.channel_id) {
    ElMessage.warning('请先在左侧选择频道')
    return
  }

  filters.channel_id = payload.channel_id
  page.value = 1

  try {
    if (payload.mode === 'all') {
      await ElMessageBox.confirm(
        '全量同步会拉取该频道全部历史消息，耗时可能较长。确认继续吗？',
        '确认全量同步',
        {
          confirmButtonText: '继续同步',
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
    }

    syncing.value = true
    if (payload.mode === 'all') {
      await syncTelegramAll(payload.channel_id)
    } else {
      await syncTelegram(payload.channel_id)
    }
    ElMessage.success('同步完成')
    await Promise.all([load(), loadChannels()])
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error instanceof Error ? error.message : '同步失败')
    }
  } finally {
    syncing.value = false
  }
}

async function onPageChange(nextPage: number) {
  page.value = nextPage
  await load()
}

async function onPageSizeChange(nextSize: number) {
  page_size.value = nextSize
  page.value = 1
  await load()
}

onMounted(async () => {
  await Promise.all([load(), loadChannels()])
})
</script>

<template>
  <div class="home-layout">
    <ChannelSidebar
      :channels="channels"
      :loading="channels_loading"
      :selected_channel_id="filters.channel_id"
      :collapsed="sidebar_collapsed"
      @select="onSelectChannel"
      @update:collapsed="sidebar_collapsed = $event"
    />

    <section class="content-panel">
      <FilterBar
        :selected_channel_id="filters.channel_id"
        :syncing="syncing"
        @search="onSearch"
        @sync="onSyncTelegram"
      />
      <MessageTable
        :data="data"
        :loading="loading"
        :total="total"
        :page="page"
        :page_size="page_size"
        :channels="channels"
        :show_channel="filters.channel_id === undefined"
        @toggle-read="onToggleReadStatus"
        @update:page="onPageChange"
        @update:page_size="onPageSizeChange"
      />
    </section>
  </div>
</template>

<style scoped>
.home-layout {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-width: 0;
}

.content-panel {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 16px;
}
</style>
