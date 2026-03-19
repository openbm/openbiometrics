import { useState, useEffect, useRef, useCallback } from 'react';
import { useWebcam } from '../useWebcam.ts';
import {
  createLivenessSession,
  submitLivenessFrame,
  identifyFace,
  type LivenessSessionResponse,
  type ChallengeResult,
} from '../api.ts';

const CHALLENGE_LABELS: Record<string, string> = {
  blink: 'Blink',
  turn_left: 'Turn Left',
  turn_right: 'Turn Right',
  look_up: 'Look Up',
  look_down: 'Look Down',
  nod: 'Nod',
  open_mouth: 'Open Mouth',
  smile: 'Smile',
};

function challengeLabel(type: string): string {
  return CHALLENGE_LABELS[type] ?? type.replace(/_/g, ' ');
}

interface Props {
  email: string;
  onVerified: (name: string) => void;
  onCancel: () => void;
}

type Stage =
  | 'starting'
  | 'liveness'
  | 'identifying'
  | 'verified'
  | 'failed';

export function FaceVerifyScreen({ email, onVerified, onCancel }: Props) {
  const { videoRef, ready, error: camError, captureFrame } = useWebcam();
  const [stage, setStage] = useState<Stage>('starting');
  const [session, setSession] = useState<LivenessSessionResponse | null>(null);
  const [challengeResults, setChallengeResults] = useState<ChallengeResult[]>([]);
  const [currentChallengeIdx, setCurrentChallengeIdx] = useState(0);
  const [matchedName, setMatchedName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [similarity, setSimilarity] = useState<number | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [capturing, setCapturing] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [isTiebreaker, setIsTiebreaker] = useState(false);
  const [tiebreakerMessage, setTiebreakerMessage] = useState<string | null>(null);
  const passedCountRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isProcessing = useRef(false);
  const stageRef = useRef<Stage>('starting');

  // Keep stageRef in sync
  useEffect(() => { stageRef.current = stage; }, [stage]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const retry = useCallback(() => {
    stopTimer();
    isProcessing.current = false;
    setStage('starting');
    stageRef.current = 'starting';
    setSession(null);
    setChallengeResults([]);
    setCurrentChallengeIdx(0);
    setMatchedName(null);
    setError(null);
    setSimilarity(null);
    setCapturing(false);
    setFrameCount(0);
    setIsTiebreaker(false);
    setTiebreakerMessage(null);
    passedCountRef.current = 0;
    setAttempt((a) => a + 1);
  }, [stopTimer]);

  // Start liveness session once camera is ready (re-runs on retry via attempt)
  useEffect(() => {
    if (!ready) return;
    let cancelled = false;

    async function start() {
      try {
        const s = await createLivenessSession(2, 15);
        if (!cancelled) {
          setSession(s);
          setStage('liveness');
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to start liveness');
          setStage('failed');
        }
      }
    }

    start();
    return () => { cancelled = true; };
  }, [ready, attempt]);

  const doIdentify = useCallback(async () => {
    setStage('identifying');
    stageRef.current = 'identifying';

    const idFrame = await captureFrame();
    const idResult = await identifyFace(idFrame);

    if (idResult.matches.length > 0 && idResult.matches[0].similarity > 0.4) {
      const name = idResult.matches[0].label;
      setSimilarity(idResult.matches[0].similarity);
      setMatchedName(name);
      setStage('verified');
      stageRef.current = 'verified';
      setTimeout(() => onVerified(name), 2000);
    } else {
      setError('Face not recognized. Make sure you have enrolled your face first.');
      setStage('failed');
      stageRef.current = 'failed';
    }
  }, [captureFrame, onVerified]);

  // Auto-submit frames during liveness
  const handleAutoSubmit = useCallback(async (currentSession: LivenessSessionResponse) => {
    if (isProcessing.current) return;
    if (stageRef.current !== 'liveness') return;

    isProcessing.current = true;
    try {
      // Flash indicator
      setCapturing(true);
      setFrameCount((c) => c + 1);
      const frame = await captureFrame();
      setTimeout(() => setCapturing(false), 300);
      const result = await submitLivenessFrame(currentSession.session_id, frame);

      const isTerminal = result.session_complete || result.state === 'failed' || result.state === 'expired' || result.state === 'completed';

      // Track passes
      if (result.passed) {
        passedCountRef.current += 1;
      }

      // Only record the result when the challenge actually resolved (passed or terminal)
      if (result.passed || isTerminal) {
        setChallengeResults((prev) => {
          const idx = currentSession.challenges.length - result.challenges_remaining - (result.passed ? 1 : 0);
          if (prev.length <= idx) return [...prev, result];
          return prev;
        });
      }

      // Update current challenge index from API response
      const completedCount = currentSession.challenges.length - result.challenges_remaining;
      setCurrentChallengeIdx(completedCount);

      if (isTerminal) {
        stopTimer();

        if (result.is_live) {
          // All challenges passed — identify
          await doIdentify();
        } else if (!isTiebreaker && passedCountRef.current > 0) {
          // Score is 1/2 — automatic tiebreaker
          setTiebreakerMessage(`Passed ${passedCountRef.current} of ${currentSession.challenges.length} — starting tiebreaker challenge...`);
          setFrameCount(0);

          // Brief pause so user sees the message
          await new Promise((r) => setTimeout(r, 2000));

          try {
            const tieSession = await createLivenessSession(1, 15);
            setSession(tieSession);
            setChallengeResults([]);
            setCurrentChallengeIdx(0);
            setIsTiebreaker(true);
            passedCountRef.current = 0;
            // Stage stays 'liveness' — the interval effect will restart
          } catch {
            setError('Failed to start tiebreaker. Please try again.');
            setStage('failed');
            stageRef.current = 'failed';
          }
        } else {
          const reason = result.state === 'expired'
            ? 'Session expired. Please try again.'
            : isTiebreaker
            ? 'Tiebreaker failed. Liveness could not be verified.'
            : 'Liveness check failed. Please try again — look at the camera and follow the instructions.';
          setError(reason);
          setStage('failed');
          stageRef.current = 'failed';
        }
      }
    } catch (e) {
      // Ignore errors if we already moved past liveness
      if (stageRef.current === 'liveness') {
        setError(e instanceof Error ? e.message : 'Verification error');
        setStage('failed');
        stageRef.current = 'failed';
        stopTimer();
      }
    } finally {
      isProcessing.current = false;
    }
  }, [captureFrame, doIdentify, stopTimer, isTiebreaker]);

  // Set up auto-submit interval with initial delay so user can read the instruction
  useEffect(() => {
    if (stage !== 'liveness' || !session) return;

    const initialDelay = setTimeout(() => {
      // Submit first frame after 2s, then every 3s
      handleAutoSubmit(session);
      timerRef.current = setInterval(() => {
        handleAutoSubmit(session);
      }, 3000);
    }, 2000);

    return () => {
      clearTimeout(initialDelay);
      stopTimer();
    };
  }, [stage, session, handleAutoSubmit, stopTimer]);

  const currentChallenge = session && currentChallengeIdx < session.challenges.length
    ? session.challenges[currentChallengeIdx]
    : null;

  const totalChallenges = session?.challenges.length ?? 0;
  const progress = totalChallenges > 0 ? challengeResults.length / totalChallenges : 0;

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">Face Verification</h1>
          <p className="text-gray-400 text-sm mt-1">
            2nd factor for <span className="text-indigo-400">{email}</span>
          </p>
        </div>

        <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
          {(stage === 'verified' || stage === 'identifying') ? (
            <div className="aspect-video bg-gray-950 flex items-center justify-center">
              {stage === 'identifying' ? (
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
                  <div className="text-indigo-400 text-sm">Identifying face...</div>
                </div>
              ) : (
                <div className="text-center space-y-2">
                  <div className="text-5xl font-bold text-green-400">Welcome!</div>
                  <div className="text-2xl text-white">{matchedName}</div>
                  {similarity !== null && (
                    <div className="text-sm text-green-300 mt-2">
                      Match confidence: {(similarity * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="relative aspect-video bg-black">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
                style={{ transform: 'scaleX(-1)' }}
              />

              {!ready && !camError && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                  <div className="text-gray-400 text-sm animate-pulse">Starting camera...</div>
                </div>
              )}

              {camError && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                  <div className="text-red-400 text-sm text-center px-4">{camError}</div>
                </div>
              )}

              {/* Face guide overlay */}
              {ready && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-48 h-60 rounded-[50%] border-2 border-indigo-400/60 animate-pulse transition-colors duration-300" />
                </div>
              )}

              {/* Capture flash */}
              {capturing && (
                <div className="absolute inset-0 bg-white/20 pointer-events-none animate-[flash_0.3s_ease-out]" />
              )}

              {/* Frame counter */}
              {stage === 'liveness' && frameCount > 0 && (
                <div className="absolute top-3 right-3 bg-black/60 backdrop-blur-sm rounded-full px-2.5 py-1 flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-xs text-gray-300 font-mono">Frame {frameCount}</span>
                </div>
              )}

              {/* Progress bar at bottom */}
              {session && stage === 'liveness' && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-800">
                  <div
                    className="h-full bg-indigo-500 transition-all duration-500"
                    style={{ width: `${progress * 100}%` }}
                  />
                </div>
              )}
            </div>
          )}

          <div className="p-5 space-y-4">
            {tiebreakerMessage && stage === 'liveness' && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 text-yellow-400 text-sm text-center">
                {tiebreakerMessage}
              </div>
            )}

            {stage === 'starting' && (
              <div className="text-center space-y-2">
                <div className="text-gray-400 text-sm animate-pulse">
                  Initializing liveness check...
                </div>
                <div className="text-xs text-gray-500">
                  You will need to pass {session?.challenges.length ?? 2} challenges to verify you are a real person.
                </div>
              </div>
            )}

            {stage === 'liveness' && currentChallenge && (
              <div className="text-center space-y-2">
                <div className="text-xs text-indigo-400 uppercase tracking-wider">
                  Challenge {currentChallengeIdx + 1} of {totalChallenges}
                </div>
                <div className="text-lg font-semibold text-white">
                  {currentChallenge.instruction}
                </div>
                <div className="text-xs text-gray-500">
                  Complete all {totalChallenges} challenges to prove you are a live person. Frames are captured automatically.
                </div>
              </div>
            )}

            {stage === 'identifying' && (
              <div className="text-center text-yellow-400 text-sm animate-pulse">
                Liveness passed! Identifying face...
              </div>
            )}

            {stage === 'verified' && (
              <div className="text-center text-green-400 text-sm">
                Redirecting to dashboard...
              </div>
            )}

            {/* Challenge progress */}
            {session && session.challenges.length > 0 && (
              <div className="flex justify-center gap-4">
                {session.challenges.map((c, i) => {
                  const isDone = i < challengeResults.length;
                  const passed = isDone && challengeResults[i].passed;
                  const isCurrent = i === currentChallengeIdx && stage === 'liveness';
                  return (
                    <div key={i} className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full transition-colors ${
                        isDone
                          ? passed ? 'bg-green-500' : 'bg-red-500'
                          : isCurrent ? 'bg-indigo-500 animate-pulse' : 'bg-gray-700'
                      }`} />
                      <span className={`text-xs ${
                        isDone
                          ? passed ? 'text-green-400' : 'text-red-400'
                          : isCurrent ? 'text-indigo-400' : 'text-gray-600'
                      }`}>
                        {challengeLabel(c.type)}{isDone ? (passed ? ' — passed' : ' — failed') : ''}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            {(stage === 'failed' || camError) && (
              <div className="flex gap-3">
                <button
                  onClick={onCancel}
                  className="flex-1 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg font-medium transition-colors border border-gray-700"
                >
                  Back to Login
                </button>
                <button
                  onClick={retry}
                  className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </div>

        <p className="text-center text-xs text-gray-600">
          Powered by <span className="text-indigo-400">OpenBiometrics</span>
        </p>
      </div>
    </div>
  );
}
