import { useState, useCallback } from 'react';
import { useWebcam } from '../useWebcam.ts';
import { identifyFace, enrollFace } from '../api.ts';
import type { WatchlistMatch } from '../api.ts';

interface CheckInEntry {
  name: string;
  time: string;
  type: 'returning' | 'new';
}

export function CheckInTab() {
  const { videoRef, ready, error: camError, captureFrame } = useWebcam();

  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Identification result state
  const [match, setMatch] = useState<WatchlistMatch | null>(null);
  const [noMatch, setNoMatch] = useState(false);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);

  // Registration state
  const [name, setName] = useState('');
  const [registering, setRegistering] = useState(false);
  const [registered, setRegistered] = useState<string | null>(null);

  // Recent check-ins
  const [recentCheckins, setRecentCheckins] = useState<CheckInEntry[]>([]);

  const addCheckin = useCallback((entry: CheckInEntry) => {
    setRecentCheckins((prev) => [entry, ...prev].slice(0, 5));
  }, []);

  const reset = useCallback(() => {
    setMatch(null);
    setNoMatch(false);
    setCapturedBlob(null);
    setName('');
    setRegistered(null);
    setError(null);
  }, []);

  const handleScan = useCallback(async () => {
    reset();
    setScanning(true);
    setError(null);
    try {
      const blob = await captureFrame();
      setCapturedBlob(blob);
      const result = await identifyFace(blob);
      if (result.matches.length > 0 && result.matches[0].similarity > 0.5) {
        const topMatch = result.matches[0];
        setMatch(topMatch);
        addCheckin({
          name: topMatch.label,
          time: new Date().toLocaleTimeString(),
          type: 'returning',
        });
      } else {
        setNoMatch(true);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Scan failed');
    } finally {
      setScanning(false);
    }
  }, [captureFrame, reset, addCheckin]);

  const handleRegister = useCallback(async () => {
    if (!capturedBlob || !name.trim()) return;
    setRegistering(true);
    setError(null);
    try {
      await enrollFace(capturedBlob, name.trim());
      setRegistered(name.trim());
      setNoMatch(false);
      addCheckin({
        name: name.trim(),
        time: new Date().toLocaleTimeString(),
        type: 'new',
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Registration failed');
    } finally {
      setRegistering(false);
    }
  }, [capturedBlob, name, addCheckin]);

  return (
    <div className="space-y-6">
      {/* Webcam Feed */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="relative bg-slate-900 aspect-video max-h-80 flex items-center justify-center">
          {camError ? (
            <div className="text-center p-8">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-12 h-12 text-red-400 mx-auto mb-3">
                <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
              </svg>
              <p className="text-red-300 text-sm font-medium">Camera unavailable</p>
              <p className="text-slate-500 text-xs mt-1">{camError}</p>
            </div>
          ) : (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          )}
          {!ready && !camError && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
              <div className="flex items-center gap-3 text-slate-300">
                <svg className="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="text-sm">Starting camera...</span>
              </div>
            </div>
          )}
        </div>

        <div className="p-4">
          <button
            onClick={handleScan}
            disabled={!ready || scanning}
            className="w-full py-3 px-4 rounded-lg font-medium text-white bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {scanning ? (
              <>
                <svg className="w-5 h-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Scanning...
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 3.75H6A2.25 2.25 0 0 0 3.75 6v1.5M16.5 3.75H18A2.25 2.25 0 0 1 20.25 6v1.5M20.25 16.5V18A2.25 2.25 0 0 1 18 20.25h-1.5M3.75 16.5V18A2.25 2.25 0 0 0 6 20.25h1.5M12 9v3m0 0v3m0-3h3m-3 0H9" />
                </svg>
                Scan Face
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-red-500 mt-0.5 shrink-0">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
          </svg>
          <div>
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-600 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Match Found - Welcome Back */}
      {match && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-emerald-600">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-emerald-900">Welcome back, {match.label}!</h3>
              <p className="text-sm text-emerald-700">
                Similarity: {(match.similarity * 100).toFixed(1)}%
              </p>
            </div>
          </div>
          <p className="text-xs text-emerald-600">
            Check-in logged at {new Date().toLocaleTimeString()}
          </p>
          <button
            onClick={reset}
            className="mt-4 text-sm text-emerald-700 hover:text-emerald-900 underline"
          >
            Scan another visitor
          </button>
        </div>
      )}

      {/* No Match - Registration Form */}
      {noMatch && !registered && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-blue-600">
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.766Z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-blue-900">New visitor detected</h3>
              <p className="text-sm text-blue-700">Register to enable quick check-in next time.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              className="flex-1 px-3 py-2 border border-blue-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              onKeyDown={(e) => e.key === 'Enter' && handleRegister()}
            />
            <button
              onClick={handleRegister}
              disabled={!name.trim() || registering}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {registering ? 'Registering...' : 'Register'}
            </button>
          </div>
          <button
            onClick={reset}
            className="mt-3 text-sm text-blue-600 hover:text-blue-800 underline"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Registration Confirmation */}
      {registered && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-emerald-600">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-emerald-900">Welcome, {registered}!</h3>
              <p className="text-sm text-emerald-700">You've been registered successfully.</p>
            </div>
          </div>
          <button
            onClick={reset}
            className="mt-4 text-sm text-emerald-700 hover:text-emerald-900 underline"
          >
            Scan another visitor
          </button>
        </div>
      )}

      {/* Recent Check-ins */}
      {recentCheckins.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
          <div className="px-4 py-3 border-b border-slate-100">
            <h3 className="text-sm font-medium text-slate-700">Recent Check-ins</h3>
          </div>
          <ul className="divide-y divide-slate-100">
            {recentCheckins.map((entry, i) => (
              <li key={i} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${entry.type === 'returning' ? 'bg-emerald-500' : 'bg-blue-500'}`} />
                  <span className="text-sm text-slate-800 font-medium">{entry.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${entry.type === 'returning' ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'}`}>
                    {entry.type === 'returning' ? 'Returning' : 'New'}
                  </span>
                </div>
                <span className="text-xs text-slate-500">{entry.time}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
