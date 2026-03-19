import { useState, useEffect, useCallback } from 'react'
import type { EventInfo } from '../api'
import { getRecentEvents } from '../api'

const EVENT_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  FACE_DETECTED: { bg: 'bg-blue-500/15', text: 'text-blue-400', icon: 'M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0' },
  FACE_MATCHED: { bg: 'bg-red-500/15', text: 'text-red-400', icon: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z' },
  WATCHLIST_ALERT: { bg: 'bg-red-500/15', text: 'text-red-400', icon: 'M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0' },
  PERSON_ENTERED: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', icon: 'M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9' },
  PERSON_EXITED: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', icon: 'M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75' },
  LINE_CROSSED: { bg: 'bg-amber-500/15', text: 'text-amber-400', icon: 'M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9m11.25-5.25v4.5m0-4.5h-4.5m4.5 0L15 9m-11.25 11.25v-4.5m0 4.5h4.5m-4.5 0L9 15m11.25 5.25v-4.5m0 4.5h-4.5m4.5 0L15 15' },
}

const DEFAULT_EVENT = { bg: 'bg-gray-500/15', text: 'text-gray-400', icon: 'M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z' }

function relativeTime(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime()
  if (diff < 0) return 'just now'
  const sec = Math.floor(diff / 1000)
  if (sec < 60) return `${sec}s ago`
  const min = Math.floor(sec / 60)
  if (min < 60) return `${min}m ago`
  const hr = Math.floor(min / 60)
  if (hr < 24) return `${hr}h ago`
  return `${Math.floor(hr / 24)}d ago`
}

function EventRow({ event }: { event: EventInfo }) {
  const style = EVENT_COLORS[event.event_type] ?? DEFAULT_EVENT
  const isAlert = event.event_type === 'FACE_MATCHED' || event.event_type === 'WATCHLIST_ALERT'

  return (
    <div className={`flex items-start gap-3 px-3 py-2.5 rounded-lg ${style.bg} ${isAlert ? 'ring-1 ring-red-500/30' : ''}`}>
      <div className={`shrink-0 mt-0.5 ${style.text}`}>
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d={style.icon} />
        </svg>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className={`text-xs font-mono font-medium ${style.text}`}>
            {event.event_type.replace(/_/g, ' ')}
          </span>
          <span className="text-[10px] text-gray-500 shrink-0">{relativeTime(event.timestamp)}</span>
        </div>
        <p className="text-xs text-gray-400 mt-0.5 truncate">{event.description}</p>
        <p className="text-[10px] text-gray-600 mt-0.5 font-mono">{event.camera_id}</p>
      </div>
    </div>
  )
}

export default function EventFeed() {
  const [events, setEvents] = useState<EventInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const list = await getRecentEvents(30)
      setEvents(list)
      setError('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const iv = setInterval(refresh, 3000)
    return () => clearInterval(iv)
  }, [refresh])

  const clearEvents = () => setEvents([])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Live Events</h2>
        </div>
        <button
          onClick={clearEvents}
          className="text-[10px] text-gray-500 hover:text-gray-300 transition-colors uppercase tracking-wider"
        >
          Clear
        </button>
      </div>

      {/* Events list */}
      <div className="flex-1 overflow-y-auto space-y-1.5 min-h-0 pr-1 scrollbar-thin">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-xs text-gray-500">{error}</p>
            <button onClick={refresh} className="text-xs text-cyan-400 hover:underline mt-1">Retry</button>
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-8 h-8 text-gray-700 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-xs text-gray-600">No events yet</p>
            <p className="text-[10px] text-gray-700 mt-1">Events will appear here in real-time</p>
          </div>
        ) : (
          events.map((ev) => <EventRow key={ev.event_id} event={ev} />)
        )}
      </div>
    </div>
  )
}
