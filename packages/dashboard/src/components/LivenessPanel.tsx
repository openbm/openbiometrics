import { useState } from 'react';
import {
  createLivenessSession,
  submitLivenessFrame,
  deleteLivenessSession,
  type LivenessSession,
} from '../api';
import { ImageDropZone } from './ImageDropZone';

export function LivenessPanel() {
  const [session, setSession] = useState<LivenessSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [frameFile, setFrameFile] = useState<File | null>(null);
  const [framePreview, setFramePreview] = useState<string | null>(null);
  const [numChallenges, setNumChallenges] = useState(3);

  const handleStartSession = async () => {
    setLoading(true);
    setError(null);
    setSession(null);
    setFrameFile(null);
    setFramePreview(null);

    try {
      const res = await createLivenessSession(numChallenges);
      setSession(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFrame = async () => {
    if (!session || !frameFile) return;
    setSubmitLoading(true);
    setError(null);

    try {
      const res = await submitLivenessFrame(session.session_id, frameFile);
      setSession(res);
      setFrameFile(null);
      setFramePreview(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to submit frame');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDeleteSession = async () => {
    if (!session) return;
    try {
      await deleteLivenessSession(session.session_id);
      setSession(null);
      setFrameFile(null);
      setFramePreview(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete session');
    }
  };

  const isCompleted = session?.status === 'completed';
  const currentChallenge = session && !isCompleted
    ? session.challenges[session.current_challenge_index]
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Liveness Detection</h2>
        <p className="text-gray-400 text-sm">
          Create a liveness session with challenge-response to verify a live person.
        </p>
      </div>

      {!session && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-400">Challenges:</label>
              <input
                type="range"
                min="1"
                max="5"
                value={numChallenges}
                onChange={(e) => setNumChallenges(parseInt(e.target.value))}
                className="w-24 accent-indigo-500"
              />
              <span className="text-sm font-mono text-gray-300 w-4">{numChallenges}</span>
            </div>
            <button
              onClick={handleStartSession}
              disabled={loading}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? 'Starting...' : 'Start Session'}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {session && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: challenge and upload */}
          <div className="space-y-4">
            {/* Progress */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Session</span>
                <span className="text-xs text-gray-500 font-mono">{session.session_id.slice(0, 12)}...</span>
              </div>

              {/* Progress bar */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-gray-300">
                    {session.results.length} / {session.challenges.length}
                  </span>
                </div>
                <div className="flex gap-1.5">
                  {session.challenges.map((_, i) => (
                    <div
                      key={i}
                      className={`h-2 flex-1 rounded-full transition-colors ${
                        i < session.results.length
                          ? session.results[i].passed
                            ? 'bg-green-500'
                            : 'bg-red-500'
                          : i === session.current_challenge_index && !isCompleted
                          ? 'bg-indigo-500 animate-pulse'
                          : 'bg-gray-700'
                      }`}
                    />
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  session.status === 'completed'
                    ? 'bg-green-600/20 text-green-400'
                    : session.status === 'expired'
                    ? 'bg-red-600/20 text-red-400'
                    : 'bg-indigo-600/20 text-indigo-400'
                }`}>
                  {session.status}
                </span>
              </div>
            </div>

            {/* Current challenge instruction */}
            {currentChallenge && (
              <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-xl p-6 text-center">
                <div className="text-xs text-indigo-400 uppercase tracking-wider mb-2">
                  Challenge {session.current_challenge_index + 1} of {session.challenges.length}
                </div>
                <div className="text-xl font-semibold text-indigo-300">
                  {currentChallenge}
                </div>
              </div>
            )}

            {/* Upload frame */}
            {!isCompleted && (
              <div className="space-y-3">
                <ImageDropZone
                  onImage={(f, p) => {
                    setFrameFile(f);
                    setFramePreview(p);
                  }}
                  preview={framePreview}
                  label="Drop frame image for current challenge"
                />
                <button
                  onClick={handleSubmitFrame}
                  disabled={!frameFile || submitLoading}
                  className="w-full px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-medium transition-colors"
                >
                  {submitLoading ? 'Submitting...' : 'Submit Frame'}
                </button>
              </div>
            )}

            {/* Final result */}
            {isCompleted && (
              <div className={`rounded-xl border p-6 text-center space-y-3 ${
                session.is_live
                  ? 'bg-green-500/5 border-green-500/30'
                  : 'bg-red-500/5 border-red-500/30'
              }`}>
                <div className={`text-4xl font-bold ${session.is_live ? 'text-green-400' : 'text-red-400'}`}>
                  {session.is_live ? 'LIVE' : 'NOT LIVE'}
                </div>
                <div className="text-sm text-gray-400">
                  {session.results.filter((r) => r.passed).length} of {session.results.length} challenges passed
                </div>
              </div>
            )}

            <button
              onClick={handleDeleteSession}
              className="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm text-gray-400 transition-colors"
            >
              {isCompleted ? 'New Session' : 'Cancel Session'}
            </button>
          </div>

          {/* Right: challenge results */}
          <div className="space-y-4">
            {session.results.length > 0 && (
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
                <h3 className="text-sm font-medium text-gray-400">Challenge Results</h3>
                <div className="space-y-2">
                  {session.results.map((res, i) => (
                    <div key={i} className="flex items-center justify-between bg-gray-800/50 rounded-lg p-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${res.passed ? 'bg-green-500' : 'bg-red-500'}`} />
                        <div>
                          <div className="text-sm font-medium">{session.challenges[i]}</div>
                          <div className="text-xs text-gray-500">Challenge {i + 1}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-bold font-mono ${res.passed ? 'text-green-400' : 'text-red-400'}`}>
                          {res.passed ? 'PASS' : 'FAIL'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {(res.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
