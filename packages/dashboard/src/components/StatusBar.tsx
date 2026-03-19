import { useEffect, useState } from 'react';
import { getHealth, type HealthResponse } from '../api';

export function StatusBar() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const check = () =>
      getHealth()
        .then((h) => { setHealth(h); setError(false); })
        .catch(() => setError(true));

    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="flex items-center gap-2 text-xs text-red-400">
        <div className="w-2 h-2 rounded-full bg-red-500" />
        Backend offline
      </div>
    );
  }

  if (!health) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <div className="w-2 h-2 rounded-full bg-gray-600 animate-pulse" />
        Connecting...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 text-xs text-gray-400">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${health.models_loaded ? 'bg-green-500' : 'bg-yellow-500'}`} />
        {health.models_loaded ? 'Models loaded' : 'Models not loaded'}
      </div>
      <div className="text-gray-600">|</div>
      <div>Watchlist: {health.watchlist_count} faces</div>
    </div>
  );
}
