import { useState } from 'react';
import { useWebcam } from '../useWebcam.ts';
import { detectFaces } from '../api.ts';
import type { KycData } from '../App.tsx';

interface Props {
  data: KycData;
  onUpdate: (partial: Partial<KycData>) => void;
  onNext: () => void;
  onBack: () => void;
}

export function SelfieScreen({ data, onUpdate, onNext, onBack }: Props) {
  const { videoRef, ready, error: camError, captureFrame } = useWebcam();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [capturedUrl, setCapturedUrl] = useState<string | null>(null);
  const [qualityWarning, setQualityWarning] = useState<string | null>(null);

  const selfieOk = data.selfieDetect !== null && data.selfieDetect.count > 0;
  const quality = data.selfieDetect?.faces[0]?.quality;

  const handleCapture = async () => {
    setError(null);
    setQualityWarning(null);
    setLoading(true);
    try {
      const blob = await captureFrame();
      const result = await detectFaces(blob);

      if (result.count === 0) {
        setError('No face detected. Please position your face in the center of the frame.');
        setLoading(false);
        return;
      }

      const q = result.faces[0].quality;
      if (q && !q.is_acceptable) {
        setQualityWarning(
          `Quality too low (${(q.overall_score * 100).toFixed(0)}%). ${q.reasons.join(', ')}. Please try again.`,
        );
        setLoading(false);
        return;
      }

      onUpdate({ selfieImage: blob, selfieDetect: result });
      setCapturedUrl(URL.createObjectURL(blob));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Capture failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    onUpdate({ selfieImage: null, selfieDetect: null });
    setCapturedUrl(null);
    setQualityWarning(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-slate-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        {/* Header */}
        <StepHeader />

        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-6">
          {/* Webcam / Captured */}
          <div className="relative rounded-xl overflow-hidden bg-slate-900 aspect-[4/3]">
            {capturedUrl ? (
              <img
                src={capturedUrl}
                alt="Selfie"
                className={`w-full h-full object-cover ${selfieOk ? 'ring-4 ring-emerald-400 rounded-xl' : ''}`}
              />
            ) : (
              <>
                <video
                  ref={videoRef}
                  className="w-full h-full object-cover"
                  muted
                  playsInline
                />
                {!ready && !camError && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Spinner />
                  </div>
                )}
              </>
            )}

            {/* Face oval guide when camera is active */}
            {!capturedUrl && ready && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-48 h-64 border-2 border-white/40 rounded-full" />
              </div>
            )}
          </div>

          {/* Camera error */}
          {camError && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              Camera error: {camError}
            </div>
          )}

          {/* Quality indicators */}
          {selfieOk && quality && (
            <div className="mt-4 flex flex-wrap gap-2">
              <QualityBadge
                ok={true}
                label={`Face Detected`}
              />
              <QualityBadge
                ok={quality.is_acceptable}
                label={`Quality: ${(quality.overall_score * 100).toFixed(0)}%`}
              />
              <QualityBadge
                ok={quality.head_pose_ok}
                label={quality.head_pose_ok ? 'Head Pose OK' : 'Head Pose Off'}
              />
            </div>
          )}

          {/* Warnings */}
          {qualityWarning && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
              {qualityWarning}
            </div>
          )}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Buttons */}
          <div className="mt-6 space-y-3">
            {!capturedUrl ? (
              <button
                onClick={handleCapture}
                disabled={!ready || loading}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors cursor-pointer"
              >
                {loading ? 'Analyzing...' : 'Capture Selfie'}
              </button>
            ) : !selfieOk ? (
              <button
                onClick={handleRetry}
                className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-xl transition-colors cursor-pointer"
              >
                Retry
              </button>
            ) : null}
          </div>

          {/* Navigation */}
          <div className="flex justify-between mt-6">
            <button
              onClick={onBack}
              className="px-5 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 transition-colors cursor-pointer"
            >
              Back
            </button>
            {selfieOk && capturedUrl && (
              <button
                onClick={onNext}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors text-sm cursor-pointer"
              >
                Continue to Liveness
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StepHeader() {
  return (
    <div className="mb-4 flex items-center gap-3">
      <div className="flex gap-1">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`w-8 h-1 rounded-full ${s <= 2 ? 'bg-indigo-600' : 'bg-slate-200'}`}
          />
        ))}
      </div>
      <span className="text-xs text-slate-500 font-medium">Step 2/3</span>
      <h1 className="text-lg font-bold text-slate-800 ml-auto">Take a Selfie</h1>
    </div>
  );
}

function QualityBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
        ok ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
      }`}
    >
      {ok ? '\u2713' : '!'} {label}
    </span>
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
