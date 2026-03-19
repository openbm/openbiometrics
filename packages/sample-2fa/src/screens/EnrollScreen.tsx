import { useState, type FormEvent } from 'react';
import { useWebcam } from '../useWebcam.ts';
import { detectFaces, enrollFace } from '../api.ts';

interface Props {
  onDone: () => void;
}

export function EnrollScreen({ onDone }: Props) {
  const { videoRef, ready, error: camError, captureFrame } = useWebcam();
  const [name, setName] = useState('');
  const [status, setStatus] = useState<'idle' | 'capturing' | 'enrolling' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  async function handleEnroll(e: FormEvent) {
    e.preventDefault();
    if (!ready || !name.trim()) return;

    setStatus('capturing');
    setMessage('Capturing frame...');

    try {
      const frame = await captureFrame();

      // First detect to make sure there's a valid face
      setMessage('Detecting face...');
      const detection = await detectFaces(frame);
      if (detection.count === 0) {
        setStatus('error');
        setMessage('No face detected. Please look at the camera and try again.');
        return;
      }
      if (detection.count > 1) {
        setStatus('error');
        setMessage('Multiple faces detected. Please ensure only you are in frame.');
        return;
      }
      if (detection.faces[0].quality && !detection.faces[0].quality.is_acceptable) {
        setStatus('error');
        setMessage(`Face quality too low: ${detection.faces[0].quality.reasons.join(', ')}`);
        return;
      }

      // Enroll face into the watchlist
      setStatus('enrolling');
      setMessage('Enrolling face...');
      await enrollFace(frame, name.trim());

      setStatus('success');
      setMessage(`Face enrolled for "${name.trim()}". You can now sign in!`);
    } catch (err) {
      setStatus('error');
      setMessage(err instanceof Error ? err.message : 'Enrollment failed');
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">Enroll Your Face</h1>
          <p className="text-gray-400 text-sm mt-1">
            Register your face for 2nd factor authentication
          </p>
        </div>

        <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
          <div className="relative aspect-video bg-black flex items-center justify-center">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover mirror"
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
            {ready && (
              <div className="absolute inset-8 border-2 border-indigo-500/30 rounded-xl pointer-events-none" />
            )}
          </div>

          <form onSubmit={handleEnroll} className="p-5 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Your Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. John Smith"
                required
                className="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            {message && (
              <div
                className={`text-sm rounded-lg p-3 ${
                  status === 'success'
                    ? 'bg-green-500/10 border border-green-500/30 text-green-400'
                    : status === 'error'
                    ? 'bg-red-500/10 border border-red-500/30 text-red-400'
                    : 'bg-indigo-500/10 border border-indigo-500/30 text-indigo-400'
                }`}
              >
                {message}
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={onDone}
                className="flex-1 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg font-medium transition-colors border border-gray-700"
              >
                Back to Login
              </button>
              {status === 'success' ? (
                <button
                  type="button"
                  onClick={onDone}
                  className="flex-1 py-2.5 bg-green-600 hover:bg-green-500 text-white rounded-lg font-medium transition-colors"
                >
                  Sign In Now
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!ready || !name.trim() || status === 'capturing' || status === 'enrolling'}
                  className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg font-medium transition-colors"
                >
                  {status === 'capturing' || status === 'enrolling' ? 'Processing...' : 'Capture & Enroll'}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
