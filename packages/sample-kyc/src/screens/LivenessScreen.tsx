import { useState, useEffect, useRef } from 'react';
import { useWebcam } from '../useWebcam.ts';
import { createLivenessSession, submitLivenessFrame } from '../api.ts';
import type { Challenge, ChallengeResult } from '../api.ts';
import type { KycData } from '../App.tsx';

interface Props {
  data: KycData;
  onUpdate: (partial: Partial<KycData>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function LivenessScreen({ data: _data, onUpdate, onNext, onBack }: Props) {
  const { videoRef, ready, error: camError, captureFrame } = useWebcam();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [results, setResults] = useState<ChallengeResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionComplete, setSessionComplete] = useState(false);
  const initRef = useRef(false);

  // Create session on mount
  useEffect(() => {
    if (initRef.current) return;
    initRef.current = true;

    async function init() {
      try {
        const session = await createLivenessSession(2);
        setSessionId(session.session_id);
        setChallenges(session.challenges);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create liveness session');
      }
    }
    init();
  }, []);

  const currentChallenge = challenges[currentIdx] ?? null;
  const allPassed = results.length > 0 && results.every((r) => r.passed);

  const handleSubmit = async () => {
    if (!sessionId) return;
    setError(null);
    setLoading(true);
    try {
      const blob = await captureFrame();
      const result = await submitLivenessFrame(sessionId, blob);
      setResults((prev) => [...prev, result]);

      if (result.session_complete) {
        setSessionComplete(true);
        const passed = result.is_live === true;
        onUpdate({
          livenessPass: passed,
          challengesCompleted: challenges.length - result.challenges_remaining,
          challengesTotal: challenges.length,
        });
      } else {
        setCurrentIdx((prev) => prev + 1);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-slate-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex gap-1">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`w-8 h-1 rounded-full ${s <= 3 ? 'bg-indigo-600' : 'bg-slate-200'}`}
              />
            ))}
          </div>
          <span className="text-xs text-slate-500 font-medium">Step 3/3</span>
          <h1 className="text-lg font-bold text-slate-800 ml-auto">Liveness Check</h1>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-6">
          {/* Challenge instruction */}
          {currentChallenge && !sessionComplete && (
            <div className="text-center mb-4">
              <p className="text-2xl font-bold text-indigo-700">{currentChallenge.instruction}</p>
              <p className="text-sm text-slate-500 mt-1">
                Challenge {currentIdx + 1} of {challenges.length}
              </p>
            </div>
          )}

          {sessionComplete && (
            <div className="text-center mb-4">
              <p className="text-2xl font-bold text-emerald-600">
                {allPassed ? 'Liveness Confirmed' : 'Check Complete'}
              </p>
            </div>
          )}

          {/* Webcam */}
          <div className="relative rounded-xl overflow-hidden bg-slate-900 aspect-[4/3]">
            <video ref={videoRef} className="w-full h-full object-cover" muted playsInline />
            {!ready && !camError && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Spinner />
              </div>
            )}
          </div>

          {/* Camera error */}
          {camError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              Camera error: {camError}
            </div>
          )}

          {/* Progress dots */}
          {challenges.length > 0 && (
            <div className="flex items-center justify-center gap-3 mt-4">
              {challenges.map((_, i) => {
                const result = results[i];
                let classes = 'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ';
                if (result) {
                  classes += result.passed
                    ? 'bg-emerald-100 text-emerald-600'
                    : 'bg-red-100 text-red-600';
                } else if (i === currentIdx && !sessionComplete) {
                  classes += 'bg-indigo-100 text-indigo-600 ring-2 ring-indigo-400';
                } else {
                  classes += 'bg-slate-100 text-slate-400';
                }
                return (
                  <div key={i} className={classes}>
                    {result ? (result.passed ? '\u2713' : '\u2717') : i + 1}
                  </div>
                );
              })}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="mt-6 space-y-3">
            {!sessionComplete && sessionId && (
              <button
                onClick={handleSubmit}
                disabled={!ready || loading}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors cursor-pointer"
              >
                {loading ? 'Submitting...' : 'Capture & Submit'}
              </button>
            )}
          </div>

          {/* Navigation */}
          <div className="flex justify-between mt-6">
            <button
              onClick={onBack}
              className="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
            >
              Back
            </button>
            {sessionComplete && (
              <button
                onClick={onNext}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors text-sm cursor-pointer"
              >
                View Results
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin h-8 w-8 text-white/60" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}
