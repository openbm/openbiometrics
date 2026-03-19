interface Props {
  name: string;
  onLogout: () => void;
}

const STATS = [
  { label: 'Revenue', value: '$48,352', change: '+12.5%' },
  { label: 'Users', value: '2,847', change: '+4.3%' },
  { label: 'Orders', value: '1,293', change: '+8.1%' },
  { label: 'Conversion', value: '3.24%', change: '+0.4%' },
];

const ACTIVITY = [
  { action: 'New order #4821', time: '2 min ago', type: 'order' },
  { action: 'User signup: sarah@example.com', time: '8 min ago', type: 'user' },
  { action: 'Payment received $299', time: '15 min ago', type: 'payment' },
  { action: 'Support ticket #892 resolved', time: '1 hr ago', type: 'support' },
  { action: 'New order #4820', time: '2 hr ago', type: 'order' },
];

export function DashboardScreen({ name, onLogout }: Props) {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-sm">
              A
            </div>
            <h1 className="text-lg font-semibold">Acme Dashboard</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-400">
              Welcome, <span className="text-white font-medium">{name}</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-sm font-medium text-indigo-400">
              {name.charAt(0).toUpperCase()}
            </div>
            <button
              onClick={onLogout}
              className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 space-y-8">
        {/* Success banner */}
        <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-green-400 text-sm">
            Identity verified via face biometrics with liveness detection
          </span>
          <span className="text-green-600 text-xs ml-auto">Powered by OpenBiometrics</span>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {STATS.map((stat) => (
            <div key={stat.label} className="bg-gray-900 rounded-xl border border-gray-800 p-5">
              <div className="text-sm text-gray-400 mb-1">{stat.label}</div>
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="text-xs text-green-400 mt-1">{stat.change}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Activity feed */}
          <div className="lg:col-span-2 bg-gray-900 rounded-xl border border-gray-800 p-5">
            <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
            <div className="space-y-3">
              {ACTIVITY.map((item, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      item.type === 'order' ? 'bg-blue-500' :
                      item.type === 'user' ? 'bg-purple-500' :
                      item.type === 'payment' ? 'bg-green-500' :
                      'bg-yellow-500'
                    }`} />
                    <span className="text-sm">{item.action}</span>
                  </div>
                  <span className="text-xs text-gray-500">{item.time}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Security info */}
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
            <h2 className="text-lg font-semibold mb-4">Security</h2>
            <div className="space-y-4">
              <div className="space-y-1">
                <div className="text-xs text-gray-400">Authentication</div>
                <div className="text-sm text-white">Password + Face 2FA</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-400">Liveness Check</div>
                <div className="text-sm text-green-400">Passed</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-400">Session Started</div>
                <div className="text-sm text-white">{new Date().toLocaleTimeString()}</div>
              </div>
              <div className="space-y-1">
                <div className="text-xs text-gray-400">Verified As</div>
                <div className="text-sm text-indigo-400">{name}</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
