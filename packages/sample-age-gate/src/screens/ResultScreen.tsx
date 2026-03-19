import type { VerificationResult } from '../App.tsx';

interface Props {
  result: VerificationResult;
  onRetry: () => void;
}

export function ResultScreen({ result, onRetry }: Props) {
  const { granted, estimatedAge, requiredAge, gender, livenessScore, isLive, qualityScore } = result;
  const livenessFailure = isLive === false;

  return (
    <div
      className={`min-h-screen flex items-center justify-center p-4 ${
        granted
          ? 'bg-gradient-to-b from-green-950 via-neutral-950 to-neutral-950'
          : 'bg-gradient-to-b from-red-950 via-neutral-950 to-neutral-950'
      }`}
    >
      <div className="max-w-md w-full text-center space-y-8">
        {/* Status icon */}
        <div className="text-7xl">
          {granted ? '✅' : '🚫'}
        </div>

        {/* Status message */}
        <div className="space-y-3">
          {granted ? (
            <>
              <h1 className="text-3xl font-bold text-green-400">
                Access Granted
              </h1>
              <p className="text-neutral-400 text-lg">
                Welcome! Age verified:{' '}
                <span className="text-green-300 font-semibold">
                  {estimatedAge != null ? Math.round(estimatedAge) : '?'}
                </span>
              </p>
            </>
          ) : (
            <>
              <h1 className="text-3xl font-bold text-red-400">
                Access Denied
              </h1>
              {livenessFailure ? (
                <p className="text-neutral-400 text-lg">
                  Liveness check failed — please try again with a real, live face.
                </p>
              ) : (
                <p className="text-neutral-400 text-lg">
                  Sorry, you don't meet the age requirement.
                  {estimatedAge != null && (
                    <>
                      {' '}Estimated age{' '}
                      <span className="text-red-300 font-semibold">
                        {Math.round(estimatedAge)}
                      </span>
                      {' '}vs required{' '}
                      <span className="text-amber-300 font-semibold">
                        {requiredAge}+
                      </span>
                    </>
                  )}
                </p>
              )}
            </>
          )}
        </div>

        {/* Details card */}
        <div className="bg-neutral-900/80 border border-neutral-800 rounded-2xl p-6 space-y-4 text-left">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-widest">
            Verification Details
          </h3>

          <div className="space-y-3">
            <DetailRow
              label="Estimated Age"
              value={estimatedAge != null ? String(Math.round(estimatedAge)) : 'N/A'}
              accent={granted ? 'text-green-400' : 'text-red-400'}
            />
            <DetailRow
              label="Required Age"
              value={`${requiredAge}+`}
              accent="text-amber-400"
            />
            <DetailRow
              label="Gender"
              value={gender === 'M' ? 'Male' : gender === 'F' ? 'Female' : 'N/A'}
              accent="text-neutral-300"
            />
            <DetailRow
              label="Liveness"
              value={
                isLive === true
                  ? 'Live'
                  : isLive === false
                    ? 'Spoof Detected'
                    : 'Not Available'
              }
              accent={
                isLive === true
                  ? 'text-green-400'
                  : isLive === false
                    ? 'text-red-400'
                    : 'text-neutral-500'
              }
            />
            {livenessScore != null && (
              <DetailRow
                label="Liveness Score"
                value={`${(livenessScore * 100).toFixed(1)}%`}
                accent="text-neutral-300"
              />
            )}
            {qualityScore != null && (
              <DetailRow
                label="Quality Score"
                value={`${(qualityScore * 100).toFixed(1)}%`}
                accent="text-neutral-300"
              />
            )}
          </div>
        </div>

        {/* Try again */}
        <button
          onClick={onRetry}
          className="w-full py-4 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 font-bold text-lg rounded-xl transition-colors"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}

function DetailRow({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-neutral-500 text-sm">{label}</span>
      <span className={`font-semibold ${accent}`}>{value}</span>
    </div>
  );
}
