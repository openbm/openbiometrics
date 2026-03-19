import { useState } from 'react';

const AGE_OPTIONS = [18, 21, 25] as const;

export function GateScreen({ onVerify }: { onVerify: (threshold: number) => void }) {
  const [threshold, setThreshold] = useState(21);

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-950 via-neutral-900 to-neutral-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-8">
        {/* Icon */}
        <div className="text-6xl">🍷</div>

        {/* Heading */}
        <div className="space-y-3">
          <h1 className="text-3xl font-bold text-amber-400 tracking-tight">
            Age Verification Required
          </h1>
          <p className="text-neutral-400 text-lg">
            You must be at least <span className="text-amber-300 font-semibold">{threshold} years old</span> to access this content.
          </p>
        </div>

        {/* Divider */}
        <div className="border-t border-amber-900/40" />

        {/* Age threshold selector */}
        <div className="space-y-2">
          <label className="text-sm text-neutral-500 uppercase tracking-widest">
            Age Requirement
          </label>
          <div className="flex justify-center gap-2">
            {AGE_OPTIONS.map((age) => (
              <button
                key={age}
                onClick={() => setThreshold(age)}
                className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
                  threshold === age
                    ? 'bg-amber-500 text-black'
                    : 'bg-neutral-800 text-neutral-400 hover:bg-neutral-700 hover:text-neutral-300'
                }`}
              >
                {age}+
              </button>
            ))}
          </div>
        </div>

        {/* Verify button */}
        <button
          onClick={() => onVerify(threshold)}
          className="w-full py-4 bg-amber-500 hover:bg-amber-400 text-black font-bold text-lg rounded-xl transition-colors shadow-lg shadow-amber-500/20"
        >
          Verify My Age
        </button>

        {/* Disclaimer */}
        <p className="text-xs text-neutral-600 leading-relaxed">
          We use AI-powered age estimation to verify your age.
          A single selfie is analyzed in real-time. No data is stored.
        </p>
      </div>
    </div>
  );
}
