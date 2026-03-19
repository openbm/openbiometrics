import { useState, useEffect, useRef, useCallback } from 'react';
import { useWebcam } from '../useWebcam.ts';
import { detectFaces } from '../api.ts';
import type { FaceResponse } from '../api.ts';
import type { VerificationResult } from '../App.tsx';

interface Props {
  threshold: number;
  onResult: (result: VerificationResult) => void;
  onCancel: () => void;
}

export function VerifyScreen({ threshold, onResult, onCancel }: Props) {
  const { videoRef, ready, error, captureFrame } = useWebcam();
  const [face, setFace] = useState<FaceResponse | null>(null);
  const [verifying, setVerifying] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-detect faces every 2 seconds
  const autoDetect = useCallback(async () => {
    if (!ready || verifying) return;
    try {
      const blob = await captureFrame();
      const res = await detectFaces(blob);
      if (res.count > 0) {
        setFace(res.faces[0]);
      } else {
        setFace(null);
      }
    } catch {
      // Silently ignore auto-detect errors
    }
  }, [ready, verifying, captureFrame]);

  useEffect(() => {
    if (!ready) return;
    // Run immediately, then every 2s
    autoDetect();
    intervalRef.current = setInterval(autoDetect, 2000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [ready, autoDetect]);

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const blob = await captureFrame();
      const res = await detectFaces(blob);

      if (res.count === 0) {
        setVerifying(false);
        setFace(null);
        return;
      }

      const f = res.faces[0];
      const age = f.demographics?.age ?? null;
      const isLive = f.liveness?.is_live ?? null;
      const livenessPass = isLive === true || isLive === null; // null = liveness not available, allow
      const agePass = age !== null && age >= threshold;

      onResult({
        granted: agePass && livenessPass,
        estimatedAge: age,
        requiredAge: threshold,
        gender: f.demographics?.gender ?? null,
        livenessScore: f.liveness?.score ?? null,
        isLive,
        qualityScore: f.quality?.overall_score ?? null,
      });
    } catch {
      setVerifying(false);
    }
  };

  const age = face?.demographics?.age;
  const gender = face?.demographics?.gender;
  const isLive = face?.liveness?.is_live;
  const livenessScore = face?.liveness?.score;
  const qualityScore = face?.quality?.overall_score;
  const isAcceptable = face?.quality?.is_acceptable;
  const canVerify = face !== null && isAcceptable !== false;

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-900 to-neutral-950 flex flex-col items-center justify-center p-4">
      <div className="max-w-lg w-full space-y-6">
        {/* Header */}
        <div className="text-center space-y-1">
          <h2 className="text-xl font-bold text-amber-400">
            Age Verification
          </h2>
          <p className="text-neutral-500 text-sm">
            Position your face in the frame
          </p>
        </div>

        {/* Webcam area */}
        <div className="relative aspect-[4/3] bg-black rounded-2xl overflow-hidden shadow-2xl border border-neutral-800">
          {error ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6">
              <div className="text-4xl">📷</div>
              <p className="text-red-400 text-center font-medium">
                Camera Access Denied
              </p>
              <p className="text-neutral-500 text-sm text-center">
                Please allow camera access in your browser settings to continue.
              </p>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                className="w-full h-full object-cover mirror"
                style={{ transform: 'scaleX(-1)' }}
                muted
                playsInline
              />

              {/* Oval face guide */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div
                  className={`w-48 h-64 rounded-full border-2 border-dashed transition-colors ${
                    face ? 'border-amber-400/60' : 'border-neutral-500/40'
                  }`}
                />
              </div>

              {/* Real-time overlay */}
              {face && (
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-4 pt-10">
                  <div className="flex items-end justify-between gap-4">
                    {/* Age (large) */}
                    <div className="flex items-baseline gap-2">
                      {age != null && (
                        <>
                          <span className="text-4xl font-black text-white tabular-nums">
                            {Math.round(age)}
                          </span>
                          <span className="text-sm text-neutral-400">
                            est. age
                          </span>
                        </>
                      )}
                    </div>

                    {/* Details */}
                    <div className="flex flex-col items-end gap-1.5 text-sm">
                      {gender && (
                        <span className="text-neutral-300">
                          {gender === 'M' ? 'Male' : 'Female'}
                        </span>
                      )}

                      {/* Liveness */}
                      <span
                        className={`flex items-center gap-1.5 font-medium ${
                          isLive === true
                            ? 'text-green-400'
                            : isLive === false
                              ? 'text-red-400'
                              : 'text-neutral-500'
                        }`}
                      >
                        <span
                          className={`w-2 h-2 rounded-full ${
                            isLive === true
                              ? 'bg-green-400'
                              : isLive === false
                                ? 'bg-red-400'
                                : 'bg-neutral-500'
                          }`}
                        />
                        {isLive === true
                          ? 'Live'
                          : isLive === false
                            ? 'Spoof'
                            : 'Checking...'}
                        {livenessScore != null && (
                          <span className="text-neutral-500 text-xs">
                            ({(livenessScore * 100).toFixed(0)}%)
                          </span>
                        )}
                      </span>

                      {/* Quality bar */}
                      {qualityScore != null && (
                        <div className="flex items-center gap-2">
                          <span className="text-neutral-500 text-xs">Quality</span>
                          <div className="w-16 h-1.5 bg-neutral-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                qualityScore > 0.6
                                  ? 'bg-green-400'
                                  : qualityScore > 0.3
                                    ? 'bg-amber-400'
                                    : 'bg-red-400'
                              }`}
                              style={{ width: `${qualityScore * 100}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Loading state for webcam */}
              {!ready && !error && (
                <div className="absolute inset-0 flex items-center justify-center bg-neutral-900">
                  <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 py-3 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 font-medium rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleVerify}
            disabled={!canVerify || verifying}
            className="flex-1 py-3 bg-amber-500 hover:bg-amber-400 disabled:bg-neutral-700 disabled:text-neutral-500 text-black font-bold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {verifying ? (
              <>
                <div className="w-4 h-4 border-2 border-black/40 border-t-black rounded-full animate-spin" />
                Verifying...
              </>
            ) : (
              'Verify'
            )}
          </button>
        </div>

        {/* Requirement reminder */}
        <p className="text-center text-neutral-600 text-xs">
          Required age: {threshold}+ &middot; Liveness check enabled
        </p>
      </div>
    </div>
  );
}
