import { useState } from 'react';
import { GateScreen } from './screens/GateScreen.tsx';
import { VerifyScreen } from './screens/VerifyScreen.tsx';
import { ResultScreen } from './screens/ResultScreen.tsx';

export interface VerificationResult {
  granted: boolean;
  estimatedAge: number | null;
  requiredAge: number;
  gender: 'M' | 'F' | null;
  livenessScore: number | null;
  isLive: boolean | null;
  qualityScore: number | null;
}

type Screen =
  | { type: 'gate' }
  | { type: 'verify'; threshold: number }
  | { type: 'result'; result: VerificationResult };

export default function App() {
  const [screen, setScreen] = useState<Screen>({ type: 'gate' });

  switch (screen.type) {
    case 'gate':
      return (
        <GateScreen
          onVerify={(threshold) => setScreen({ type: 'verify', threshold })}
        />
      );
    case 'verify':
      return (
        <VerifyScreen
          threshold={screen.threshold}
          onResult={(result) => setScreen({ type: 'result', result })}
          onCancel={() => setScreen({ type: 'gate' })}
        />
      );
    case 'result':
      return (
        <ResultScreen
          result={screen.result}
          onRetry={() => setScreen({ type: 'gate' })}
        />
      );
  }
}
