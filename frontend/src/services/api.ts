import type { Channel, FetchParams, MessageKey, MessageListResponse } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const { headers: customHeaders, ...restInit } = init || {}
  const resp = await fetch(`${API_BASE}${path}`, {
    ...restInit,
    headers: {
      'Content-Type': 'application/json',
      ...customHeaders,
    },
  })

  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(text || `Request failed: ${resp.status}`)
  }

  if (resp.status === 204) {
    return {} as T
  }

  return (await resp.json()) as T
}

function buildQuery(params: object): string {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (
      value !== undefined &&
      value !== '' &&
      (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean')
    ) {
      query.set(key, String(value))
    }
  })
  const q = query.toString()
  return q ? `?${q}` : ''
}

export function fetchMessages(params: FetchParams): Promise<MessageListResponse> {
  return request<MessageListResponse>(`/messages${buildQuery(params)}`)
}

export function fetchChannels(): Promise<Channel[]> {
  return request<Channel[]>('/channels')
}

export function patchMessageRead(
  message_keys: MessageKey[],
  is_read: boolean,
): Promise<{ affected: number }> {
  return request<{ affected: number }>('/messages/read', {
    method: 'PATCH',
    body: JSON.stringify({ message_keys, is_read }),
  })
}

export function syncTelegram(channel_id: number, limit = 200): Promise<unknown> {
  return request<unknown>(`/channel/sync-telegram${buildQuery({ channel_id, limit })}`, {
    method: 'POST',
  })
}

export function syncTelegramAll(channel_id: number): Promise<unknown> {
  return request<unknown>(
    `/channel/sync-telegram${buildQuery({ channel_id, sync_all: true })}`,
    {
      method: 'POST',
    },
  )
}
