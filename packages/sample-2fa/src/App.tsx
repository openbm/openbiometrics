import { useState } from 'react';
import { LoginScreen } from './screens/LoginScreen.tsx';
import { FaceVerifyScreen } from './screens/FaceVerifyScreen.tsx';
import { EnrollScreen } from './screens/EnrollScreen.tsx';
import { DashboardScreen } from './screens/DashboardScreen.tsx';

type Screen =
  | { type: 'login' }
  | { type: 'enroll' }
  | { type: 'face-verify'; email: string }
  | { type: 'dashboard'; name: string };

export default function App() {
  const [screen, setScreen] = useState<Screen>({ type: 'login' });

  switch (screen.type) {
    case 'login':
      return (
        <LoginScreen
          onLogin={(email) => setScreen({ type: 'face-verify', email })}
          onEnroll={() => setScreen({ type: 'enroll' })}
        />
      );
    case 'enroll':
      return (
        <EnrollScreen
          onDone={() => setScreen({ type: 'login' })}
        />
      );
    case 'face-verify':
      return (
        <FaceVerifyScreen
          email={screen.email}
          onVerified={(name) => setScreen({ type: 'dashboard', name })}
          onCancel={() => setScreen({ type: 'login' })}
        />
      );
    case 'dashboard':
      return (
        <DashboardScreen
          name={screen.name}
          onLogout={() => setScreen({ type: 'login' })}
        />
      );
  }
}
