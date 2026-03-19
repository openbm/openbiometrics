import { useState, type FormEvent } from 'react';

interface Props {
  onLogin: (email: string) => void;
  onEnroll: () => void;
}

export function LoginScreen({ onLogin, onEnroll }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (email && password) onLogin(email);
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center">
          <div className="w-14 h-14 rounded-2xl bg-indigo-600 flex items-center justify-center text-xl font-bold mx-auto mb-4">
            A
          </div>
          <h1 className="text-2xl font-bold text-white">Acme SaaS</h1>
          <p className="text-gray-400 text-sm mt-1">Sign in with face verification</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              className="w-full px-4 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
          <button
            type="submit"
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors"
          >
            Continue to Face Verification
          </button>
        </form>

        <div className="border-t border-gray-800 pt-4">
          <p className="text-center text-sm text-gray-500 mb-3">First time? Enroll your face for 2FA</p>
          <button
            onClick={onEnroll}
            className="w-full py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg font-medium transition-colors border border-gray-700"
          >
            Enroll Face
          </button>
        </div>

        <p className="text-center text-xs text-gray-600">
          Powered by <span className="text-indigo-400">OpenBiometrics</span>
        </p>
      </div>
    </div>
  );
}
