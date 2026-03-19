interface Props {
  onStart: () => void;
}

export function WelcomeScreen({ onStart }: Props) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-slate-50 flex items-center justify-center p-4">
      <div className="max-w-lg w-full text-center">
        {/* Logo */}
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-indigo-600 text-white text-4xl mb-4 shadow-lg">
            <span role="img" aria-label="bank">&#x1F3E6;</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">SecureBank</h1>
          <p className="text-slate-500 mt-1 text-sm">Digital Identity Verification</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-2">
            Verify your identity in 3 simple steps
          </h2>
          <p className="text-slate-500 text-sm mb-8">
            Complete the verification process to activate your account.
          </p>

          {/* Steps */}
          <div className="space-y-4 mb-8 text-left">
            <StepPreview
              number={1}
              title="Scan ID Document"
              desc="Upload your passport or ID card"
            />
            <StepPreview
              number={2}
              title="Take a Selfie"
              desc="Capture a live photo of your face"
            />
            <StepPreview
              number={3}
              title="Liveness Check"
              desc="Prove you are a real person"
            />
          </div>

          <button
            onClick={onStart}
            className="w-full py-3 px-6 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors shadow-md cursor-pointer"
          >
            Begin Verification
          </button>
        </div>

        <p className="text-xs text-slate-400 mt-6">
          Powered by OpenBiometrics
        </p>
      </div>
    </div>
  );
}

function StepPreview({ number, title, desc }: { number: number; title: string; desc: string }) {
  return (
    <div className="flex items-start gap-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-bold">
        {number}
      </div>
      <div>
        <p className="font-medium text-slate-800 text-sm">{title}</p>
        <p className="text-slate-500 text-xs">{desc}</p>
      </div>
    </div>
  );
}
