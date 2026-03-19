import { useState } from 'react';
import { WelcomeScreen } from './screens/WelcomeScreen.tsx';
import { DocumentScanScreen } from './screens/DocumentScanScreen.tsx';
import { SelfieScreen } from './screens/SelfieScreen.tsx';
import { LivenessScreen } from './screens/LivenessScreen.tsx';
import { ResultScreen } from './screens/ResultScreen.tsx';
import type { DocumentScanResponse, DetectResponse, VerifyResponse } from './api.ts';

export interface KycData {
  documentImage: Blob | null;
  documentScan: DocumentScanResponse | null;
  selfieImage: Blob | null;
  selfieDetect: DetectResponse | null;
  livenessPass: boolean;
  challengesCompleted: number;
  challengesTotal: number;
  verification: VerifyResponse | null;
}

const initialData: KycData = {
  documentImage: null,
  documentScan: null,
  selfieImage: null,
  selfieDetect: null,
  livenessPass: false,
  challengesCompleted: 0,
  challengesTotal: 0,
  verification: null,
};

type Screen = 'welcome' | 'document' | 'selfie' | 'liveness' | 'result';

export default function App() {
  const [screen, setScreen] = useState<Screen>('welcome');
  const [data, setData] = useState<KycData>(initialData);

  const update = (partial: Partial<KycData>) =>
    setData((prev) => ({ ...prev, ...partial }));

  const restart = () => {
    setData(initialData);
    setScreen('welcome');
  };

  switch (screen) {
    case 'welcome':
      return <WelcomeScreen onStart={() => setScreen('document')} />;
    case 'document':
      return (
        <DocumentScanScreen
          data={data}
          onUpdate={update}
          onNext={() => setScreen('selfie')}
          onBack={() => setScreen('welcome')}
        />
      );
    case 'selfie':
      return (
        <SelfieScreen
          data={data}
          onUpdate={update}
          onNext={() => setScreen('liveness')}
          onBack={() => setScreen('document')}
        />
      );
    case 'liveness':
      return (
        <LivenessScreen
          data={data}
          onUpdate={update}
          onNext={() => setScreen('result')}
          onBack={() => setScreen('selfie')}
        />
      );
    case 'result':
      return <ResultScreen data={data} onRestart={restart} />;
  }
}
