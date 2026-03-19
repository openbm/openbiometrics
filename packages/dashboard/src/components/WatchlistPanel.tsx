import { useEffect, useState } from 'react';
import { enrollFace, identifyFace, listWatchlists, type IdentifyResponse } from '../api';
import { ImageDropZone } from './ImageDropZone';

export function WatchlistPanel() {
  const [mode, setMode] = useState<'enroll' | 'identify'>('enroll');
  const [watchlists, setWatchlists] = useState<{ name: string; size: number }[]>([]);

  useEffect(() => {
    listWatchlists().then((r) => setWatchlists(r.watchlists)).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">1:N Watchlist</h2>
        <p className="text-gray-400 text-sm">
          Enroll faces into a watchlist, then search for matches.
        </p>
      </div>

      <div className="flex gap-4 items-center">
        <div className="flex bg-gray-900 rounded-lg p-1 border border-gray-800">
          <button
            onClick={() => setMode('enroll')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              mode === 'enroll' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            Enroll
          </button>
          <button
            onClick={() => setMode('identify')}
            className={`px-4 py-2 text-sm rounded-md transition-colors ${
              mode === 'identify' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            Identify
          </button>
        </div>

        <div className="text-sm text-gray-500">
          {watchlists.map((wl) => (
            <span key={wl.name} className="bg-gray-800 px-3 py-1 rounded-full mr-2">
              {wl.name}: {wl.size} faces
            </span>
          ))}
        </div>
      </div>

      {mode === 'enroll' ? (
        <EnrollSection onEnrolled={() => listWatchlists().then((r) => setWatchlists(r.watchlists))} />
      ) : (
        <IdentifySection />
      )}
    </div>
  );
}

function EnrollSection({ onEnrolled }: { onEnrolled: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [label, setLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEnroll = async () => {
    if (!file || !label.trim()) return;
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await enrollFace(file, label.trim());
      setSuccess(`Enrolled "${label.trim()}" successfully`);
      setLabel('');
      setFile(null);
      setPreview(null);
      onEnrolled();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Enrollment failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-4">
        <ImageDropZone
          onImage={(f, p) => { setFile(f); setPreview(p); setSuccess(null); }}
          preview={preview}
          label="Drop face image to enroll"
        />
      </div>
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Name / Label</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g. John Doe"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
        <button
          onClick={handleEnroll}
          disabled={!file || !label.trim() || loading}
          className="w-full px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-medium transition-colors"
        >
          {loading ? 'Enrolling...' : 'Enroll Face'}
        </button>

        {success && (
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-green-400 text-sm">
            {success}
          </div>
        )}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

function IdentifySection() {
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<IdentifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImage = async (f: File, previewUrl: string) => {
    setPreview(previewUrl);
    setResult(null);
    setError(null);
    setLoading(true);

    try {
      const res = await identifyFace(f);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Identification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-4">
        <ImageDropZone
          onImage={handleImage}
          preview={preview}
          label="Drop image to identify"
        />
        {loading && (
          <div className="flex items-center gap-3 text-indigo-400 text-sm">
            <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
            Searching watchlist...
          </div>
        )}
      </div>

      <div className="space-y-4">
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
            {error}
          </div>
        )}

        {result && (
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
            <h3 className="text-sm font-medium text-gray-400">
              {result.matches.length > 0
                ? `${result.matches.length} match${result.matches.length > 1 ? 'es' : ''} found`
                : 'No matches found'}
            </h3>

            {result.matches.length === 0 && (
              <p className="text-gray-500 text-sm">
                This face doesn't match anyone in the watchlist. Try enrolling some faces first.
              </p>
            )}

            {result.matches.map((match, i) => (
              <div
                key={i}
                className="flex items-center justify-between bg-gray-800/50 rounded-lg p-4"
              >
                <div>
                  <div className="font-medium">{match.label}</div>
                  <div className="text-xs text-gray-500">{match.identity_id}</div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold font-mono ${
                    match.similarity > 0.6 ? 'text-green-400' :
                    match.similarity > 0.4 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {(match.similarity * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">similarity</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
