import { useState, useEffect, useCallback } from 'react'
import type { WebhookInfo } from '../api'
import { listWebhooks, registerWebhook, deleteWebhook } from '../api'

const ALL_EVENT_TYPES = [
  'FACE_DETECTED',
  'FACE_MATCHED',
  'WATCHLIST_ALERT',
  'PERSON_ENTERED',
  'PERSON_EXITED',
  'LINE_CROSSED',
]

export default function WebhookManager() {
  const [open, setOpen] = useState(false)
  const [webhooks, setWebhooks] = useState<WebhookInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [url, setUrl] = useState('')
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set())
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const list = await listWebhooks()
      setWebhooks(list)
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (open) refresh()
  }, [open, refresh])

  const toggleType = (t: string) => {
    setSelectedTypes((prev) => {
      const next = new Set(prev)
      if (next.has(t)) next.delete(t)
      else next.add(t)
      return next
    })
  }

  const handleRegister = async () => {
    if (!url.trim() || selectedTypes.size === 0) return
    setSubmitting(true)
    setError('')
    try {
      await registerWebhook(url.trim(), Array.from(selectedTypes))
      setUrl('')
      setSelectedTypes(new Set())
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to register webhook')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteWebhook(id)
      setWebhooks((prev) => prev.filter((w) => w.webhook_id !== id))
    } catch {
      // silent
    }
  }

  return (
    <div className="bg-gray-800/60 rounded-lg border border-gray-700">
      {/* Toggle header */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-800 transition-colors rounded-lg"
      >
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m9.036-3.036a4.5 4.5 0 00-1.242-7.244l-4.5-4.5a4.5 4.5 0 00-6.364 6.364L4.25 8.81" />
          </svg>
          <span className="text-sm font-medium text-gray-300">Webhooks</span>
          {webhooks.length > 0 && (
            <span className="text-[10px] bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded-full">{webhooks.length}</span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4">
          {/* Register form */}
          <div className="space-y-2">
            <input
              type="url"
              placeholder="https://example.com/webhook"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-600 focus:outline-none"
            />
            <div className="flex flex-wrap gap-1.5">
              {ALL_EVENT_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => toggleType(t)}
                  className={`text-[10px] px-2 py-1 rounded border transition-colors ${
                    selectedTypes.has(t)
                      ? 'bg-cyan-900/50 border-cyan-700 text-cyan-300'
                      : 'bg-gray-900 border-gray-700 text-gray-500 hover:text-gray-300'
                  }`}
                >
                  {t.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
            <button
              onClick={handleRegister}
              disabled={submitting || !url.trim() || selectedTypes.size === 0}
              className="w-full bg-cyan-700 hover:bg-cyan-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded px-3 py-1.5 transition-colors"
            >
              {submitting ? 'Registering...' : 'Register Webhook'}
            </button>
            {error && <p className="text-xs text-red-400">{error}</p>}
          </div>

          {/* Active webhooks */}
          {loading ? (
            <div className="flex justify-center py-3">
              <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : webhooks.length === 0 ? (
            <p className="text-xs text-gray-600 text-center py-2">No webhooks registered</p>
          ) : (
            <div className="space-y-1.5">
              {webhooks.map((wh) => (
                <div key={wh.webhook_id} className="flex items-center justify-between bg-gray-900/50 rounded px-3 py-2">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-gray-300 font-mono truncate">{wh.url}</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">
                      {wh.event_types.map((t) => t.replace(/_/g, ' ')).join(', ')}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(wh.webhook_id)}
                    className="ml-2 text-gray-600 hover:text-red-400 transition-colors shrink-0"
                    title="Delete webhook"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
