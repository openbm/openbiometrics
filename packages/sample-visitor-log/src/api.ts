const BASE = '/api/v1';

export interface FaceDetection {
  bbox: number[];
  confidence: number;
  face_size: number;
  landmarks: number[][];
}

export interface QualityInfo {
  overall_score: number;
  is_acceptable: boolean;
  reasons: string[];
}

export interface LivenessInfo {
  is_live: boolean | null;
  score: number | null;
}

export interface FaceResponse {
  detection: FaceDetection;
  quality: QualityInfo | null;
  liveness: LivenessInfo | null;
  has_embedding: boolean;
}

export interface DetectResponse {
  faces: FaceResponse[];
  count: number;
}

export interface WatchlistMatch {
  identity_id: string;
  label: string;
  similarity: number;
  metadata: Record<string, unknown>;
}

export interface IdentifyResponse {
  face: FaceResponse;
  matches: WatchlistMatch[];
}

export interface EnrollResponse {
  identity_id: string;
  label: string;
  watchlist_name: string;
}

export interface WatchlistInfo {
  name: string;
  size: number;
}

export interface WatchlistListResponse {
  watchlists: WatchlistInfo[];
}

export interface EventEntry {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  data: Record<string, unknown>;
  camera_id: string | null;
}

export async function detectFaces(image: Blob): Promise<DetectResponse> {
  const form = new FormData();
  form.append('image', image, 'frame.jpg');
  const res = await fetch(`${BASE}/detect`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function enrollFace(image: Blob, label: string, watchlist = 'default'): Promise<EnrollResponse> {
  const form = new FormData();
  form.append('image', image, 'face.jpg');
  form.append('label', label);
  form.append('watchlist_name', watchlist);
  const res = await fetch(`${BASE}/watchlist/enroll`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function identifyFace(image: Blob, watchlist = 'default', topK = 3): Promise<IdentifyResponse> {
  const form = new FormData();
  form.append('image', image, 'frame.jpg');
  form.append('watchlist_name', watchlist);
  form.append('top_k', String(topK));
  const res = await fetch(`${BASE}/identify`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listWatchlist(): Promise<WatchlistListResponse> {
  const res = await fetch(`${BASE}/watchlist`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function removeFace(identityId: string): Promise<void> {
  const res = await fetch(`${BASE}/watchlist/${identityId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
}

export async function getRecentEvents(limit = 50): Promise<EventEntry[]> {
  const res = await fetch(`${BASE}/events/recent?limit=${limit}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
