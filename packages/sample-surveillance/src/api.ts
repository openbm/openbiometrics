// ---------- Types ----------

export interface CameraInfo {
  camera_id: string
  source: string
  status: CameraStatus
  fps: number
  frame_count: number
  created_at: string
}

export type CameraStatus = 'running' | 'stopped' | 'error' | 'connecting'

export interface EventInfo {
  event_id: string
  event_type: string
  camera_id: string
  timestamp: string
  description: string
  metadata?: Record<string, unknown>
}

export interface WebhookInfo {
  webhook_id: string
  url: string
  event_types: string[]
  created_at: string
  active: boolean
}

export interface AdminHealth {
  status: string
  modules: Record<string, { status: string; message?: string }>
  uptime_seconds: number
  version: string
}

// ---------- Helpers ----------

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${text}`)
  }
  return res.json() as Promise<T>
}

// ---------- Camera API ----------

export function addCamera(source: string, cameraId?: string) {
  return request<CameraInfo>('/api/v1/video/cameras', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, camera_id: cameraId || undefined }),
  })
}

export function removeCamera(cameraId: string) {
  return request<{ success: boolean }>(`/api/v1/video/cameras/${encodeURIComponent(cameraId)}`, {
    method: 'DELETE',
  })
}

export function listCameras() {
  return request<CameraInfo[]>('/api/v1/video/cameras')
}

export function getCameraSnapshotUrl(cameraId: string) {
  return `/api/v1/video/cameras/${encodeURIComponent(cameraId)}/snapshot`
}

// ---------- Events API ----------

export function getRecentEvents(limit?: number, eventType?: string) {
  const params = new URLSearchParams()
  if (limit) params.set('limit', String(limit))
  if (eventType) params.set('event_type', eventType)
  const qs = params.toString()
  return request<EventInfo[]>(`/api/v1/events/recent${qs ? `?${qs}` : ''}`)
}

// ---------- Webhooks API ----------

export function registerWebhook(url: string, eventTypes: string[]) {
  return request<WebhookInfo>('/api/v1/events/webhooks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, event_types: eventTypes }),
  })
}

export function listWebhooks() {
  return request<WebhookInfo[]>('/api/v1/events/webhooks')
}

export function deleteWebhook(webhookId: string) {
  return request<{ success: boolean }>(`/api/v1/events/webhooks/${encodeURIComponent(webhookId)}`, {
    method: 'DELETE',
  })
}

// ---------- Admin API ----------

export function getAdminHealth() {
  return request<AdminHealth>('/api/v1/admin/health')
}
