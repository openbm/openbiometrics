import { useState } from 'react';
import { verifyFaces, type VerifyResponse } from '../api';
import { ImageDropZone } from './ImageDropZone';

export function VerifyPanel() {
  const [file1, setFile1] = useState<File | null>(null);
  const [file2, setFile2] = useState<File | null>(null);
  const [preview1, setPreview1] = useState<string | null>(null);
  const [preview2, setPreview2] = useState<string | null>(null);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [threshold, setThreshold] = useState(0.4);

  const handleVerify = async () => {
    if (!file1 || !file2) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await verifyFaces(file1, file2, threshold);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">1:1 Verification</h2>
        <p className="text-gray-400 text-sm">
          Upload two face images to check if they belong to the same person.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm text-gray-400">Image 1</label>
          <ImageDropZone
            onImage={(f, p) => { setFile1(f); setPreview1(p); setResult(null); }}
            preview={preview1}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm text-gray-400">Image 2</label>
          <ImageDropZone
            onImage={(f, p) => { setFile2(f); setPreview2(p); setResult(null); }}
            preview={preview2}
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-400">Threshold:</label>
          <input
            type="range"
            min="0.1"
            max="0.8"
            step="0.05"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-32 accent-indigo-500"
          />
          <span className="text-sm font-mono text-gray-300 w-10">{threshold.toFixed(2)}</span>
        </div>

        <button
          onClick={handleVerify}
          disabled={!file1 || !file2 || loading}
          className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-medium transition-colors"
        >
          {loading ? 'Verifying...' : 'Verify'}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className={`rounded-xl border p-6 text-center space-y-3 ${
          result.is_match
            ? 'bg-green-500/5 border-green-500/30'
            : 'bg-red-500/5 border-red-500/30'
        }`}>
          <div className={`text-4xl font-bold ${result.is_match ? 'text-green-400' : 'text-red-400'}`}>
            {result.is_match ? 'MATCH' : 'NO MATCH'}
          </div>
          <div className="text-lg">
            Similarity: <span className="font-mono font-bold">{(result.similarity * 100).toFixed(2)}%</span>
          </div>
          <div className="text-sm text-gray-500">
            Threshold: {(threshold * 100).toFixed(0)}% | Score needed: {threshold.toFixed(2)}
          </div>
        </div>
      )}
    </div>
  );
}
