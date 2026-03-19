import { useState } from 'react';
import { detectFaces, type DetectResponse, type FaceResponse } from '../api';
import { ImageDropZone } from './ImageDropZone';
import { FaceOverlay } from './FaceOverlay';

export function DetectPanel() {
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<DetectResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImage = async (f: File, previewUrl: string) => {
    setPreview(previewUrl);
    setResult(null);
    setError(null);
    setLoading(true);

    try {
      const res = await detectFaces(f);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Detection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Face Detection</h2>
        <p className="text-gray-400 text-sm">
          Upload an image to detect faces with quality assessment, demographics, and liveness check.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <ImageDropZone onImage={handleImage} preview={!result ? preview : undefined} />

          {loading && (
            <div className="flex items-center gap-3 text-indigo-400 text-sm">
              <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
              Processing...
            </div>
          )}

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
              {error}
            </div>
          )}

          {result && preview && (
            <FaceOverlay imageUrl={preview} faces={result.faces} />
          )}
        </div>

        <div className="space-y-4">
          {result && (
            <>
              <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
                <h3 className="text-sm font-medium text-gray-400 mb-3">
                  {result.count} face{result.count !== 1 ? 's' : ''} detected
                </h3>
                <div className="space-y-4">
                  {result.faces.map((face, i) => (
                    <FaceCard key={i} face={face} index={i} />
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function FaceCard({ face, index }: { face: FaceResponse; index: number }) {
  return (
    <div className="bg-gray-800/50 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Face #{index + 1}</span>
        <span className="text-xs text-gray-500">
          {(face.detection.confidence * 100).toFixed(1)}% confidence
        </span>
      </div>

      {face.demographics && (
        <div className="flex gap-4">
          {face.demographics.age && (
            <Stat label="Age" value={String(face.demographics.age)} />
          )}
          {face.demographics.gender && (
            <Stat label="Gender" value={face.demographics.gender === 'M' ? 'Male' : 'Female'} />
          )}
        </div>
      )}

      {face.liveness && (
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${face.liveness.is_live ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className={`text-sm ${face.liveness.is_live ? 'text-green-400' : 'text-red-400'}`}>
            {face.liveness.is_live ? 'Live' : 'Spoof detected'}
          </span>
          {face.liveness.score != null && (
            <span className="text-xs text-gray-500 ml-auto">
              {(face.liveness.score * 100).toFixed(0)}%
            </span>
          )}
        </div>
      )}

      {face.quality && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Quality</span>
            <span className={face.quality.is_acceptable ? 'text-green-400' : 'text-yellow-400'}>
              {face.quality.overall_score.toFixed(0)}/100
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all ${
                face.quality.overall_score > 70 ? 'bg-green-500' :
                face.quality.overall_score > 40 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${face.quality.overall_score}%` }}
            />
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <Stat label="Sharpness" value={face.quality.sharpness.toFixed(0)} />
            <Stat label="Brightness" value={face.quality.brightness.toFixed(0)} />
            <Stat label="Face size" value={`${face.quality.face_size_px.toFixed(0)}px`} />
            <Stat label="Contrast" value={face.quality.contrast.toFixed(0)} />
          </div>
          {face.quality.reasons.length > 0 && (
            <div className="text-xs text-yellow-400/80">
              Issues: {face.quality.reasons.join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-gray-500 text-xs">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}
