import { useState } from 'react';
import { DetectPanel } from './components/DetectPanel';
import { VerifyPanel } from './components/VerifyPanel';
import { WatchlistPanel } from './components/WatchlistPanel';
import { DocumentPanel } from './components/DocumentPanel';
import { LivenessPanel } from './components/LivenessPanel';
import { VideoPanel } from './components/VideoPanel';
import { EventsPanel } from './components/EventsPanel';
import { AdminPanel } from './components/AdminPanel';
import { StatusBar } from './components/StatusBar';

type Tab = 'detect' | 'verify' | 'watchlist' | 'documents' | 'liveness' | 'video' | 'events' | 'admin';

const TAB_LABELS: Record<Tab, string> = {
  detect: 'Detect',
  verify: '1:1 Verify',
  watchlist: '1:N Watchlist',
  documents: 'Documents',
  liveness: 'Liveness',
  video: 'Video',
  events: 'Events',
  admin: 'Admin',
};

export default function App() {
  const [tab, setTab] = useState<Tab>('detect');

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-sm">
              OB
            </div>
            <h1 className="text-xl font-semibold tracking-tight">OpenBiometrics</h1>
            <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">v0.1</span>
          </div>
          <StatusBar />
        </div>
        <nav className="max-w-6xl mx-auto px-6 flex gap-1 overflow-x-auto">
          {(Object.keys(TAB_LABELS) as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${
                tab === t
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-600'
              }`}
            >
              {TAB_LABELS[t]}
            </button>
          ))}
        </nav>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {tab === 'detect' && <DetectPanel />}
        {tab === 'verify' && <VerifyPanel />}
        {tab === 'watchlist' && <WatchlistPanel />}
        {tab === 'documents' && <DocumentPanel />}
        {tab === 'liveness' && <LivenessPanel />}
        {tab === 'video' && <VideoPanel />}
        {tab === 'events' && <EventsPanel />}
        {tab === 'admin' && <AdminPanel />}
      </main>
    </div>
  );
}
