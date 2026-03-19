import { useEffect, useState } from 'react';
import {
  addCamera,
  removeCamera,
  listCameras,
  getCameraSnapshotUrl,
  type CameraInfo,
} from '../api';

export function VideoPanel() {
  const [cameras, setCameras] = useState<CameraInfo[]>([]);
  const [source, setSource] = useState('');
  const [cameraId, setCameraId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCamera, setSelectedCamera] = useState<string | null>(null);
  const [snapshotKey, setSnapshotKey] = useState(0);

  const fetchCameras = async () => {
    try {
      const res = await listCameras();
      setCameras(res.cameras);
    } catch {
      // silently fail on poll
    }
  };

  useEffect(() => {
    fetchCameras();
    const interval = setInterval(fetchCameras, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAdd = async () => {
    if (!source.trim()) return;
    setLoading(true);
    setError(null);

    try {
      await addCamera(source.trim(), cameraId.trim() || undefined);
      setSource('');
      setCameraId('');
      await fetchCameras();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to add camera');
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (id: string) => {
    try {
      await removeCamera(id);
      if (selectedCamera === id) setSelectedCamera(null);
      await fetchCameras();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to remove camera');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold mb-2">Video Surveillance</h2>
        <p className="text-gray-400 text-sm">
          Manage camera feeds for real-time face detection and tracking.
        </p>
      </div>

      {/* Add camera form */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-4">
        <h3 className="text-sm font-medium text-gray-400">Add Camera</h3>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-xs text-gray-500 mb-1">Source URL / Path</label>
            <input
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="rtsp://... or /dev/video0 or http://..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
          <div className="w-40">
            <label className="block text-xs text-gray-500 mb-1">Camera ID (optional)</label>
            <input
              type="text"
              value={cameraId}
              onChange={(e) => setCameraId(e.target.value)}
              placeholder="cam-01"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>
          <button
            onClick={handleAdd}
            disabled={!source.trim() || loading}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
          >
            {loading ? 'Adding...' : 'Add Camera'}
          </button>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Camera grid */}
      {cameras.length === 0 ? (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-12 text-center">
          <div className="text-gray-500 text-sm">No cameras connected. Add one above to get started.</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {cameras.map((cam) => (
            <div
              key={cam.id}
              onClick={() => {
                setSelectedCamera(cam.id);
                setSnapshotKey((k) => k + 1);
              }}
              className={`bg-gray-900 rounded-xl border p-4 cursor-pointer transition-colors space-y-3 ${
                selectedCamera === cam.id
                  ? 'border-indigo-500'
                  : 'border-gray-800 hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    cam.status === 'running' ? 'bg-green-500' :
                    cam.status === 'stopped' ? 'bg-yellow-500' : 'bg-red-500'
                  }`} />
                  <span className="text-sm font-medium">{cam.id}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemove(cam.id);
                  }}
                  className="text-gray-500 hover:text-red-400 transition-colors text-xs"
                >
                  Remove
                </button>
              </div>

              <div className="text-xs text-gray-500 truncate">{cam.source}</div>

              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <div className="text-gray-500">Status</div>
                  <div className={
                    cam.status === 'running' ? 'text-green-400' :
                    cam.status === 'stopped' ? 'text-yellow-400' : 'text-red-400'
                  }>
                    {cam.status}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">FPS</div>
                  <div className="font-mono">{cam.fps.toFixed(1)}</div>
                </div>
                <div>
                  <div className="text-gray-500">Frames</div>
                  <div className="font-mono">{cam.frame_count.toLocaleString()}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Snapshot display */}
      {selectedCamera && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-400">
              Snapshot: {selectedCamera}
            </h3>
            <button
              onClick={() => setSnapshotKey((k) => k + 1)}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Refresh
            </button>
          </div>
          <img
            key={snapshotKey}
            src={`${getCameraSnapshotUrl(selectedCamera)}?t=${snapshotKey}`}
            alt={`Snapshot from ${selectedCamera}`}
            className="w-full rounded-lg object-contain max-h-96 bg-gray-800"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        </div>
      )}
    </div>
  );
}
