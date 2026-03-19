import { useEffect, useState } from 'react';
import { getAdminHealth, getModels, type AdminHealth, type ModelStatus } from '../api';

export function AdminPanel() {
  const [health, setHealth] = useState<AdminHealth | null>(null);
  const [models, setModels] = useState<ModelStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      setError(null);
      try {
        const [h, m] = await Promise.all([getAdminHealth(), getModels()]);
        setHealth(h);
        setModels(m.models);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load admin data');
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold mb-2">Administration</h2>
          <p className="text-gray-400 text-sm">System health, models, and configuration.</p>
        </div>
        <div className="flex items-center gap-3 text-indigo-400 text-sm">
          <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          Loading admin data...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Administration</h2>
        <p className="text-gray-400 text-sm">
          System health, models, and configuration.
        </p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Module health cards */}
      {health && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <ModuleCard
            name="Face"
            status={health.modules.face.status}
            detail={health.modules.face.models_loaded ? 'Models loaded' : 'Models not loaded'}
          />
          <ModuleCard
            name="Document"
            status={health.modules.document.status}
            detail={health.modules.document.models_loaded ? 'Models loaded' : 'Models not loaded'}
          />
          <ModuleCard
            name="Liveness"
            status={health.modules.liveness.status}
            detail={`${health.modules.liveness.sessions_active} active sessions`}
          />
          <ModuleCard
            name="Video"
            status={health.modules.video.status}
            detail={`${health.modules.video.cameras_active} cameras active`}
          />
        </div>
      )}

      {/* Models table */}
      {models.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
          <h3 className="text-sm font-medium text-gray-400">Models</h3>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-800">
                  <th className="pb-2 pr-4 font-medium">Name</th>
                  <th className="pb-2 pr-4 font-medium">Size</th>
                  <th className="pb-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr key={model.name} className="border-b border-gray-800/50">
                    <td className="py-2.5 pr-4 font-medium">{model.name}</td>
                    <td className="py-2.5 pr-4 text-gray-400 font-mono text-xs">{model.size}</td>
                    <td className="py-2.5">
                      <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full ${
                        model.status === 'loaded'
                          ? 'bg-green-600/20 text-green-400 border border-green-500/30'
                          : model.status === 'available'
                          ? 'bg-yellow-600/20 text-yellow-400 border border-yellow-500/30'
                          : 'bg-red-600/20 text-red-400 border border-red-500/30'
                      }`}>
                        <div className={`w-1.5 h-1.5 rounded-full ${
                          model.status === 'loaded' ? 'bg-green-500' :
                          model.status === 'available' ? 'bg-yellow-500' : 'bg-red-500'
                        }`} />
                        {model.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* System info */}
      {health && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
            <h3 className="text-sm font-medium text-gray-400">System Info</h3>
            <div className="space-y-2">
              <InfoRow label="Uptime" value={health.system.uptime} />
              <InfoRow label="Memory Used" value={health.system.memory_used} />
              <InfoRow label="CPU Usage" value={`${health.system.cpu_percent.toFixed(1)}%`} />
            </div>
            {/* CPU bar */}
            <div className="space-y-1">
              <div className="w-full bg-gray-700 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all ${
                    health.system.cpu_percent > 80 ? 'bg-red-500' :
                    health.system.cpu_percent > 50 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(100, health.system.cpu_percent)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Configuration */}
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
            <h3 className="text-sm font-medium text-gray-400">Configuration</h3>
            <pre className="bg-gray-800/50 rounded-lg p-3 text-xs text-gray-300 max-h-64 overflow-auto font-mono">
              {JSON.stringify(health.config, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function ModuleCard({ name, status, detail }: { name: string; status: string; detail: string }) {
  const statusColor =
    status === 'ok' || status === 'healthy'
      ? 'green'
      : status === 'degraded' || status === 'warning'
      ? 'yellow'
      : 'red';

  const colors = {
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', dot: 'bg-green-500', text: 'text-green-400' },
    yellow: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', dot: 'bg-yellow-500', text: 'text-yellow-400' },
    red: { bg: 'bg-red-500/10', border: 'border-red-500/30', dot: 'bg-red-500', text: 'text-red-400' },
  };

  const c = colors[statusColor];

  return (
    <div className={`rounded-xl border p-4 space-y-2 ${c.bg} ${c.border}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{name}</span>
        <div className={`w-2.5 h-2.5 rounded-full ${c.dot}`} />
      </div>
      <div className={`text-xs font-medium ${c.text}`}>{status}</div>
      <div className="text-xs text-gray-500">{detail}</div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-mono text-gray-300">{value}</span>
    </div>
  );
}
