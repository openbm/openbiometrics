import { useEffect, useRef, useState } from 'react';
import {
  getRecentEvents,
  registerWebhook,
  deleteWebhook,
  listWebhooks,
  type EventInfo,
  type WebhookInfo,
} from '../api';

const EVENT_TYPES = [
  'face.detected',
  'face.identified',
  'face.enrolled',
  'document.scanned',
  'liveness.completed',
  'camera.started',
  'camera.stopped',
  'camera.error',
];

export function EventsPanel() {
  const [events, setEvents] = useState<EventInfo[]>([]);
  const [webhooks, setWebhooks] = useState<WebhookInfo[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [filterType, setFilterType] = useState<string>('');
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Webhook form state
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookSecret, setWebhookSecret] = useState('');
  const [webhookEventTypes, setWebhookEventTypes] = useState<string[]>([]);
  const [webhookLoading, setWebhookLoading] = useState(false);
  const [webhookError, setWebhookError] = useState<string | null>(null);

  const fetchEvents = async () => {
    try {
      const res = await getRecentEvents(50, filterType || undefined);
      setEvents(res.events);
    } catch {
      // silently fail on poll
    }
  };

  const fetchWebhooks = async () => {
    try {
      const res = await listWebhooks();
      setWebhooks(res.webhooks);
    } catch {
      // silently fail
    }
  };

  useEffect(() => {
    fetchEvents();
    fetchWebhooks();
  }, [filterType]);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchEvents, 5000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh, filterType]);

  const handleRegisterWebhook = async () => {
    if (!webhookUrl.trim() || webhookEventTypes.length === 0) return;
    setWebhookLoading(true);
    setWebhookError(null);

    try {
      await registerWebhook(
        webhookUrl.trim(),
        webhookEventTypes,
        webhookSecret.trim() || undefined
      );
      setWebhookUrl('');
      setWebhookSecret('');
      setWebhookEventTypes([]);
      await fetchWebhooks();
    } catch (e) {
      setWebhookError(e instanceof Error ? e.message : 'Failed to register webhook');
    } finally {
      setWebhookLoading(false);
    }
  };

  const handleDeleteWebhook = async (id: string) => {
    try {
      await deleteWebhook(id);
      await fetchWebhooks();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete webhook');
    }
  };

  const toggleEventType = (type: string) => {
    setWebhookEventTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Events & Webhooks</h2>
        <p className="text-gray-400 text-sm">
          Monitor system events and manage webhook subscriptions.
        </p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Events table */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-400">Recent Events</h3>
          <div className="flex items-center gap-4">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="">All types</option>
              {EVENT_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <div
                onClick={() => setAutoRefresh((v) => !v)}
                className={`w-8 h-4.5 rounded-full transition-colors relative cursor-pointer ${
                  autoRefresh ? 'bg-indigo-600' : 'bg-gray-700'
                }`}
              >
                <div className={`absolute top-0.5 w-3.5 h-3.5 rounded-full bg-white transition-transform ${
                  autoRefresh ? 'translate-x-4' : 'translate-x-0.5'
                }`} />
              </div>
              Auto-refresh
            </label>
          </div>
        </div>

        {events.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-8">No events found.</div>
        ) : (
          <div className="space-y-1 max-h-96 overflow-auto">
            {events.map((evt) => (
              <div key={evt.id}>
                <div
                  onClick={() => setExpandedEvent(expandedEvent === evt.id ? null : evt.id)}
                  className="flex items-center gap-4 px-3 py-2.5 rounded-lg hover:bg-gray-800/50 cursor-pointer transition-colors"
                >
                  <span className="text-xs text-gray-500 font-mono w-40 shrink-0">
                    {new Date(evt.timestamp).toLocaleString()}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shrink-0">
                    {evt.type}
                  </span>
                  <span className="text-xs text-gray-500 shrink-0">{evt.source}</span>
                  <span className="text-xs text-gray-400 truncate ml-auto">
                    {summarizeEvent(evt)}
                  </span>
                </div>
                {expandedEvent === evt.id && (
                  <pre className="bg-gray-800/50 rounded-lg p-3 mx-3 mb-2 text-xs text-gray-300 overflow-auto max-h-48 font-mono">
                    {JSON.stringify(evt.data, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Webhooks management */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
        <h3 className="text-sm font-medium text-gray-400">Webhooks</h3>

        {/* Register form */}
        <div className="space-y-3 bg-gray-800/50 rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Webhook URL</label>
              <input
                type="text"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://example.com/webhook"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Secret (optional)</label>
              <input
                type="text"
                value={webhookSecret}
                onChange={(e) => setWebhookSecret(e.target.value)}
                placeholder="webhook-secret"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-2">Event Types</label>
            <div className="flex flex-wrap gap-2">
              {EVENT_TYPES.map((type) => (
                <button
                  key={type}
                  onClick={() => toggleEventType(type)}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                    webhookEventTypes.includes(type)
                      ? 'bg-indigo-600/20 text-indigo-400 border-indigo-500/30'
                      : 'bg-gray-900 text-gray-500 border-gray-700 hover:border-gray-500'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleRegisterWebhook}
            disabled={!webhookUrl.trim() || webhookEventTypes.length === 0 || webhookLoading}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-medium transition-colors"
          >
            {webhookLoading ? 'Registering...' : 'Register Webhook'}
          </button>

          {webhookError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
              {webhookError}
            </div>
          )}
        </div>

        {/* Webhook list */}
        {webhooks.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-4">No webhooks registered.</div>
        ) : (
          <div className="space-y-2">
            {webhooks.map((wh) => (
              <div key={wh.id} className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3">
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium truncate">{wh.url}</div>
                  <div className="flex items-center gap-2 mt-1">
                    {wh.event_types.map((t) => (
                      <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteWebhook(wh.id)}
                  className="text-xs text-gray-500 hover:text-red-400 transition-colors ml-4 shrink-0"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function summarizeEvent(evt: EventInfo): string {
  const d = evt.data;
  if (d.count !== undefined) return `${d.count} detected`;
  if (d.label) return String(d.label);
  if (d.camera_id) return `camera: ${d.camera_id}`;
  if (d.session_id) return `session: ${String(d.session_id).slice(0, 8)}`;
  return '';
}
