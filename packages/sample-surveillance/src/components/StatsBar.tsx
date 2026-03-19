import { useState, useEffect, useCallback } from 'react'
import type { AdminHealth } from '../api'
import { getAdminHealth, listCameras, getRecentEvents, listWebhooks } from '../api'

interface Stats {
  health: AdminHealth | null
  cameraCount: number
  eventCount: number
  webhookCount: number
}

function ModuleDot({ name, status }: { name: string; status: string }) {
  const color = status === 'ok' || status === 'healthy'
    ? 'bg-emerald-500'
    : status === 'degraded'
      ? 'bg-amber-500'
      : 'bg-red-500'

  return (
    <div className="flex items-center gap-1.5" title={`${name}: ${status}`}>
      <span className={`inline-block w-1.5 h-1.5 rounded-full ${color}`} />
      <span className="text-[10px] text-gray-400 capitalize">{name}</span>
    </div>
  )
}

export default function StatsBar() {
  const [stats, setStats] = useState<Stats>({ health: null, cameraCount: 0, eventCount: 0, webhookCount: 0 })
  const [error, setError] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [health, cameras, events, webhooks] = await Promise.allSettled([
        getAdminHealth(),
        listCameras(),
        getRecentEvents(1000),
        listWebhooks(),
      ])

      setStats({
        health: health.status === 'fulfilled' ? health.value : null,
        cameraCount: cameras.status === 'fulfilled' ? cameras.value.length : 0,
        eventCount: events.status === 'fulfilled' ? events.value.length : 0,
        webhookCount: webhooks.status === 'fulfilled' ? webhooks.value.length : 0,
      })
      setError(false)
    } catch {
      setError(true)
    }
  }, [])

  useEffect(() => {
    refresh()
    const iv = setInterval(refresh, 10000)
    return () => clearInterval(iv)
  }, [refresh])

  const modules = stats.health?.modules ?? {}
  const moduleNames = Object.keys(modules)

  return (
    <div className="bg-gray-800/80 border-t border-gray-700 px-6 py-2.5">
      <div className="flex items-center justify-between flex-wrap gap-x-6 gap-y-1">
        {/* System modules */}
        <div className="flex items-center gap-4">
          <span className="text-[10px] text-gray-500 uppercase tracking-wider mr-1">Modules</span>
          {error || moduleNames.length === 0 ? (
            <>
              <ModuleDot name="face" status="unknown" />
              <ModuleDot name="person" status="unknown" />
              <ModuleDot name="video" status="unknown" />
              <ModuleDot name="events" status="unknown" />
            </>
          ) : (
            moduleNames.map((name) => (
              <ModuleDot key={name} name={name} status={modules[name].status} />
            ))
          )}
        </div>

        {/* Counters */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
            </svg>
            <span className="text-xs text-gray-300 font-mono">{stats.cameraCount}</span>
            <span className="text-[10px] text-gray-500">cameras</span>
          </div>

          <div className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-xs text-gray-300 font-mono">{stats.eventCount}</span>
            <span className="text-[10px] text-gray-500">events</span>
          </div>

          <div className="flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.036-3.036a4.5 4.5 0 00-1.242-7.244l-4.5-4.5a4.5 4.5 0 00-6.364 6.364L4.25 8.81" />
            </svg>
            <span className="text-xs text-gray-300 font-mono">{stats.webhookCount}</span>
            <span className="text-[10px] text-gray-500">webhooks</span>
          </div>

          {stats.health && (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-gray-600">v{stats.health.version}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
