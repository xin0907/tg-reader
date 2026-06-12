export interface ItemStats {
  views: number
  forwards: number
  replies: number
}

export interface Item {
  channel_id: number
  message_id: number
  grouped_id?: string | null
  is_read: boolean
  sent_at: string
  content: string
  media_type?: string | null
  images: string[]
  stats: ItemStats
  link?: string | null
}

export interface FetchParams {
  page?: number
  page_size?: number
  channel_id?: number
  keyword?: string
  is_read?: boolean
}

export interface Channel {
  id: number
  name: string
  username?: string | null
}

export interface MessageKey {
  channel_id: number
  message_id: number
}

export interface MessageListResponse {
  total: number
  page: number
  page_size: number
  items: Item[]
}

export type SyncMode = 'limit' | 'all'
