import { useState, useEffect, useCallback } from 'react'
import CameraGrid from './components/CameraGrid.tsx'
import EventFeed from './components/EventFeed.tsx'
import StatsBar from './components/StatsBar.tsx'
import WebhookManager from './components/WebhookManager.tsx'
import { getAdminHealth, listCameras } from './api'

export default function App() {
  const [healthOk, setHealthOk] = useState<boolean | null>(null)
  const [cameraCount, setCameraCount] = useState(0)

  const checkStatus = useCallback(async () => {
    try {
      const [health, cameras] = await Promise.allSettled([getAdminHealth(), listCameras()])
      setHealthOk(health.status === 'fulfilled' && (health.value.status === 'ok' || health.value.status === 'healthy'))
      setCameraCount(cameras.status === 'fulfilled' ? cameras.value.length : 0)
    } catch {
      setHealthOk(false)
    }
  }, [])

  useEffect(() => {
    checkStatus()
    const iv = setInterval(checkStatus, 10000)
    return () => clearInterval(iv)
  }, [checkStatus])

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      {/* Top bar */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-cyan-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-wide text-gray-100">SecureWatch</h1>
              <p className="text-[10px] text-gray-500 -mt-0.5">Video Analytics Platform</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-5">
          {/* Camera count */}
          <div className="flex items-center gap-1.5">
            <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
            </svg>
            <span className="text-xs text-gray-300 font-mono">{cameraCount}</span>
          </div>

          {/* Health indicator */}
          <div className="flex items-center gap-1.5">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                healthOk === null
                  ? 'bg-gray-600'
                  : healthOk
                    ? 'bg-emerald-500'
                    : 'bg-red-500'
              }`}
            />
            <span className="text-xs text-gray-400">
              {healthOk === null ? 'Checking...' : healthOk ? 'System Online' : 'System Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left: cameras + webhooks (2/3) */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 min-w-0" style={{ flex: '2 1 0%' }}>
          <CameraGrid />
          <WebhookManager />
        </div>

        {/* Right: event feed (1/3) */}
        <div
          className="border-l border-gray-800 overflow-hidden flex flex-col p-4"
          style={{ flex: '1 1 0%', maxWidth: '420px', minWidth: '300px' }}
        >
          <EventFeed />
        </div>
      </main>

      {/* Bottom stats bar */}
      <StatsBar />
    </div>
  )
}
