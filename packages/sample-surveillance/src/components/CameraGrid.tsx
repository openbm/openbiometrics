import { useState, useEffect, useCallback } from 'react'
import type { CameraInfo } from '../api'
import { listCameras, addCamera, removeCamera, getCameraSnapshotUrl } from '../api'

function CameraCard({ camera, onRemove }: { camera: CameraInfo; onRemove: (id: string) => void }) {
  const [tick, setTick] = useState(0)
  const [imgError, setImgError] = useState(false)

  useEffect(() => {
    const iv = setInterval(() => setTick((t) => t + 1), 3000)
    return () => clearInterval(iv)
  }, [])

  const snapshotUrl = `${getCameraSnapshotUrl(camera.camera_id)}?t=${tick}`

  const statusColor: Record<string, string> = {
    running: 'bg-emerald-500',
    stopped: 'bg-gray-500',
    error: 'bg-red-500',
    connecting: 'bg-amber-500',
  }

  return (
    <div className="relative group bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-gray-500 transition-colors">
      {/* Snapshot */}
      <div className="aspect-video bg-gray-900 flex items-center justify-center relative">
        {imgError ? (
          <div className="text-gray-600 text-sm flex flex-col items-center gap-2">
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
            </svg>
            <span>No signal</span>
          </div>
        ) : (
          <img
            src={snapshotUrl}
            alt={`Camera ${camera.camera_id}`}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
            onLoad={() => setImgError(false)}
          />
        )}

        {/* Overlay: status + REC indicator */}
        <div className="absolute top-2 left-2 flex items-center gap-2">
          <span className={`inline-block w-2 h-2 rounded-full ${statusColor[camera.status] ?? 'bg-gray-500'}`} />
          <span className="text-[10px] font-mono text-gray-300 uppercase">{camera.status}</span>
        </div>
        {camera.status === 'running' && (
          <div className="absolute top-2 right-2 flex items-center gap-1">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            <span className="text-[10px] font-mono text-red-400 tracking-wider">REC</span>
          </div>
        )}
      </div>

      {/* Info bar */}
      <div className="px-3 py-2 flex items-center justify-between">
        <div className="min-w-0">
          <p className="text-xs font-mono text-gray-200 truncate">{camera.camera_id}</p>
          <p className="text-[10px] text-gray-500 truncate">{camera.source}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0 ml-2">
          <span className="text-[10px] font-mono text-gray-400">{camera.fps.toFixed(1)} fps</span>
          <span className="text-[10px] font-mono text-gray-500">{camera.frame_count} frames</span>
          <button
            onClick={() => onRemove(camera.camera_id)}
            className="text-gray-600 hover:text-red-400 transition-colors p-0.5"
            title="Remove camera"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

function AddCameraCard({ onAdd }: { onAdd: (source: string, id?: string) => Promise<void> }) {
  const [source, setSource] = useState('')
  const [cameraId, setCameraId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (!source.trim()) return
    setLoading(true)
    setError('')
    try {
      await onAdd(source.trim(), cameraId.trim() || undefined)
      setSource('')
      setCameraId('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to add camera')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-800/50 rounded-lg border-2 border-dashed border-gray-700 hover:border-gray-500 transition-colors flex flex-col items-center justify-center p-6 min-h-[200px]">
      <svg className="w-8 h-8 text-gray-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
      </svg>
      <p className="text-sm text-gray-400 mb-4">Add Camera</p>

      <div className="w-full space-y-2">
        <input
          type="text"
          placeholder="rtsp://... or webcam index (0)"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-600 focus:outline-none"
        />
        <input
          type="text"
          placeholder="Camera ID (optional)"
          value={cameraId}
          onChange={(e) => setCameraId(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-cyan-600 focus:outline-none"
        />
        <button
          onClick={handleSubmit}
          disabled={loading || !source.trim()}
          className="w-full bg-cyan-700 hover:bg-cyan-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded px-3 py-1.5 transition-colors"
        >
          {loading ? 'Connecting...' : 'Connect'}
        </button>
        {error && <p className="text-xs text-red-400 text-center">{error}</p>}
      </div>
    </div>
  )
}

export default function CameraGrid() {
  const [cameras, setCameras] = useState<CameraInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const list = await listCameras()
      setCameras(list)
      setError('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load cameras')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const iv = setInterval(refresh, 5000)
    return () => clearInterval(iv)
  }, [refresh])

  const handleAdd = async (source: string, id?: string) => {
    await addCamera(source, id)
    await refresh()
  }

  const handleRemove = async (cameraId: string) => {
    await removeCamera(cameraId)
    setCameras((prev) => prev.filter((c) => c.camera_id !== cameraId))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error && cameras.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500 gap-2">
        <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
        </svg>
        <p className="text-sm">{error}</p>
        <button onClick={refresh} className="text-xs text-cyan-400 hover:underline">Retry</button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Camera Feeds</h2>
        <span className="text-xs text-gray-500">{cameras.length} camera{cameras.length !== 1 ? 's' : ''}</span>
      </div>

      {cameras.length === 0 && !error ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex flex-col items-center justify-center h-48 bg-gray-800/30 rounded-lg border border-gray-800 text-gray-600">
            <svg className="w-12 h-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
            </svg>
            <p className="text-sm">No cameras connected</p>
            <p className="text-xs text-gray-700 mt-1">Add a camera to get started</p>
          </div>
          <AddCameraCard onAdd={handleAdd} />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {cameras.map((cam) => (
            <CameraCard key={cam.camera_id} camera={cam} onRemove={handleRemove} />
          ))}
          <AddCameraCard onAdd={handleAdd} />
        </div>
      )}
    </div>
  )
}
